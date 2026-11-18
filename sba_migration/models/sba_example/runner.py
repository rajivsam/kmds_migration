import json
import warnings
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    fbeta_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

from ..core.runner import ExperimentRunner
from .transformer import SBAScreenedFeatureTransformer


class SBAExperimentRunner:
    def __init__(self, config_path: str):
        self.runner = ExperimentRunner(config_path)
        self.config = self.runner.config
        self.transformer = SBAScreenedFeatureTransformer()
        self.models = {}
        self.calibrators = {}
        self.model_results_ = []
        self.model_name = None
        self.model = None
        self.calibrator = None
        self.cutoff_percent = None
        self.threshold = None
        self.validation_gains_ = pd.DataFrame()
        self.cutoff_metadata_ = {}
        self.test_results_ = None
        self.active_scores_ = None

        # Compatibility attributes retained for existing callers and artifact readers.
        self.stage_1_model_name = None
        self.stage_1_model = None
        self.stage_1_calibrator = None
        self.stage_1_threshold = None
        self.stage_1_results_ = []

    def _get_candidate_class(self, class_path: str):
        module_name, class_name = class_path.rsplit(".", 1)
        module = __import__(module_name, fromlist=[class_name])
        return getattr(module, class_name)

    def load_data(self):
        df = self.runner.X.copy()
        df[self.config["project"]["target_variable"]] = self.runner.y
        return df

    def _legacy_split_fallback(self, df):
        target_col = self.config["project"]["target_variable"]
        active_df = df[df[target_col] == -1].copy()
        development_df = df[df[target_col].isin([0, 1])].copy()
        train_df, validation_df = train_test_split(
            development_df,
            test_size=float(
                self.config.get("experiment_settings", {}).get("validation_fraction", 0.2)
            ),
            stratify=development_df[target_col],
            random_state=42,
        )
        warnings.warn(
            "dataset_partition is missing; using a legacy train/validation split. "
            "No unbiased test split is available.",
            RuntimeWarning,
        )
        return train_df, validation_df, pd.DataFrame(), active_df

    def prepare_datasets(self):
        df = self.load_data()
        target_col = self.config["project"]["target_variable"]
        if "dataset_partition" not in df.columns:
            return self._legacy_split_fallback(df)

        allowed = {"train", "validation", "test", "active"}
        observed = set(df["dataset_partition"].dropna().astype(str).unique())
        unexpected = sorted(observed - allowed)
        if unexpected:
            raise ValueError(
                "Unexpected dataset_partition values found in model-ready data: "
                f"{unexpected}. Allowed values: {sorted(allowed)}"
            )

        train_df = df[
            (df["dataset_partition"] == "train") & df[target_col].isin([0, 1])
        ].copy()
        validation_df = df[
            (df["dataset_partition"] == "validation") & df[target_col].isin([0, 1])
        ].copy()
        test_df = df[
            (df["dataset_partition"] == "test") & df[target_col].isin([0, 1])
        ].copy()
        active_df = df[
            (df["dataset_partition"] == "active") & (df[target_col] == -1)
        ].copy()

        if train_df.empty:
            raise ValueError("The canonical train partition is empty.")
        if validation_df.empty:
            raise ValueError(
                "The canonical validation partition is empty; Stage-2 cutoff tuning "
                "requires validation data."
            )
        if test_df.empty:
            warnings.warn(
                "The canonical test partition is empty; final evaluation will be skipped.",
                RuntimeWarning,
            )
        return train_df, validation_df, test_df, active_df

    def transform_datasets(self, train_df, validation_df, test_df, active_df):
        target_col = self.config["project"]["target_variable"]
        train_X = self.transformer.fit_transform(
            train_df[self.transformer.raw_feature_names_],
            train_df[target_col],
        )
        transformed = [
            pd.concat([train_X, train_df[[target_col, "dataset_partition"]]], axis=1)
        ]

        for frame in (validation_df, test_df, active_df):
            if frame.empty:
                transformed.append(pd.DataFrame())
                continue
            X = self.transformer.transform(frame[self.transformer.raw_feature_names_])
            transformed.append(
                pd.concat([X, frame[[target_col, "dataset_partition"]]], axis=1)
            )
        return tuple(transformed)

    def _probabilities(self, dataframe, calibrator=None):
        selected = self.calibrator if calibrator is None else calibrator
        if selected is None:
            raise ValueError("A calibrated model must be fitted before prediction.")
        return selected.predict_proba(
            dataframe[self.transformer.feature_names_]
        )[:, 1]

    def fit_stage_1(self, train_df, validation_df):
        target_col = self.config["project"]["target_variable"]
        X_train = train_df[self.transformer.feature_names_]
        y_train = train_df[target_col].astype(int)
        X_validation = validation_df[self.transformer.feature_names_]
        y_validation = validation_df[target_col].astype(int)
        results = []

        for candidate_cfg in self.config.get("candidates", []):
            candidate_class = self._get_candidate_class(candidate_cfg["class_path"])
            candidate = candidate_class(candidate_cfg.get("hyperparameters", {}))
            candidate.fit(X_train, y_train)
            calibrated = CalibratedClassifierCV(
                estimator=candidate.model,
                method="isotonic",
                cv=int(
                    self.config.get("experiment_settings", {})
                    .get("cross_validation", {})
                    .get("splits", 5)
                ),
            )
            calibrated.fit(X_train, y_train)
            validation_probability = calibrated.predict_proba(X_validation)[:, 1]
            result = {
                "stage": "stage_1",
                "model_name": candidate_cfg["name"],
                "pr_auc": float(
                    average_precision_score(y_validation, validation_probability)
                ),
            }
            results.append(result)
            self.models[candidate_cfg["name"]] = candidate
            self.calibrators[candidate_cfg["name"]] = calibrated

        if not results:
            raise ValueError("No candidate models are configured.")

        champion = max(results, key=lambda item: item["pr_auc"])
        self.model_name = champion["model_name"]
        self.model = self.models[self.model_name]
        self.calibrator = self.calibrators[self.model_name]
        self.model_results_ = results
        self.stage_1_model_name = self.model_name
        self.stage_1_model = self.model
        self.stage_1_calibrator = self.calibrator
        self.stage_1_results_ = results
        return pd.DataFrame(results)

    def _stage_2_settings(self):
        settings = self.config.get("experiment_settings", {}).get("stage_2", {})
        return {
            "method": str(settings.get("method", "max_distance_to_diagonal")),
            "cutoff_step": float(settings.get("cutoff_step", 1.0)),
            "capacity_percent": settings.get("capacity_percent"),
            "tie_policy": str(settings.get("tie_policy", "inclusive_score_threshold")),
        }

    def build_validation_gains(self, validation_df):
        if self.calibrator is None:
            raise ValueError("Stage 1 must be fitted before building gains.")

        target_col = self.config["project"]["target_variable"]
        probabilities = self._probabilities(validation_df)
        ranked = pd.DataFrame(
            {
                "row_id": validation_df.index.astype(str),
                "p_default": probabilities,
                "actual_default": validation_df[target_col].astype(int).to_numpy(),
            }
        ).sort_values(
            ["p_default", "row_id"], ascending=[False, True], kind="mergesort"
        )
        total_defaults = int(ranked["actual_default"].sum())
        if total_defaults == 0:
            raise ValueError("Validation data contains no true defaults; gains is undefined.")

        settings = self._stage_2_settings()
        step = settings["cutoff_step"]
        if step <= 0 or step > 100:
            raise ValueError("stage_2.cutoff_step must be greater than 0 and at most 100.")

        cutoffs = list(np.arange(step, 100.0, step))
        if not cutoffs or not np.isclose(cutoffs[-1], 100.0):
            cutoffs.append(100.0)

        rows = []
        for requested_percent in sorted(set(float(round(k, 10)) for k in cutoffs)):
            selected_count = min(
                len(ranked),
                max(1, int(np.ceil(len(ranked) * requested_percent / 100.0))),
            )
            prefix = ranked.iloc[:selected_count]
            population_percent = selected_count / len(ranked) * 100.0
            captured = int(prefix["actual_default"].sum())
            gains_percent = captured / total_defaults * 100.0
            rows.append(
                {
                    "requested_population_percent": requested_percent,
                    "population_percent": population_percent,
                    "reviewed_loans": selected_count,
                    "defaults_captured": captured,
                    "total_validation_defaults": total_defaults,
                    "precision": captured / selected_count,
                    "cumulative_gains_percent": gains_percent,
                    "lift": gains_percent / population_percent,
                    "marginal_gains_percent": (
                        gains_percent
                        if not rows
                        else gains_percent - rows[-1]["cumulative_gains_percent"]
                    ),
                    "threshold_probability": float(prefix["p_default"].iloc[-1]),
                }
            )
        return pd.DataFrame(rows)

    def tune_stage_2_cutoff(self, validation_df):
        gains = self.build_validation_gains(validation_df)
        settings = self._stage_2_settings()
        if settings["method"] != "max_distance_to_diagonal":
            raise ValueError(
                f"Unsupported Stage-2 elbow method: {settings['method']}"
            )
        gains = gains.copy()
        gains["elbow_distance"] = (
            gains["cumulative_gains_percent"] - gains["population_percent"]
        )

        capacity = settings["capacity_percent"]
        if capacity is not None:
            capacity = float(capacity)
            selected = gains.iloc[
                (gains["population_percent"] - capacity).abs().argmin()
            ]
            selection_reason = "capacity_override"
        else:
            selected = gains.iloc[gains["elbow_distance"].argmax()]
            selection_reason = "elbow_max_distance_to_diagonal"

        self.cutoff_percent = float(selected["requested_population_percent"])
        self.threshold = float(selected["threshold_probability"])
        self.validation_gains_ = gains
        self.cutoff_metadata_ = {
            "method": settings["method"],
            "selection_reason": selection_reason,
            "cutoff_percent": self.cutoff_percent,
            "reviewed_loans": int(selected["reviewed_loans"]),
            "population_percent": float(selected["population_percent"]),
            "precision": float(selected["precision"]),
            "cumulative_gains_percent": float(
                selected["cumulative_gains_percent"]
            ),
            "lift": float(selected["lift"]),
            "marginal_gains_percent": float(selected["marginal_gains_percent"]),
            "threshold_probability": self.threshold,
            "cutoff_step": settings["cutoff_step"],
            "capacity_percent": capacity,
            "tie_policy": settings["tie_policy"],
        }
        self.stage_1_threshold = self.threshold
        return self.cutoff_metadata_

    def fit_and_calibrate(self, train_df, validation_df):
        results = self.fit_stage_1(train_df, validation_df)
        self.tune_stage_2_cutoff(validation_df)
        return results

    def evaluate_test_set(self, test_df):
        if test_df.empty:
            return None
        if self.calibrator is None or self.threshold is None:
            raise ValueError("The model and frozen Stage-2 cutoff must exist.")

        target_col = self.config["project"]["target_variable"]
        y_true = test_df[target_col].astype(int)
        probabilities = self._probabilities(test_df)
        predictions = (probabilities >= self.threshold).astype(int)
        ranked_cutoff = np.sort(np.asarray(probabilities))[::-1][
            max(0, int(np.ceil(len(probabilities) * self.cutoff_percent / 100.0)) - 1)
        ]
        ranked_predictions = (probabilities >= ranked_cutoff).astype(int)

        report = {
            "test_rows": int(len(test_df)),
            "actual_positive_rows": int(y_true.sum()),
            "frozen_cutoff_percent": self.cutoff_percent,
            "threshold": self.threshold,
            "predicted_positive": int(predictions.sum()),
            "reviewed_population_percent": float(predictions.mean() * 100.0),
            "precision": float(precision_score(y_true, predictions, zero_division=0)),
            "recall": float(recall_score(y_true, predictions, zero_division=0)),
            "pr_auc": float(average_precision_score(y_true, probabilities)),
            "balanced_accuracy": float(
                balanced_accuracy_score(y_true, predictions)
            ),
            "f2": float(fbeta_score(y_true, predictions, beta=2, zero_division=0)),
            "brier_score": float(brier_score_loss(y_true, probabilities)),
            "frozen_percentile_recall": float(
                recall_score(y_true, ranked_predictions, zero_division=0)
            ),
            "frozen_percentile_lift": float(
                (recall_score(y_true, ranked_predictions, zero_division=0) * 100.0)
                / self.cutoff_percent
            ),
        }
        self.test_results_ = report
        return report

    def score_active_set(self, active_df):
        if self.calibrator is None or self.threshold is None:
            raise ValueError("The model and frozen Stage-2 cutoff must exist.")
        scored = active_df.copy()
        scored["p_default"] = self._probabilities(active_df)
        scored["threshold"] = self.threshold
        scored["review_cutoff_percent"] = self.cutoff_percent
        scored["review_flag"] = (scored["p_default"] >= self.threshold).astype(int)
        self.active_scores_ = scored
        return scored

    def _save_gains_plot(self, output_path):
        if self.validation_gains_.empty:
            return None
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        chart = self.validation_gains_
        fig, axes = plt.subplots(2, 1, figsize=(9, 10), sharex=True)
        axes[0].plot(
            chart["population_percent"],
            chart["cumulative_gains_percent"],
            marker="o",
            label="Cumulative gains",
        )
        axes[0].plot([0, 100], [0, 100], "--", label="Random selection")
        axes[0].axvline(
            self.cutoff_metadata_["population_percent"],
            color="tab:red",
            linestyle=":",
            label=f"Selected k = {self.cutoff_percent:g}%",
        )
        axes[0].set_ylabel("Cumulative gains (%)")
        axes[0].legend()
        axes[0].grid(alpha=0.3)
        axes[1].plot(
            chart["population_percent"], chart["lift"], marker="o", color="tab:orange"
        )
        axes[1].axhline(1.0, linestyle="--", label="Random lift")
        axes[1].axvline(
            self.cutoff_metadata_["population_percent"],
            color="tab:red",
            linestyle=":",
        )
        axes[1].set_xlabel("Validation population reviewed (%)")
        axes[1].set_ylabel("Lift")
        axes[1].grid(alpha=0.3)
        fig.suptitle(f"SBA Stage-2 validation gains and lift: {self.model_name}")
        fig.tight_layout()
        fig.savefig(output_path, dpi=180, bbox_inches="tight")
        plt.close(fig)
        return output_path

    def export_artifacts(self, out_dir: str = None):
        export_path = Path(out_dir or self.runner.path_coordinator.modeling_output_path)
        export_path.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.transformer, export_path / "sba_transformer.pkl")
        joblib.dump({"stage_1": self.model}, export_path / "sba_models.pkl")
        joblib.dump(
            {"stage_1": self.calibrator}, export_path / "sba_calibrators.pkl"
        )
        joblib.dump(
            {
                "stage_2": {
                    "cutoff_percent": self.cutoff_percent,
                    "score_threshold": self.threshold,
                    "tie_policy": self.cutoff_metadata_["tie_policy"],
                }
            },
            export_path / "sba_thresholds.pkl",
        )
        joblib.dump(self.config, export_path / "config.pkl")
        self.validation_gains_.to_csv(
            export_path / "validation_gains_lift.csv", index=False
        )
        gains_plot = self._save_gains_plot(
            export_path / "validation_gains_lift.png"
        )
        if self.active_scores_ is not None:
            self.active_scores_.to_csv(
                export_path / "scored_active_loans.csv", index=True
            )

        metadata = {
            "model_name": self.model_name,
            "features": self.transformer.raw_feature_names_,
            "transformed_features": self.transformer.feature_names_,
            "feature_screen": {
                "source": "https://github.com/rajivsam/imbalanced_feature_screener/tree/master",
                "selection_mode": "fixed_external_screen",
            },
            "target": self.config["project"]["target_variable"],
            "stage_2_cutoff": self.cutoff_metadata_,
            "stage_1_results": self.model_results_,
            "test_results": self.test_results_,
            "validation_gains_lift_file": "validation_gains_lift.csv",
            "validation_gains_lift_chart": (
                gains_plot.name if gains_plot is not None else None
            ),
            "stages": ["stage_1_model", "stage_2_cutoff", "stage_3_evaluation"],
        }
        with open(export_path / "metadata.json", "w") as stream:
            json.dump(metadata, stream, indent=2)
