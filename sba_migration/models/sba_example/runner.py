import json
import os
import warnings
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
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
        self.training_target_name = self.config["project"].get("target_variable", "loan_status_r")
        self.stage_1_model_name = None
        self.stage_1_model = None
        self.stage_1_calibrator = None
        self.stage_1_threshold = None
        self.stage_1_results_ = []
        self.stage_2_model_name = None
        self.stage_2_model = None
        self.stage_2_calibrator = None
        self.stage_2_threshold = None
        self.stage_2_results_ = []

    def _get_candidate_class(self, class_path: str):
        module_name, class_name = class_path.rsplit(".", 1)
        module = __import__(module_name, fromlist=[class_name])
        return getattr(module, class_name)

    def _utility_defaults(self):
        settings = self.config.get("experiment_settings", {})
        return {
            "default_loan_age_months": float(settings.get("default_loan_age_months", 24.0)),
            "default_loss_rate": float(settings.get("default_loss_rate", 0.35)),
            "manual_review_cost": float(settings.get("manual_review_cost", 1500.0)),
            "default_annuity_rate": float(settings.get("default_annuity_rate", 0.06)),
            "default_term_months": float(settings.get("default_term_months", 120.0)),
            "default_guarantee_share": float(settings.get("default_guarantee_share", 0.75)),
            "default_guarantee_fee_rate": float(settings.get("default_guarantee_fee_rate", 0.0125)),
            "utility_safety_factor": float(settings.get("utility_safety_factor", 1.5)),
        }

    def _resolve_loan_amount(self, df):
        for col in ("grossapproval", "loan_amount", "principal_amount"):
            if col in df.columns:
                return pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        return pd.Series(0.0, index=df.index, dtype=float)

    def _resolve_annual_rate(self, df):
        for col in ("initialinterestrate", "apr", "interest_rate"):
            if col in df.columns:
                rate = pd.to_numeric(df[col], errors="coerce").fillna(0.0) / 100.0
                return rate.where(rate > 0, 0.0)
        return pd.Series(self._utility_defaults()["default_annuity_rate"], index=df.index, dtype=float)

    def _resolve_term_months(self, df):
        for col in ("terminmonths", "term_months", "loan_term_months"):
            if col in df.columns:
                term = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
                return term.where(term > 0, 1.0)
        return pd.Series(self._utility_defaults()["default_term_months"], index=df.index, dtype=float)

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
            reference_col = "AsOfDate" if "AsOfDate" in df.columns else "asofdate"
            reference_dates = pd.to_datetime(df[reference_col], errors="coerce") if reference_col in df.columns else pd.Timestamp.utcnow()
            reference_dates = pd.Series(reference_dates, index=df.index)
            if isinstance(reference_dates.iloc[0], pd.Timestamp):
                reference_dates = pd.to_datetime(reference_dates, errors="coerce")
            merged = date_candidates[0].copy()
            for ts in date_candidates[1:]:
                merged = merged.fillna(ts)
            age_series = (reference_dates - merged).dt.total_seconds() / (30.4375 * 24 * 60 * 60)
            age_series = age_series.fillna(default_months)

        return age_series.clip(lower=0).astype(float)

    def _compute_estimated_balance(self, df):
        principal = self._resolve_loan_amount(df)
        annual_rate = self._resolve_annual_rate(df)
        term_months = self._resolve_term_months(df)
        loan_age_months = self._compute_loan_age_months(df)
        default_term = term_months.where(term_months > 0, 1.0)

        rate = annual_rate / 12.0
        month_fraction = loan_age_months.clip(lower=0)

        no_rate_balance = principal * np.maximum(0.0, 1.0 - (month_fraction / default_term))
        if (rate <= 0).all():
            return no_rate_balance.fillna(0.0)

        term_power = np.power(1.0 + rate, default_term)
        payment_denom = np.where(default_term > 0, term_power - 1.0, 1.0)
        monthly_payment = np.divide(
            principal * rate * term_power,
            payment_denom,
            out=np.zeros_like(principal, dtype=float),
            where=(default_term > 0) & (np.abs(payment_denom) > 1e-12),
        )

        age_power = np.power(1.0 + rate, month_fraction)
        age_factor = np.divide(
            age_power - 1.0,
            rate,
            out=np.zeros_like(principal, dtype=float),
            where=(month_fraction > 0) & (np.abs(rate) > 1e-12),
        )
        remaining_balance = principal * age_power - monthly_payment * age_factor
        remaining_balance = np.where(month_fraction > 0, remaining_balance, principal)
        remaining_balance = np.where(remaining_balance < 0, 0.0, remaining_balance)
        return pd.Series(np.maximum(remaining_balance, no_rate_balance), index=df.index, dtype=float)

    def _compute_guarantee_fee_proxy(self, df, principal=None):
        if principal is None:
            principal = self._resolve_loan_amount(df)
        defaults = self._utility_defaults()
        share = defaults["default_guarantee_share"]
        if "sbaguaranteedapproval" in df.columns:
            guaranteed_amount = pd.to_numeric(df["sbaguaranteedapproval"], errors="coerce").fillna(0.0)
            return guaranteed_amount * defaults["default_guarantee_fee_rate"]
        if "guarantee_amount" in df.columns:
            guaranteed_amount = pd.to_numeric(df["guarantee_amount"], errors="coerce").fillna(0.0)
            return guaranteed_amount * defaults["default_guarantee_fee_rate"]
        return principal * share * defaults["default_guarantee_fee_rate"]

    def _use_action_target(self):
        settings = self.config.get("experiment_settings", {})
        return bool(settings.get("use_action_target", False))

    def _resolve_target_column(self, df=None):
        if self._use_action_target() and df is not None and "action_target" in df.columns:
            return "action_target"
        return self.training_target_name

    def _feature_columns(self, df, target_col=None):
        if target_col is None:
            target_col = self._resolve_target_column(df)
        columns = [c for c in ["hdgc", "hdbc", "loan_age_months", "default_utility_score"] if c in df.columns]
        if columns:
            return columns
        return [c for c in df.columns if c != target_col]

    def _build_action_target(self, df):
        df = df.copy()
        target_name = self.config["project"].get("target_variable", "loan_status_r")
        if target_name not in df.columns:
            return df

        target_series = pd.to_numeric(df[target_name], errors="coerce").fillna(0).astype(int)
        if "loan_age_months" not in df.columns:
            df["loan_age_months"] = self._compute_loan_age_months(df)
        if "estimated_balance" not in df.columns and "residual_amount" not in df.columns:
            df["estimated_balance"] = self._compute_estimated_balance(df)
        if "estimated_balance" in df.columns:
            df["estimated_balance"] = pd.to_numeric(df["estimated_balance"], errors="coerce").fillna(0.0)
        if "residual_amount" in df.columns:
            df["residual_amount"] = pd.to_numeric(df["residual_amount"], errors="coerce").fillna(0.0)

        balance_col = "estimated_balance" if "estimated_balance" in df.columns else "residual_amount"
        principal = self._resolve_loan_amount(df)
        balance = pd.to_numeric(df[balance_col], errors="coerce").fillna(0.0)
        balance_ratio = balance / principal.replace(0, np.nan)
        balance_ratio = balance_ratio.fillna(0.0)

        action_target = pd.Series(0, index=df.index, dtype=int)
        action_target[target_series == 1] = 1

        high_exposure_mask = (
            (target_series == 0)
            & (pd.to_numeric(df["loan_age_months"], errors="coerce").fillna(0).clip(lower=0) >= 18)
            & (balance_ratio >= 0.75)
        )
        action_target[high_exposure_mask] = 1
        df["action_target"] = action_target
        return df

    def _leakage_guard(self, df):
        forbidden = {"dataset_partition", "record_id", "loan_status_r", "action_target"}
        feature_columns = [c for c in df.columns if c not in forbidden]
        if "dataset_partition" in df.columns:
            feature_columns = [c for c in feature_columns if c != "dataset_partition"]
        if "loan_status_r" in feature_columns:
            feature_columns = [c for c in feature_columns if c != "loan_status_r"]
        return feature_columns

    def _utility_thresholds(self, df, p_default, safety_factor=None):
        principal = self._resolve_loan_amount(df)
        annual_rate = self._resolve_annual_rate(df)
        term_months = self._resolve_term_months(df)
        estimated_balance = self._compute_estimated_balance(df)
        guarantee_fee_proxy = self._compute_guarantee_fee_proxy(df, principal)
        if safety_factor is None:
            safety_factor = self._utility_defaults()["utility_safety_factor"]

        monthly_rate = annual_rate / 12.0
        term_power = np.power(1.0 + monthly_rate, term_months)
        payment_denom = np.where(term_months > 0, term_power - 1.0, 1.0)
        monthly_payment = np.divide(
            principal * monthly_rate * term_power,
            payment_denom,
            out=np.zeros_like(principal, dtype=float),
            where=(term_months > 0) & (np.abs(payment_denom) > 1e-12),
        )
        gross_interest_revenue = np.maximum(0.0, monthly_payment * term_months - principal)
        loss_amount = np.maximum(0.0, estimated_balance + guarantee_fee_proxy)
        p_default = np.asarray(p_default, dtype=float)
        p_payback = np.maximum(0.0, 1.0 - p_default)
        u_payback = p_payback * gross_interest_revenue
        u_default = p_default * loss_amount
        u_default_risk_buffer = safety_factor * u_default

        # Threshold should be the fixed default-probability cutoff at which expected payback
        # and expected loss are equal after applying the risk buffer, not a probability that
        # depends on the same p_default term used on both sides of the comparison.
        threshold = np.divide(
            gross_interest_revenue,
            gross_interest_revenue + safety_factor * loss_amount,
            out=np.full_like(p_default, 0.5, dtype=float),
            where=(gross_interest_revenue + safety_factor * loss_amount) > 0,
        )
        action = (p_default >= threshold).astype(int)
        return action, threshold, u_payback, u_default_risk_buffer

    def _profit_loss_summary(self, df, y_true, action):
        principal = self._resolve_loan_amount(df)
        annual_rate = self._resolve_annual_rate(df)
        term_months = self._resolve_term_months(df)
        estimated_balance = self._compute_estimated_balance(df)
        guarantee_fee_proxy = self._compute_guarantee_fee_proxy(df, principal)

        monthly_rate = annual_rate / 12.0
        term_power = np.power(1.0 + monthly_rate, term_months)
        payment_denom = np.where(term_months > 0, term_power - 1.0, 1.0)
        monthly_payment = np.divide(
            principal * monthly_rate * term_power,
            payment_denom,
            out=np.zeros_like(principal, dtype=float),
            where=(term_months > 0) & (np.abs(payment_denom) > 1e-12),
        )
        gross_interest_revenue = np.maximum(0.0, monthly_payment * term_months - principal)

        profit = np.where((y_true == 1) & (action == 1), gross_interest_revenue, 0.0)
        loss = np.where((y_true == 1) & (action == 0), estimated_balance + guarantee_fee_proxy, 0.0)
        loss = loss + np.where((y_true == 0) & (action == 1), guarantee_fee_proxy, 0.0)
        y_true_arr = np.asarray(y_true, dtype=int)
        action_arr = np.asarray(action, dtype=int)
        precision = precision_score(y_true_arr, action_arr, zero_division=0)
        recall = recall_score(y_true_arr, action_arr, zero_division=0)
        net_profit = float(profit.sum() - loss.sum())
        return {
            "profit_total": float(profit.sum()),
            "loss_total": float(loss.sum()),
            "net_profit_total": net_profit,
            "precision": float(precision),
            "recall": float(recall),
            "predicted_positive": int(action_arr.sum()),
        }

    def _safety_factor_grid(self, min_factor=1.0, max_factor=10.0, steps=91):
        return np.round(np.linspace(min_factor, max_factor, int(steps)), 3)

    def _save_safety_factor_plot(self, sweep_results, output_dir="output/utility_tuning"):
        results_df = pd.DataFrame(sweep_results)
        if results_df.empty:
            return None
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(results_df["safety_factor"], results_df["net_profit_total"], marker="o", linewidth=2)
        ax.set_xlabel("Safety factor")
        ax.set_ylabel("Net profit (profit - loss)")
        ax.set_title("Validation-set utility safety factor sweep")
        ax.grid(True, alpha=0.3)
        best_row = results_df.loc[results_df["net_profit_total"].idxmax()]
        ax.axvline(best_row["safety_factor"], linestyle="--", color="tab:red", label=f"Best factor = {best_row['safety_factor']:.3f}")
        ax.legend()
        fig.tight_layout()
        plot_path = output_path / "validation_safety_factor_profit_curve.png"
        fig.savefig(plot_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        return plot_path

    def tune_safety_factor_on_validation(self, validation_df, output_dir="output/utility_tuning"):
        if validation_df.empty:
            raise ValueError("Validation data is empty; cannot tune the utility safety factor.")

        target_col = self.config["project"]["target_variable"]
        if self.stage_1_model is None or self.stage_1_calibrator is None:
            raise ValueError("Stage 1 model and calibrator must be fitted before tuning the safety factor.")

        feature_cols = [c for c in ["hdgc", "hdbc", "loan_age_months", "default_utility_score"] if c in validation_df.columns]
        if not feature_cols:
            feature_cols = [c for c in validation_df.columns if c != target_col]

        y_true = validation_df[target_col].astype(int).to_numpy()
        y_prob = np.asarray(
            self.stage_1_calibrator.predict(self.stage_1_model.predict_proba(validation_df[feature_cols])[:, 1]),
            dtype=float,
        )

        sweep_results = []
        for safety_factor in self._safety_factor_grid():
            action, _, _, _ = self._utility_thresholds(validation_df, y_prob, safety_factor=float(safety_factor))
            metrics = self._profit_loss_summary(validation_df, y_true, action)
            row = {
                "safety_factor": float(safety_factor),
                **metrics,
            }
            sweep_results.append(row)

        best_row = max(sweep_results, key=lambda row: (row["net_profit_total"], row["profit_total"], row["recall"], row["precision"]))
        self.best_safety_factor_ = float(best_row["safety_factor"])
        self.validation_safety_factor_results_ = sweep_results
        self.validation_safety_factor_plot_path_ = self._save_safety_factor_plot(sweep_results, output_dir)

        results_df = pd.DataFrame(sweep_results)
        results_csv = Path(output_dir) / "validation_safety_factor_tuning.csv"
        results_csv.parent.mkdir(parents=True, exist_ok=True)
        results_df.to_csv(results_csv, index=False)

        return best_row, sweep_results

    def _ensure_utility_features(self, df):
        df = df.copy()
        defaults = self._utility_defaults()
        default_months = defaults["default_loan_age_months"]

        if "loan_age_months" not in df.columns:
            df["loan_age_months"] = self._compute_loan_age_months(df)
        else:
            df["loan_age_months"] = pd.to_numeric(df["loan_age_months"], errors="coerce").fillna(default_months)

        if "estimated_balance" not in df.columns and "residual_amount" not in df.columns:
            df["estimated_balance"] = self._compute_estimated_balance(df)
        if "estimated_balance" in df.columns:
            df["estimated_balance"] = pd.to_numeric(df["estimated_balance"], errors="coerce").fillna(0.0)
        if "residual_amount" in df.columns:
            df["residual_amount"] = pd.to_numeric(df["residual_amount"], errors="coerce").fillna(0.0)

        if "estimated_balance" not in df.columns and "residual_amount" in df.columns:
            df["estimated_balance"] = df["residual_amount"]
        elif "residual_amount" not in df.columns and "estimated_balance" in df.columns:
            df["residual_amount"] = df["estimated_balance"]

        if "guarantee_fee_proxy" not in df.columns:
            df["guarantee_fee_proxy"] = self._compute_guarantee_fee_proxy(df, self._resolve_loan_amount(df))

        df["loan_age_months"] = pd.to_numeric(df["loan_age_months"], errors="coerce").fillna(default_months).clip(lower=0)
        if "estimated_balance" in df.columns:
            df["estimated_balance"] = pd.to_numeric(df["estimated_balance"], errors="coerce").fillna(0.0)
        if "residual_amount" in df.columns:
            df["residual_amount"] = pd.to_numeric(df["residual_amount"], errors="coerce").fillna(0.0)
        df["guarantee_fee_proxy"] = pd.to_numeric(df["guarantee_fee_proxy"], errors="coerce").fillna(0.0)
        return df

    def load_data(self):
        df = self.runner.X.copy()
        target_name = self.config["project"].get("target_variable", "loan_status_r")
        df[target_name] = self.runner.y
        df = self._ensure_utility_features(df)
        if self._use_action_target():
            df = self._build_action_target(df)
            self.training_target_name = "action_target" if "action_target" in df.columns else target_name
        else:
            self.training_target_name = target_name
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
        target_col = self._resolve_target_column(df)

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

        target_col = self._resolve_target_column(train_df)

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

        for df in (train_df, validation_df, test_df, active_df):
            if df.empty:
                continue
            if "loan_age_months" not in df.columns:
                df["loan_age_months"] = self._compute_loan_age_months(df)
            if "estimated_balance" not in df.columns and "residual_amount" not in df.columns:
                df["estimated_balance"] = self._compute_estimated_balance(df)
            if "estimated_balance" in df.columns:
                df["estimated_balance"] = pd.to_numeric(df["estimated_balance"], errors="coerce").fillna(0.0)
            if "residual_amount" in df.columns:
                df["residual_amount"] = pd.to_numeric(df["residual_amount"], errors="coerce").fillna(0.0)
            if "guarantee_fee_proxy" not in df.columns:
                df["guarantee_fee_proxy"] = self._compute_guarantee_fee_proxy(df, self._resolve_loan_amount(df))

        return train_df, validation_df, test_df, active_df

    def _threshold_policy(self, stage_name: str):
        threshold_policy = self.config.get("experiment_settings", {}).get("threshold_policy", {})
        if isinstance(threshold_policy, dict):
            threshold_policy = threshold_policy.get(stage_name, threshold_policy)
        return {
            "objective": threshold_policy.get("objective", "recall"),
            "min_recall": float(threshold_policy.get("min_recall", 0.90)),
            "min_precision": float(threshold_policy.get("min_precision", 0.0)),
        }

    def _utility_value(
        self,
        y_true,
        y_prob,
        threshold,
        grossapproval,
        loan_age_months,
        annual_rate=None,
        term_months=None,
        estimated_balance=None,
        guarantee_fee_proxy=None,
    ):
        y_pred = (y_prob >= threshold).astype(int)
        principal = np.asarray(grossapproval, dtype=float)
        age_months = np.asarray(loan_age_months, dtype=float)
        if estimated_balance is None:
            estimated_balance = principal.copy()
        else:
            estimated_balance = np.asarray(estimated_balance, dtype=float)

        if guarantee_fee_proxy is None:
            guarantee_fee_proxy = np.zeros_like(principal, dtype=float)
        else:
            guarantee_fee_proxy = np.asarray(guarantee_fee_proxy, dtype=float)

        if annual_rate is None:
            annual_rate = np.asarray(self._resolve_annual_rate(pd.DataFrame({"grossapproval": principal, "initialinterestrate": np.zeros_like(principal)})), dtype=float)
        else:
            annual_rate = np.asarray(annual_rate, dtype=float)

        if term_months is None:
            term_months = np.asarray(self._resolve_term_months(pd.DataFrame({"terminmonths": np.ones_like(principal, dtype=float)})), dtype=float)
        else:
            term_months = np.asarray(term_months, dtype=float)

        monthly_rate = annual_rate / 12.0
        term_power = np.power(1.0 + monthly_rate, term_months)
        payment_denom = np.where(term_months > 0, term_power - 1.0, 1.0)
        monthly_payment = np.divide(
            principal * monthly_rate * term_power,
            payment_denom,
            out=np.zeros_like(principal, dtype=float),
            where=(term_months > 0) & (np.abs(payment_denom) > 1e-12),
        )
        gross_interest = np.maximum(0.0, monthly_payment * term_months - principal)

        value = np.where(
            (y_true == 1) & (y_pred == 1),
            gross_interest,
            np.where(
                (y_true == 0) & (y_pred == 1),
                -guarantee_fee_proxy,
                np.where((y_true == 1) & (y_pred == 0), -(estimated_balance + guarantee_fee_proxy), 0.0),
            ),
        )
        return float(np.sum(value))

    def _select_threshold(
        self,
        y_true,
        y_prob,
        objective=None,
        min_recall=None,
        min_precision=None,
        grossapproval=None,
        loan_age_months=None,
        annual_rate=None,
        term_months=None,
        estimated_balance=None,
        guarantee_fee_proxy=None,
    ):
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
                utility_score = self._utility_value(
                    y_true,
                    y_prob,
                    threshold,
                    grossapproval,
                    loan_age_months,
                    annual_rate=self._resolve_annual_rate(pd.DataFrame({"grossapproval": np.asarray(grossapproval, dtype=float), "initialinterestrate": np.zeros_like(np.asarray(grossapproval, dtype=float))})),
                    term_months=self._resolve_term_months(pd.DataFrame({"terminmonths": np.ones_like(np.asarray(grossapproval, dtype=float), dtype=float)})),
                    estimated_balance=estimated_balance,
                    guarantee_fee_proxy=guarantee_fee_proxy,
                )
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
                    utility_score = self._utility_value(
                        y_true,
                        y_prob,
                        threshold,
                        grossapproval,
                        loan_age_months,
                        estimated_balance=estimated_balance,
                        guarantee_fee_proxy=guarantee_fee_proxy,
                    )
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

    def _select_profit_threshold(self, y_true, y_prob, df=None, min_precision=0.0, min_recall=0.0):
        y_true_arr = np.asarray(y_true, dtype=int).ravel()
        y_prob_arr = np.asarray(y_prob, dtype=float).ravel()
        thresholds = np.unique(np.concatenate(([0.0, 1.0], y_prob_arr)))
        best = None
        best_key = None
        for threshold in np.sort(thresholds)[::-1]:
            y_pred = (y_prob_arr >= threshold).astype(int)
            precision = precision_score(y_true_arr, y_pred, zero_division=0)
            recall_value = recall_score(y_true_arr, y_pred, zero_division=0)
            if recall_value < min_recall or precision < min_precision:
                continue
            if df is not None:
                metrics = self._profit_loss_summary(df, y_true_arr, y_pred)
                key = (metrics["net_profit_total"], metrics["profit_total"], precision, recall_value)
            else:
                key = (float((y_pred == 1).sum()), float(precision), float(recall_value))
            if best is None or key > best_key:
                best = {
                    "threshold": float(threshold),
                    "precision": float(precision),
                    "recall": float(recall_value),
                    "net_profit_total": float(metrics["net_profit_total"]) if df is not None else 0.0,
                    "profit_total": float(metrics["profit_total"]) if df is not None else 0.0,
                    "loss_total": float(metrics["loss_total"]) if df is not None else 0.0,
                }
                best_key = key
        if best is None:
            default_threshold = float(np.median(y_prob_arr)) if len(y_prob_arr) else 0.5
            default_pred = (y_prob_arr >= default_threshold).astype(int)
            precision = precision_score(y_true_arr, default_pred, zero_division=0)
            recall_value = recall_score(y_true_arr, default_pred, zero_division=0)
            metrics = self._profit_loss_summary(df, y_true_arr, default_pred) if df is not None else {"net_profit_total": 0.0, "profit_total": 0.0, "loss_total": 0.0}
            best = {
                "threshold": float(default_threshold),
                "precision": float(precision),
                "recall": float(recall_value),
                "net_profit_total": float(metrics["net_profit_total"]) if df is not None else 0.0,
                "profit_total": float(metrics["profit_total"]) if df is not None else 0.0,
                "loss_total": float(metrics["loss_total"]) if df is not None else 0.0,
            }
        return best["threshold"], best

    def _fit_candidate(self, candidate_cfg, train_df, eval_df, stage_name: str):
        target_col = self._resolve_target_column(train_df)
        model_name = candidate_cfg["name"]
        candidate_class = self._get_candidate_class(candidate_cfg["class_path"])
        params = candidate_cfg.get("hyperparameters", {})

        estimator = candidate_class(params)
        feature_cols = self._feature_columns(train_df, target_col)
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

        best = max(results, key=lambda item: (item["recall"], item["pr_auc"], item["precision"], item["f2"]))
        self.stage_1_model_name = best["model_name"]
        self.stage_1_model = self.models[self.stage_1_model_name]
        self.stage_1_calibrator = self.calibrators[self.stage_1_model_name]
        self.stage_1_threshold = float(best["threshold"])
        self.stage_1_results_ = results
        return pd.DataFrame(results)

    def fit_stage_2(self, train_df, validation_df):
        if self.stage_1_model is None or self.stage_1_calibrator is None:
            raise ValueError("Stage 1 model and calibrator must be fit before fitting stage 2.")

        target_col = self._resolve_target_column(train_df)
        train_stage_1_mask, _ = self._stage_positive_mask(train_df, self.stage_1_model, self.stage_1_calibrator, self.stage_1_threshold)
        valid_stage_1_mask, _ = self._stage_positive_mask(validation_df, self.stage_1_model, self.stage_1_calibrator, self.stage_1_threshold)

        train_stage_2 = train_df.loc[train_stage_1_mask].copy()
        valid_stage_2 = validation_df.loc[valid_stage_1_mask].copy()

        if train_stage_2.empty or valid_stage_2.empty:
            warnings.warn(
                "No stage-2 rows remain after stage-1 recall-first filtering; falling back to stage-1 predictions.",
                RuntimeWarning,
            )
            self.stage_2_model_name = self.stage_1_model_name
            self.stage_2_model = self.stage_1_model
            self.stage_2_calibrator = self.stage_1_calibrator
            self.stage_2_threshold = float(self.stage_1_threshold)
            self.stage_2_results_ = []
            return pd.DataFrame(self.stage_2_results_)

        self.stage_2_model = None
        self.stage_2_calibrator = None
        self.stage_2_threshold = None
        best_result = None
        for candidate_cfg in self.config.get("candidates", []):
            model_name = candidate_cfg["name"]
            candidate_class = self._get_candidate_class(candidate_cfg["class_path"])
            params = candidate_cfg.get("hyperparameters", {})

            estimator = candidate_class(params)
            feature_cols = self._feature_columns(train_stage_2, target_col)
            estimator.fit(train_stage_2[feature_cols], train_stage_2[target_col])
            raw_prob = estimator.predict_proba(valid_stage_2[feature_cols])[:, 1]
            calibrator = ProbabilityCalibrator().fit(raw_prob, valid_stage_2[target_col])
            prob = calibrator.predict(raw_prob)
            threshold, metrics = self._select_profit_threshold(
                valid_stage_2[target_col],
                prob,
                df=valid_stage_2,
                min_precision=0.0,
                min_recall=0.0,
            )
            result = {
                "stage": "stage_2",
                "model_name": model_name,
                "threshold": float(threshold),
                "pr_auc": float(average_precision_score(valid_stage_2[target_col], prob)),
                "precision": float(metrics["precision"]),
                "recall": float(metrics["recall"]),
                "net_profit_total": float(metrics["net_profit_total"]),
                "profit_total": float(metrics["profit_total"]),
                "loss_total": float(metrics["loss_total"]),
            }
            if best_result is None or (result["net_profit_total"], result["pr_auc"], result["precision"], result["recall"]) > (
                best_result["net_profit_total"], best_result["pr_auc"], best_result["precision"], best_result["recall"]
            ):
                best_result = result
                self.stage_2_model_name = model_name
                self.stage_2_model = estimator
                self.stage_2_calibrator = calibrator
                self.stage_2_threshold = float(threshold)
                self.stage_2_results_ = [result]

        if best_result is None:
            self.stage_2_model_name = self.stage_1_model_name
            self.stage_2_model = self.stage_1_model
            self.stage_2_calibrator = self.stage_1_calibrator
            self.stage_2_threshold = float(self.stage_1_threshold)
            self.stage_2_results_ = []
            return pd.DataFrame(self.stage_2_results_)

        return pd.DataFrame(self.stage_2_results_)

    def _stage_positive_mask(self, df, model, calibrator, threshold):
        feature_cols = self._feature_columns(df, self._resolve_target_column(df))
        raw_prob = model.predict_proba(df[feature_cols])[:, 1]
        prob = calibrator.predict(raw_prob)
        return (prob >= threshold).astype(bool), prob

    def fit_and_calibrate(self, train_df, validation_df):
        results = self.fit_stage_1(train_df, validation_df)
        self.fit_stage_2(train_df, validation_df)
        return results

    def _cascade_predict(self, df):
        if self.stage_1_model is None:
            raise ValueError("Stage 1 model must be fit before prediction.")

        stage_1_mask, stage_1_prob = self._stage_positive_mask(df, self.stage_1_model, self.stage_1_calibrator, self.stage_1_threshold)
        final_pred = np.zeros(len(df), dtype=int)
        if self.stage_2_model is not None and self.stage_2_calibrator is not None and stage_1_mask.any():
            screened_df = df.loc[stage_1_mask].copy()
            feature_cols = self._feature_columns(screened_df, self._resolve_target_column(screened_df))
            stage_2_raw = self.stage_2_model.predict_proba(screened_df[feature_cols])[:, 1]
            stage_2_prob = self.stage_2_calibrator.predict(stage_2_raw)
            final_pred[stage_1_mask] = (stage_2_prob >= self.stage_2_threshold).astype(int)
        else:
            final_pred = stage_1_mask.astype(int)
        return final_pred.astype(int), stage_1_mask.astype(int), stage_1_prob, final_pred.astype(float)

    def evaluate_test_set(self, test_df):
        if test_df.empty:
            warnings.warn(
                "No test rows are present in the canonical dataset_partition; skipping final test evaluation.",
                RuntimeWarning,
            )
            return None

        if self.stage_1_model is None:
            raise ValueError("Stage 1 model must be fit before evaluation.")

        target_col = self._resolve_target_column(test_df)
        y_true = test_df[target_col].astype(int)
        feature_cols = [c for c in ["hdgc", "hdbc", "loan_age_months", "default_utility_score"] if c in test_df.columns]
        if not feature_cols:
            feature_cols = [c for c in test_df.columns if c not in {target_col, "dataset_partition", "loan_status_r", "action_target"}]
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
            "final_threshold": float(self.stage_1_threshold),
            "stage_1_precision": float(stage_1_precision),
            "stage_1_recall": float(stage_1_recall),
            "stage_1_predicted_positive": int(stage_1_pred.sum()),
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
        active_df = active_df.copy()
        active_df["stage_1_probability"] = stage_1_prob
        active_df["stage_1_prediction"] = stage_1_mask.astype(int)
        active_df["final_prediction"] = stage_1_mask.astype(int)
        active_df["threshold"] = float(self.stage_1_threshold)
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
