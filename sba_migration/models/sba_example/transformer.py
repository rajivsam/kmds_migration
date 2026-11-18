import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import OrdinalEncoder

from ..core.base import BaseFeatureTransformer


class SBAScreenedFeatureTransformer(BaseFeatureTransformer, BaseEstimator, TransformerMixin):
    """Preprocess the fixed predictor screen without learning a new feature subset."""

    raw_feature_names_ = [
        "bankname",
        "initialinterestrate",
        "terminmonths",
        "borrstreet",
        "sbadistrictoffice",
        "projectcounty",
        "bankstate",
        "borrcity",
        "processingmethod",
        "loan_age_months",
    ]
    categorical_columns_ = [
        "bankname",
        "borrstreet",
        "sbadistrictoffice",
        "projectcounty",
        "bankstate",
        "borrcity",
        "processingmethod",
    ]
    numeric_columns_ = [
        "initialinterestrate",
        "terminmonths",
        "loan_age_months",
    ]
    feature_names_ = [
        "bankname_encoded",
        "initialinterestrate",
        "terminmonths",
        "borrstreet_encoded",
        "sbadistrictoffice_encoded",
        "projectcounty_encoded",
        "bankstate_encoded",
        "borrcity_encoded",
        "processingmethod_encoded",
        "loan_age_months",
    ]

    def fit(self, X: pd.DataFrame, y: pd.Series = None):
        missing = [column for column in self.raw_feature_names_ if column not in X.columns]
        if missing:
            raise ValueError(f"Missing required screened predictors: {missing}")

        self.numeric_medians_ = {
            column: float(pd.to_numeric(X[column], errors="coerce").median())
            for column in self.numeric_columns_
        }

        categorical = pd.DataFrame(index=X.index)
        for column in self.categorical_columns_:
            categorical[column] = X[column].fillna("__MISSING__").astype(str)

        self.categorical_encoder_ = OrdinalEncoder(
            handle_unknown="use_encoded_value",
            unknown_value=np.nan,
            dtype=float,
        )
        self.categorical_encoder_.fit(categorical[self.categorical_columns_])
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        if not hasattr(self, "categorical_encoder_"):
            raise RuntimeError("SBAScreenedFeatureTransformer must be fitted before transform.")

        missing = [column for column in self.raw_feature_names_ if column not in X.columns]
        if missing:
            raise ValueError(f"Missing required screened predictors: {missing}")

        categorical = pd.DataFrame(index=X.index)
        for column in self.categorical_columns_:
            categorical[column] = X[column].fillna("__MISSING__").astype(str)
        encoded = self.categorical_encoder_.transform(categorical[self.categorical_columns_])
        encoded = np.nan_to_num(encoded, nan=-1.0)

        transformed = pd.DataFrame(index=X.index)
        transformed["bankname_encoded"] = encoded[:, 0]
        transformed["initialinterestrate"] = pd.to_numeric(
            X["initialinterestrate"], errors="coerce"
        ).fillna(self.numeric_medians_["initialinterestrate"])
        transformed["terminmonths"] = pd.to_numeric(
            X["terminmonths"], errors="coerce"
        ).fillna(self.numeric_medians_["terminmonths"])
        transformed["borrstreet_encoded"] = encoded[:, 1]
        transformed["sbadistrictoffice_encoded"] = encoded[:, 2]
        transformed["projectcounty_encoded"] = encoded[:, 3]
        transformed["bankstate_encoded"] = encoded[:, 4]
        transformed["borrcity_encoded"] = encoded[:, 5]
        transformed["processingmethod_encoded"] = encoded[:, 6]
        transformed["loan_age_months"] = pd.to_numeric(
            X["loan_age_months"], errors="coerce"
        ).fillna(self.numeric_medians_["loan_age_months"])
        return transformed[self.feature_names_]


# Backwards-compatible name retained for imports in older notebooks.
SBAClusterDistanceTransformer = SBAScreenedFeatureTransformer
