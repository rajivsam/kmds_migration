import json
import os
import warnings
from pathlib import Path

import joblib
import numpy as np
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
from sklearn.model_selection import StratifiedKFold, train_test_split

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
        self.stage_1_model_name = None
        self.stage_1_model = None
        self.stage_1_calibrator = None
        self.stage_1_threshold = None
        self.stage_1_results_ = []

    def _get_candidate_class(self, class_path: str):
        module_name, class_name = class_path.rsplit(".", 1)
        module = __import__(module_name, fromlist=[class_name])
        return getattr(module, class_name)

    def _utility_defaults(self):
        settings = self.config.get("experiment_settings", {})
        return {
            "default_loan_age_months": float(settings.get("default_loan_age_months", 24.0)),
            "default_loss_rate": float(settings.get("default_loss_rate", 0.35)),
            "manual_review_cost": float(settings.get("manual_review_cost", 2000.0)),
        }

    def _compute_loan_age_months(self, df):
        defaults = self._utility_defaults()
        default_months = defaults["default_loan_age_months"]

        if "loan_age_months" in df.columns:
            return pd.to_numeric(df["loan_age_months"], errors="coerce").fillna(default_months).clip(lower=0)

        if len(df) == 0:
            return pd.Series(dtype=float, index=df.index)

        age_series = pd.Series(default_months, index=df.index, dtype=float)
        date_candidates = []
        for col in ("firstdisbursementdate", "approvaldate"):
            if col in df.columns:
                date_candidates.append(pd.to_datetime(df[col], errors="coerce"))

        if date_candidates:
            reference_dates = pd.to_datetime(df["AsOfDate"], errors="coerce") if "AsOfDate" in df.columns else pd.Timestamp.utcnow()
            reference_dates = pd.Series(reference_dates, index=df.index)
            if isinstance(reference_dates.iloc[0], pd.Timestamp):
                reference_dates = pd.to_datetime(reference_dates, errors="coerce")
            merged = date_candidates[0].copy()
            for ts in date_candidates[1:]:
                merged = merged.fillna(ts)
            age_series = (reference_dates - merged).dt.total_seconds() / (30.4375 * 24 * 60 * 60)
            age_series = age_series.fillna(default_months)

        return age_series.clip(lower=0).astype(float)

    def _ensure_utility_features(self, df):
        df = df.copy()
        defaults = self._utility_defaults()
        default_months = defaults["default_loan_age_months"]
        loss_rate = defaults["default_loss_rate"]

        if "loan_age_months" not in df.columns:
            df["loan_age_months"] = self._compute_loan_age_months(df)
        else:
            df["loan_age_months"] = pd.to_numeric(df["loan_age_months"], errors="coerce").fillna(default_months)

        if "grossapproval" in df.columns:
            grossapproval = pd.to_numeric(df["grossapproval"], errors="coerce").fillna(0.0)
            seasoning_factor = np.maximum(0.25, 1.0 - df["loan_age_months"] / 60.0)
            df["default_utility_score"] = grossapproval * loss_rate * seasoning_factor
        else:
            df["default_utility_score"] = 0.0

        df["loan_age_months"] = pd.to_numeric(df["loan_age_months"], errors="coerce").fillna(default_months).clip(lower=0)
        df["default_utility_score"] = pd.to_numeric(df["default_utility_score"], errors="coerce").fillna(0.0)
        return df

    def load_data(self):
        df = self.runner.X.copy()
        df[self.config["project"]["target_variable"]] = self.runner.y
        return self._ensure_utility_features(df)

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

    def _threshold_policy(self, stage_name: str):
        threshold_policy = self.config.get("experiment_settings", {}).get("threshold_policy", {})
        if isinstance(threshold_policy, dict) and "stage_1" in threshold_policy:
            threshold_policy = threshold_policy["stage_1"]
        return {
            "objective": threshold_policy.get("objective", "recall"),
            "min_recall": float(threshold_policy.get("min_recall", 0.90)),
            "min_precision": float(threshold_policy.get("min_precision", 0.01)),
        }

    def _utility_value(self, y_true, y_prob, threshold, grossapproval, loan_age_months):
        y_pred = (y_prob >= threshold).astype(int)
        loss_rate = self._utility_defaults()["default_loss_rate"]
        review_cost = self._utility_defaults()["manual_review_cost"]
        seasoning_factor = np.maximum(0.25, 1.0 - np.asarray(loan_age_months, dtype=float) / 60.0)
        expected_loss = np.asarray(grossapproval, dtype=float) * loss_rate * seasoning_factor
        value = np.where(
            (y_true == 1) & (y_pred == 1),
            expected_loss,
            np.where((y_true == 0) & (y_pred == 1), -review_cost, np.where((y_true == 1) & (y_pred == 0), -expected_loss, 0.0))
        )
        return float(np.sum(value))

    def _select_threshold(self, y_true, y_prob, objective=None, min_recall=None, min_precision=None, grossapproval=None, loan_age_months=None):
        if objective is None:
            objective = self._threshold_policy("stage_1")["objective"]
        if min_recall is None:
            min_recall = self._threshold_policy("stage_1")["min_recall"]
        if min_precision is None:
            min_precision = self._threshold_policy("stage_1")["min_precision"]

        _, _, thresholds = roc_curve(y_true, y_prob)
        candidates = []

        for threshold in thresholds:
            y_pred = (y_prob >= threshold).astype(int)
            precision = precision_score(y_true, y_pred, zero_division=0)
            recall_score_value = recall_score(y_true, y_pred, zero_division=0)
            if recall_score_value < min_recall or precision < min_precision:
                continue
            f2 = fbeta_score(y_true, y_pred, beta=2, zero_division=0)
            utility_score = 0.0
            if grossapproval is not None and loan_age_months is not None:
                utility_score = self._utility_value(y_true, y_prob, threshold, grossapproval, loan_age_months)
            candidates.append({
                "threshold": float(threshold),
                "precision": float(precision),
                "recall": float(recall_score_value),
                "f2": float(f2),
                "utility": float(utility_score),
                "objective_score": float(
                    utility_score if objective == "utility"
                    else recall_score_value if objective == "recall"
                    else f2 if objective == "f2"
                    else precision if objective == "precision"
                    else utility_score
                ),
            })

        if not candidates:
            for threshold in thresholds:
                y_pred = (y_prob >= threshold).astype(int)
                precision = precision_score(y_true, y_pred, zero_division=0)
                recall_score_value = recall_score(y_true, y_pred, zero_division=0)
                f2 = fbeta_score(y_true, y_pred, beta=2, zero_division=0)
                utility_score = 0.0
                if grossapproval is not None and loan_age_months is not None:
                    utility_score = self._utility_value(y_true, y_prob, threshold, grossapproval, loan_age_months)
                candidates.append({
                    "threshold": float(threshold),
                    "precision": float(precision),
                    "recall": float(recall_score_value),
                    "f2": float(f2),
                    "utility": float(utility_score),
                    "objective_score": float(
                        utility_score if objective == "utility"
                        else recall_score_value if objective == "recall"
                        else f2 if objective == "f2"
                        else precision if objective == "precision"
                        else utility_score
                    ),
                })

        best = max(candidates, key=lambda item: (item["objective_score"], item["utility"], item["precision"], item["recall"]))
        return best["threshold"], best

    def _fit_candidate(self, candidate_cfg, train_df, eval_df, stage_name: str):
        target_col = self.config["project"]["target_variable"]
        model_name = candidate_cfg["name"]
        candidate_class = self._get_candidate_class(candidate_cfg["class_path"])
        params = candidate_cfg.get("hyperparameters", {})

        estimator = candidate_class(params)
        feature_cols = [c for c in ["hdgc", "hdbc", "loan_age_months", "default_utility_score"] if c in train_df.columns]
        estimator.fit(train_df[feature_cols], train_df[target_col])

        raw_prob = estimator.predict_proba(eval_df[feature_cols])[:, 1]
        calibrator = ProbabilityCalibrator().fit(raw_prob, eval_df[target_col])
        y_prob = calibrator.predict(raw_prob)
        y_true = eval_df[target_col]
        policy = self._threshold_policy(stage_name)
        threshold, metrics = self._select_threshold(
            y_true,
            y_prob,
            objective=policy["objective"],
            min_recall=policy["min_recall"],
            min_precision=policy["min_precision"],
            grossapproval=eval_df["grossapproval"].to_numpy() if "grossapproval" in eval_df.columns else None,
            loan_age_months=eval_df["loan_age_months"].to_numpy() if "loan_age_months" in eval_df.columns else None,
        )

        metrics = {
            "stage": stage_name,
            "model_name": model_name,
            "threshold": float(threshold),
            "pr_auc": float(average_precision_score(y_true, y_prob)),
            "precision": float(metrics["precision"]),
            "recall": float(metrics["recall"]),
            "f2": float(metrics["f2"]),
            "utility": float(metrics["utility"]),
            "balanced_accuracy": float(balanced_accuracy_score(y_true, (y_prob >= threshold).astype(int))),
        }

        self.models[model_name] = estimator
        self.calibrators[model_name] = calibrator
        self.thresholds[model_name] = float(threshold)
        return model_name, estimator, calibrator, threshold, metrics

    def fit_stage_1(self, train_df, validation_df):
        results = []
        for candidate_cfg in self.config.get("candidates", []):
            model_name, estimator, calibrator, threshold, metrics = self._fit_candidate(
                candidate_cfg,
                train_df,
                validation_df,
                "stage_1",
            )
            self.models[model_name] = estimator
            self.calibrators[model_name] = calibrator
            self.thresholds[model_name] = float(threshold)
            results.append(metrics)

        best = max(results, key=lambda item: (item["pr_auc"], item["recall"], item["precision"], item["f2"]))
        self.stage_1_model_name = best["model_name"]
        self.stage_1_model = self.models[self.stage_1_model_name]
        self.stage_1_calibrator = self.calibrators[self.stage_1_model_name]
        self.stage_1_threshold = float(best["threshold"])
        self.stage_1_results_ = results
        return pd.DataFrame(results)

    def _stage_positive_mask(self, df, model, calibrator, threshold):
        feature_cols = [c for c in ["hdgc", "hdbc", "loan_age_months", "default_utility_score"] if c in df.columns]
        raw_prob = model.predict_proba(df[feature_cols])[:, 1]
        prob = calibrator.predict(raw_prob)
        return (prob >= threshold).astype(bool), prob

    def fit_and_calibrate(self, train_df, validation_df):
        return self.fit_stage_1(train_df, validation_df)

    def _cascade_predict(self, df):
        if self.stage_1_model is None:
            raise ValueError("Stage 1 model must be fit before prediction.")

        stage_1_mask, stage_1_prob = self._stage_positive_mask(df, self.stage_1_model, self.stage_1_calibrator, self.stage_1_threshold)
        final_pred = stage_1_mask.astype(int)
        final_prob = stage_1_prob
        return final_pred.astype(int), stage_1_mask.astype(int), stage_1_prob, final_prob

    def evaluate_test_set(self, test_df):
        if test_df.empty:
            warnings.warn(
                "No test rows are present in the canonical dataset_partition; skipping final test evaluation.",
                RuntimeWarning,
            )
            return None

        if self.stage_1_model is None:
            raise ValueError("Stage 1 model must be fit before evaluation.")

        target_col = self.config["project"]["target_variable"]
        y_true = test_df[target_col].astype(int)
        feature_cols = [c for c in ["hdgc", "hdbc", "loan_age_months", "default_utility_score"] if c in test_df.columns]
        stage_1_prob = np.asarray(
            self.stage_1_calibrator.predict(self.stage_1_model.predict_proba(test_df[feature_cols])[:, 1]),
            dtype=float,
        )
        stage_1_pred = (stage_1_prob >= self.stage_1_threshold).astype(int)
        stage_1_precision = precision_score(y_true, stage_1_pred, zero_division=0)
        stage_1_recall = recall_score(y_true, stage_1_pred, zero_division=0)

        report = {
            "test_rows": int(len(test_df)),
            "actual_positive_rows": int(y_true.sum()),
            "stage_1_threshold": float(self.stage_1_threshold),
            "stage_1_precision": float(stage_1_precision),
            "stage_1_recall": float(stage_1_recall),
            "stage_1_predicted_positive": int(stage_1_pred.sum()),
            "final_threshold": float(self.stage_1_threshold),
            "final_precision": float(stage_1_precision),
            "final_recall": float(stage_1_recall),
            "final_predicted_positive": int(stage_1_pred.sum()),
            "pr_auc": float(average_precision_score(y_true, stage_1_prob)),
            "threshold": float(self.stage_1_threshold),
            "balanced_accuracy": float(balanced_accuracy_score(y_true, stage_1_pred)),
            "precision": float(stage_1_precision),
            "recall": float(stage_1_recall),
            "f2": float(fbeta_score(y_true, stage_1_pred, beta=2, zero_division=0)),
            "brier_score": float(brier_score_loss(y_true, stage_1_prob)),
        }
        return report

    def score_active_set(self, active_df):
        if self.stage_1_model is None:
            raise ValueError("Stage 1 model must be fit before active scoring.")

        stage_1_mask, stage_1_prob = self._stage_positive_mask(active_df, self.stage_1_model, self.stage_1_calibrator, self.stage_1_threshold)
        active_df["stage_1_probability"] = stage_1_prob
        active_df["stage_1_prediction"] = stage_1_mask.astype(int)
        active_df["final_prediction"] = stage_1_mask.astype(int)
        return active_df

    def export_artifacts(self, out_dir: str = None):
        export_path = out_dir or self.runner.path_coordinator.modeling_output_path
        Path(export_path).mkdir(parents=True, exist_ok=True)
        joblib.dump(self.transformer, Path(export_path) / "sba_transformer.pkl")
        joblib.dump({
            "stage_1": self.stage_1_model,
        }, Path(export_path) / "sba_models.pkl")
        joblib.dump({
            "stage_1": self.stage_1_calibrator,
        }, Path(export_path) / "sba_calibrators.pkl")
        joblib.dump({
            "stage_1": self.stage_1_threshold,
        }, Path(export_path) / "sba_thresholds.pkl")
        joblib.dump(self.runner.config, Path(export_path) / "config.pkl")

        metadata = {
            "model_names": {
                "stage_1": self.stage_1_model_name,
            },
            "features": [c for c in ["hdgc", "hdbc", "loan_age_months", "default_utility_score"] if c in self.runner.X.columns],
            "target": self.config["project"]["target_variable"],
            "thresholds": {
                "stage_1": self.stage_1_threshold,
            },
            "stages": ["stage_1"],
        }
        with open(Path(export_path) / "metadata.json", "w") as f:
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
