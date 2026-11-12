import os
import warnings
from pathlib import Path
from typing import Dict

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import (
    auc,
    average_precision_score,
    fbeta_score,
    precision_score,
    recall_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split

from ..core.runner import ExperimentRunner
from .transformer import SBAClusterDistanceTransformer


class SBAModelPipeline:
    def __init__(self, config_path: str):
        self.runner = ExperimentRunner(config_path)
        self.config = self.runner.config
        self.transformer = SBAClusterDistanceTransformer()
        self.models = {}
        self.calibrators = {}
        self.thresholds = {}
        self.active_scores_ = None
        self.active_preds_ = None

    def load_data(self):
        df = self.runner.X.copy()
        df[self.config["project"]["target_variable"]] = self.runner.y
        return df

    def _legacy_split_fallback(self, df):
        """Compatibility-only fallback used when a canonical dataset_partition column is absent."""
        active_mask = df["loan_status_r"] == -1
        active_df = df[active_mask].copy()
        dev_df = df[~active_mask].copy()

        train_df, validation_df = train_test_split(
            dev_df,
            test_size=0.2,
            stratify=dev_df["loan_status_r"],
            random_state=42,
        )

        train_df.sort_index(inplace=True)
        validation_df.sort_index(inplace=True)

        return train_df, validation_df, active_df

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

    def fit_transformer(self, train_df, validation_df, active_df):
        X_train = train_df.drop(columns=[self.config["project"]["target_variable"]])
        y_train = train_df[self.config["project"]["target_variable"]]

        X_train_transformed = self.transformer.fit_transform(X_train, y_train)
        X_validation_transformed = self.transformer.transform(validation_df.drop(columns=[self.config["project"]["target_variable"]]))
        X_active_transformed = self.transformer.transform(active_df.drop(columns=[self.config["project"]["target_variable"]]))

        train_df_transformed = pd.concat([X_train_transformed, y_train], axis=1)
        validation_df_transformed = pd.concat([X_validation_transformed, validation_df[self.config["project"]["target_variable"]].reset_index(drop=True)], axis=1)
        active_df_transformed = pd.concat([X_active_transformed, active_df[[self.config["project"]["target_variable"]]].reset_index(drop=True)], axis=1)

        return train_df_transformed, validation_df_transformed, active_df_transformed

    def _select_threshold(self, y_true, y_prob):
        threshold_policy = self.config.get("experiment_settings", {}).get("threshold_policy", {})
        objective = threshold_policy.get("objective", "f2")
        min_recall = float(threshold_policy.get("min_recall", 0.0))
        min_precision = float(threshold_policy.get("min_precision", 0.0))

        _, _, thresholds = roc_curve(y_true, y_prob)
        candidates = []

        for threshold in thresholds:
            y_pred = (y_prob >= threshold).astype(int)
            precision = precision_score(y_true, y_pred, zero_division=0)
            recall = recall_score(y_true, y_pred, zero_division=0)
            if recall < min_recall or precision < min_precision:
                continue
            f2 = fbeta_score(y_true, y_pred, beta=2, zero_division=0)
            candidates.append({
                "threshold": float(threshold),
                "precision": float(precision),
                "recall": float(recall),
                "f2": float(f2),
                "objective_score": float(
                    recall if objective == "recall"
                    else f2 if objective == "f2"
                    else precision if objective == "precision"
                    else recall
                ),
            })

        if not candidates:
            for threshold in thresholds:
                y_pred = (y_prob >= threshold).astype(int)
                precision = precision_score(y_true, y_pred, zero_division=0)
                recall = recall_score(y_true, y_pred, zero_division=0)
                f2 = fbeta_score(y_true, y_pred, beta=2, zero_division=0)
                candidates.append({
                    "threshold": float(threshold),
                    "precision": float(precision),
                    "recall": float(recall),
                    "f2": float(f2),
                    "objective_score": float(
                        recall if objective == "recall"
                        else f2 if objective == "f2"
                        else precision if objective == "precision"
                        else recall
                    ),
                })

        best = max(candidates, key=lambda item: (item["objective_score"], item["precision"], item["f2"], item["recall"]))
        return best["threshold"], best

    def _fit_model(self, estimator, model_name, train_df, validation_df):
        X_train = train_df[["hdgc", "hdbc"]].copy()
        y_train = train_df[self.config["project"]["target_variable"]]
        X_val = validation_df[["hdgc", "hdbc"]].copy()
        y_val = validation_df[self.config["project"]["target_variable"]]

        estimator.fit(X_train, y_train)
        calibrator = CalibratedClassifierCV(estimator=estimator, method="isotonic", cv="prefit")
        calibrator.fit(X_val, y_val)

        self.models[model_name] = estimator
        self.calibrators[model_name] = calibrator

        y_prob = calibrator.predict_proba(X_val)[:, 1]
        threshold, _ = self._select_threshold(y_val, y_prob)

        self.thresholds[model_name] = float(threshold)
        score = average_precision_score(y_val, y_prob)

        return {
            "model_name": model_name,
            "pr_auc": score,
            "threshold": float(threshold),
        }

    def train(self, train_df, validation_df):
        results = []

        results.append(self._fit_model(
            GradientBoostingClassifier(random_state=42, n_estimators=100, learning_rate=0.1),
            "gradient_boosting",
            train_df,
            validation_df,
        ))

        results.append(self._fit_model(
            RandomForestClassifier(random_state=42, n_estimators=100),
            "random_forest",
            train_df,
            validation_df,
        ))

        return pd.DataFrame(results)

    def score_active_set(self, active_df):
        X_active = active_df[["hdgc", "hdbc"]].copy()
        best_model_name = max(self.thresholds, key=lambda key: self.calibrators[key].score(X_active, active_df[self.config["project"]["target_variable"]])) if self.thresholds else None
        best_model_name = best_model_name or "gradient_boosting"

        calibrated = self.calibrators[best_model_name]
        proba = calibrated.predict_proba(X_active)[:, 1]
        threshold = self.thresholds[best_model_name]

        active_df["probability_bad"] = proba
        active_df["prediction_bad"] = (proba >= threshold).astype(int)
        self.active_scores_ = active_df
        return active_df

    def export_artifacts(self, out_dir: str):
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        joblib.dump(self.transformer, Path(out_dir) / "sba_transformer.pkl")
        joblib.dump(self.models, Path(out_dir) / "sba_models.pkl")
        joblib.dump(self.calibrators, Path(out_dir) / "sba_calibrators.pkl")
        joblib.dump(self.thresholds, Path(out_dir) / "sba_thresholds.pkl")

        metadata = {
            "model_family": list(self.models.keys()),
            "features": ["hdgc", "hdbc"],
            "target": self.config["project"]["target_variable"],
            "thresholds": self.thresholds,
        }
        with open(Path(out_dir) / "metadata.json", "w") as f:
            import json
            json.dump(metadata, f, indent=2)
