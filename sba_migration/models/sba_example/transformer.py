import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import OrdinalEncoder

from ..core.base import BaseFeatureTransformer


class SBAScreenedFeatureTransformer(BaseFeatureTransformer, BaseEstimator, TransformerMixin):
    """Preprocess the fixed predictor screen without learning a new feature subset."""

    raw_feature_names_ = [
        "initialinterestrate",
        "bankcity",
        "approvaldate",
        "terminmonths",
        "bankname",
    ]
    feature_names_ = [
        "initialinterestrate",
        "bankcity_encoded",
        "approvaldate_days",
        "terminmonths",
        "bankname_encoded",
    ]

    def fit(self, X: pd.DataFrame, y: pd.Series = None):
        missing = [column for column in self.raw_feature_names_ if column not in X.columns]
        if missing:
            raise ValueError(f"Missing required screened predictors: {missing}")

        self.numeric_medians_ = {
            "initialinterestrate": float(
                pd.to_numeric(X["initialinterestrate"], errors="coerce").median()
            ),
            "terminmonths": float(
                pd.to_numeric(X["terminmonths"], errors="coerce").median()
            ),
        }

        approval_dates = pd.to_datetime(X["approvaldate"], errors="coerce")
        approval_days = (approval_dates - pd.Timestamp("1970-01-01")).dt.days
        self.approvaldate_median_ = float(approval_days.median())

        categorical = pd.DataFrame(index=X.index)
        for column in ("bankcity", "bankname"):
            categorical[column] = X[column].fillna("__MISSING__").astype(str)

        self.categorical_encoder_ = OrdinalEncoder(
            handle_unknown="use_encoded_value",
            unknown_value=np.nan,
            dtype=float,
        )
        self.categorical_encoder_.fit(categorical[["bankcity", "bankname"]])
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        if not hasattr(self, "categorical_encoder_"):
            raise RuntimeError("SBAScreenedFeatureTransformer must be fitted before transform.")

        missing = [column for column in self.raw_feature_names_ if column not in X.columns]
        if missing:
            raise ValueError(f"Missing required screened predictors: {missing}")

        categorical = pd.DataFrame(index=X.index)
        for column in ("bankcity", "bankname"):
            categorical[column] = X[column].fillna("__MISSING__").astype(str)
        encoded = self.categorical_encoder_.transform(categorical[["bankcity", "bankname"]])
        encoded = np.nan_to_num(encoded, nan=-1.0)

        approval_dates = pd.to_datetime(X["approvaldate"], errors="coerce")
        approval_days = (
            approval_dates - pd.Timestamp("1970-01-01")
        ).dt.days.fillna(self.approvaldate_median_)

        transformed = pd.DataFrame(index=X.index)
        transformed["initialinterestrate"] = pd.to_numeric(
            X["initialinterestrate"], errors="coerce"
        ).fillna(self.numeric_medians_["initialinterestrate"])
        transformed["bankcity_encoded"] = encoded[:, 0]
        transformed["approvaldate_days"] = approval_days.astype(float)
        transformed["terminmonths"] = pd.to_numeric(
            X["terminmonths"], errors="coerce"
        ).fillna(self.numeric_medians_["terminmonths"])
        transformed["bankname_encoded"] = encoded[:, 1]
        return transformed[self.feature_names_]


# Backwards-compatible name retained for imports in older notebooks.
SBAClusterDistanceTransformer = SBAScreenedFeatureTransformer
