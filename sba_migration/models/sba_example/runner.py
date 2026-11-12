import json
import os
import warnings
from pathlib import Path

import joblib
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    fbeta_score,
    precision_score,
    recall_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split

from ..core.runner import ExperimentRunner
from .transformer import SBAClusterDistanceTransformer
from .candidates import GradientBoostingCandidate, RandomForestCandidate


class ProbabilityCalibrator:
    def __init__(self):
        self.model = IsotonicRegression(out_of_bounds="clip")

    def fit(self, y_prob, y_true):
        self.model.fit(y_prob, y_true)
        return self

    def predict(self, y_prob):
        return self.model.predict(y_prob)


class SBAExperimentRunner:
    def __init__(self, config_path: str):
        self.runner = ExperimentRunner(config_path)
        self.config = self.runner.config
        self.transformer = SBAClusterDistanceTransformer()
        self.models = {}
        self.calibrators = {}
        self.thresholds = {}

    def _get_candidate_class(self, class_path: str):
        module_name, class_name = class_path.rsplit(".", 1)
        module = __import__(module_name, fromlist=[class_name])
        return getattr(module, class_name)

    def load_data(self):
        df = self.runner.X.copy()
        df[self.config["project"]["target_variable"]] = self.runner.y
        return df

    def _legacy_split_fallback(self, df):
        """Compatibility-only fallback for data files without a canonical partition column."""
        active_mask = df["loan_status_r"] == -1
        active_df = df[active_mask].copy()
        dev_df = df[~active_mask].copy()

        validation_fraction = self.config.get("experiment_settings", {}).get("validation_fraction", 0.2)
        train_df, validation_df = train_test_split(
            dev_df,
            test_size=validation_fraction,
            stratify=dev_df["loan_status_r"],
            random_state=self.config.get("experiment_settings", {}).get("random_state", 42),
        )
        return train_df, validation_df, pd.DataFrame(), active_df

    def prepare_datasets(self):
        df = self.load_data()
        target_col = self.config["project"]["target_variable"]

        if "dataset_partition" in df.columns:
            allowed_partitions = {"train", "validation", "test", "active"}
            observed = set(df["dataset_partition"].dropna().astype(str).unique())
            unexpected = sorted(observed - allowed_partitions)
            if unexpected:
                raise ValueError(
                    "Unexpected dataset_partition values found in model-ready data: "
                    f"{unexpected}. Allowed values: {sorted(allowed_partitions)}"
                )

            train_df = df[df["dataset_partition"] == "train"].copy()
            validation_df = df[df["dataset_partition"] == "validation"].copy()
            test_df = df[df["dataset_partition"] == "test"].copy()
            active_df = df[df["dataset_partition"] == "active"].copy()

            train_df = train_df[train_df[target_col].isin([0, 1])].copy()
            validation_df = validation_df[validation_df[target_col].isin([0, 1])].copy()
            test_df = test_df[test_df[target_col].isin([0, 1])].copy()
            active_df = active_df[active_df[target_col] == -1].copy()

            if train_df.empty:
                raise ValueError("The canonical train partition is empty. Check the featurization output.")
            if validation_df.empty:
                warnings.warn(
                    "No validation rows are present in the canonical dataset_partition; "
                    "continuing with an empty validation set.",
                    RuntimeWarning,
                )
            if test_df.empty:
                warnings.warn(
                    "No test rows are present in the canonical dataset_partition; "
                    "final test evaluation will be skipped.",
                    RuntimeWarning,
                )
            return train_df, validation_df, test_df, active_df

        warnings.warn(
            "dataset_partition is missing; using the legacy train/validation split fallback.",
            RuntimeWarning,
        )
        return self._legacy_split_fallback(df)

    def transform_datasets(self, train_df, validation_df, *rest):
        if len(rest) == 1:
            test_df = pd.DataFrame()
            active_df = rest[0]
        elif len(rest) == 2:
            test_df, active_df = rest
        else:
            raise TypeError("transform_datasets expects train_df, validation_df, [test_df,] active_df")

        target_col = self.config["project"]["target_variable"]

        X_train = train_df.drop(columns=[target_col])
        y_train = train_df[target_col]

        X_train_transformed = self.transformer.fit_transform(X_train, y_train)
        X_validation_transformed = self.transformer.transform(validation_df.drop(columns=[target_col]))

        train_df = pd.concat([X_train_transformed, y_train], axis=1)
        validation_df = pd.concat([X_validation_transformed, validation_df[[target_col]]], axis=1)

        if not test_df.empty:
            X_test_transformed = self.transformer.transform(test_df.drop(columns=[target_col]))
            test_df = pd.concat([X_test_transformed, test_df[[target_col]]], axis=1)
        else:
            test_df = pd.DataFrame()

        if not active_df.empty:
            X_active_transformed = self.transformer.transform(active_df.drop(columns=[target_col]))
            active_df = pd.concat([X_active_transformed, active_df[[target_col]]], axis=1)

        return train_df, validation_df, test_df, active_df

    def _select_threshold(self, y_true, y_prob):
        threshold_policy = self.config.get("experiment_settings", {}).get("threshold_policy", {})
        objective = threshold_policy.get("objective", "f2")
        min_recall = float(threshold_policy.get("min_recall", 0.0))
        min_precision = float(threshold_policy.get("min_precision", 0.0))

        fpr, tpr, thresholds = roc_curve(y_true, y_prob)
        candidates = []

        for threshold, recall, fpr_value in zip(thresholds, tpr, fpr):
            y_pred = (y_prob >= threshold).astype(int)
            precision = precision_score(y_true, y_pred, zero_division=0)
            recall_score_value = recall_score(y_true, y_pred, zero_division=0)
            if recall_score_value < min_recall or precision < min_precision:
                continue
            f2 = fbeta_score(y_true, y_pred, beta=2, zero_division=0)
            candidates.append({
                "threshold": float(threshold),
                "precision": float(precision),
                "recall": float(recall_score_value),
                "f2": float(f2),
                "objective_score": float(
                    recall_score_value if objective == "recall"
                    else f2 if objective == "f2"
                    else precision if objective == "precision"
                    else recall_score_value
                ),
            })

        if not candidates:
            for threshold in thresholds:
                y_pred = (y_prob >= threshold).astype(int)
                precision = precision_score(y_true, y_pred, zero_division=0)
                recall_score_value = recall_score(y_true, y_pred, zero_division=0)
                f2 = fbeta_score(y_true, y_pred, beta=2, zero_division=0)
                candidates.append({
                    "threshold": float(threshold),
                    "precision": float(precision),
                    "recall": float(recall_score_value),
                    "f2": float(f2),
                    "objective_score": float(
                        recall_score_value if objective == "recall"
                        else f2 if objective == "f2"
                        else precision if objective == "precision"
                        else recall_score_value
                    ),
                })

        best = max(candidates, key=lambda item: (item["objective_score"], item["precision"], item["f2"], item["recall"]))
        return best["threshold"], best

    def fit_and_calibrate(self, train_df, validation_df):
        results = []

        for candidate_cfg in self.config.get("candidates", []):
            model_name = candidate_cfg["name"]
            candidate_class = self._get_candidate_class(candidate_cfg["class_path"])
            params = candidate_cfg.get("hyperparameters", {})

            estimator = candidate_class(params)
            estimator.fit(train_df[["hdgc", "hdbc"]], train_df[self.config["project"]["target_variable"]])

            raw_prob = estimator.predict_proba(validation_df[["hdgc", "hdbc"]])[:, 1]
            calibrator = ProbabilityCalibrator().fit(raw_prob, validation_df[self.config["project"]["target_variable"]])
            self.models[model_name] = estimator
            self.calibrators[model_name] = calibrator

            y_prob = calibrator.predict(raw_prob)
            y_true = validation_df[self.config["project"]["target_variable"]]
            threshold, _ = self._select_threshold(y_true, y_prob)
            self.thresholds[model_name] = float(threshold)
            results.append({
                "model_name": model_name,
                "pr_auc": float(average_precision_score(y_true, y_prob)),
                "threshold": float(threshold),
            })

        return pd.DataFrame(results)

    def evaluate_test_set(self, test_df, model_name="gradient_boosting"):
        if test_df.empty:
            warnings.warn(
                "No test rows are present in the canonical dataset_partition; skipping final test evaluation.",
                RuntimeWarning,
            )
            return None
        if model_name not in self.calibrators:
            raise ValueError(f"Calibrator for {model_name} not found")

        estimator = self.models[model_name]
        raw_prob = estimator.predict_proba(test_df[["hdgc", "hdbc"]])[:, 1]
        calibrator = self.calibrators[model_name]
        y_prob = calibrator.predict(raw_prob)
        y_true = test_df[self.config["project"]["target_variable"]]
        threshold = self.thresholds[model_name]
        y_pred = (y_prob >= threshold).astype(int)

        metrics = {
            "model_name": model_name,
            "pr_auc": float(average_precision_score(y_true, y_prob)),
            "threshold": float(threshold),
            "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
            "precision": float(precision_score(y_true, y_pred, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, zero_division=0)),
            "f2": float(fbeta_score(y_true, y_pred, beta=2, zero_division=0)),
            "brier_score": float(brier_score_loss(y_true, y_prob)),
        }
        return metrics

    def score_active_set(self, active_df, model_name="gradient_boosting"):
        if model_name not in self.calibrators:
            raise ValueError(f"Calibrator for {model_name} not found")

        estimator = self.models[model_name]
        raw_prob = estimator.predict_proba(active_df[["hdgc", "hdbc"]])[:, 1]
        calibrator = self.calibrators[model_name]
        proba = calibrator.predict(raw_prob)

        active_df["probability_bad"] = proba
        active_df["prediction_bad"] = (proba >= self.thresholds[model_name]).astype(int)
        return active_df

    def export_artifacts(self, out_dir: str = None):
        export_path = out_dir or self.runner.path_coordinator.modeling_output_path
        Path(export_path).mkdir(parents=True, exist_ok=True)
        joblib.dump(self.transformer, Path(export_path) / "sba_transformer.pkl")
        joblib.dump(self.models, Path(export_path) / "sba_models.pkl")
        joblib.dump(self.calibrators, Path(export_path) / "sba_calibrators.pkl")
        joblib.dump(self.thresholds, Path(export_path) / "sba_thresholds.pkl")
        joblib.dump(self.runner.config, Path(export_path) / "config.pkl")

        metadata = {
            "model_names": list(self.models.keys()),
            "features": ["hdgc", "hdbc"],
            "target": self.config["project"]["target_variable"],
            "thresholds": self.thresholds,
        }
        with open(Path(export_path) / "metadata.json", "w") as f:
            import json
            json.dump(metadata, f, indent=2)

    def evaluate_threshold_metrics(self, y_true, y_prob, threshold):
        y_pred = (y_prob >= threshold).astype(int)
        return {
            "threshold": float(threshold),
            "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
            "precision": float(precision_score(y_true, y_pred, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, zero_division=0)),
            "f2": float(fbeta_score(y_true, y_pred, beta=2, zero_division=0)),
            "brier_score": float(brier_score_loss(y_true, y_prob)),
        }
