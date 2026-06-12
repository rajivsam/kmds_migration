import json
import os
from pathlib import Path

import joblib
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import roc_auc_score, roc_curve
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

    def prepare_datasets(self):
        df = self.load_data()
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

        return train_df, validation_df, active_df

    def transform_datasets(self, train_df, validation_df, active_df):
        X_train = train_df.drop(columns=[self.config["project"]["target_variable"]])
        y_train = train_df[self.config["project"]["target_variable"]]

        X_train_transformed = self.transformer.fit_transform(X_train, y_train)
        X_validation_transformed = self.transformer.transform(validation_df.drop(columns=[self.config["project"]["target_variable"]]))
        X_active_transformed = self.transformer.transform(active_df.drop(columns=[self.config["project"]["target_variable"]]))

        train_df = pd.concat([X_train_transformed, y_train], axis=1)
        validation_df = pd.concat([X_validation_transformed, validation_df[self.config["project"]["target_variable"]]], axis=1)
        active_df = pd.concat([X_active_transformed, active_df[[self.config["project"]["target_variable"]]]], axis=1)

        return train_df, validation_df, active_df

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
            fpr, tpr, thresholds = roc_curve(validation_df[self.config["project"]["target_variable"]], y_prob)
            best_idx = (tpr - fpr).argmax()
            self.thresholds[model_name] = float(thresholds[best_idx])
            results.append({
                "model_name": model_name,
                "roc_auc": float(roc_auc_score(validation_df[self.config["project"]["target_variable"]], y_prob)),
                "threshold": float(thresholds[best_idx]),
            })

        return pd.DataFrame(results)

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
