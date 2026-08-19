import pandas as pd
import numpy as np
import pgeocode
import os
import re
from typing import Dict, Optional, Tuple

from tabular.entity_tagging import get_stage_subset
from tabular.low_count_cat_var_encoding import get_categorical_subset
from tabular.hierarchical_low_count_var_encoding import hierarchical_recode_by_support_right
from tabular.merge_ops import merge_frames_by_index
from tabular.modeling_filter import filter_binary_universe, validate_binary_target
from tabular.train_val_split import assign_train_val_split
from tabular.target_encoding import (
    select_categorical_columns,
    fit_target_encoder,
    transform_with_encoder,
)
from tabular.feature_space import select_model_features, project_feature_space
from tabular.feature_space import plot_feature_selection_knee_curve


STATE_CENTROIDS: Dict[str, Tuple[float, float]] = {
    "AL": (32.806671, -86.791130), "AK": (61.370716, -152.404419),
    "AZ": (33.729759, -111.431221), "AR": (34.969704, -92.373123),
    "CA": (36.116203, -119.681564), "CO": (39.059811, -105.311104),
    "CT": (41.597782, -72.755371), "DE": (39.318523, -75.507141),
    "FL": (27.766279, -81.686783), "GA": (33.040619, -83.643074),
    "HI": (21.094318, -157.498337), "ID": (44.240459, -114.478828),
    "IL": (40.349457, -88.986137), "IN": (39.849426, -86.258278),
    "IA": (42.011539, -93.210526), "KS": (38.526600, -96.726486),
    "KY": (37.668140, -84.670067), "LA": (31.169546, -91.867805),
    "ME": (44.693947, -69.381927), "MD": (39.063946, -76.802101),
    "MA": (42.230171, -71.530106), "MI": (43.326618, -84.536095),
    "MN": (45.694454, -93.900192), "MS": (32.741646, -89.678696),
    "MO": (38.456085, -92.288368), "MT": (46.921925, -110.454353),
    "NE": (41.125370, -98.268082), "NV": (38.313515, -117.055374),
    "NH": (43.452492, -71.563896), "NJ": (40.298904, -74.521011),
    "NM": (34.840515, -106.248482), "NY": (42.165726, -74.948051),
    "NC": (35.630066, -79.806419), "ND": (47.528912, -99.784012),
    "OH": (40.388783, -82.764915), "OK": (35.565342, -96.928917),
    "OR": (44.572021, -122.070938), "PA": (40.590752, -77.209755),
    "RI": (41.680893, -71.511780), "SC": (33.856892, -80.945007),
    "SD": (44.299782, -99.438828), "TN": (35.747845, -86.692345),
    "TX": (31.054487, -97.563461), "UT": (40.150032, -111.862434),
    "VT": (44.045876, -72.710686), "VA": (37.769337, -78.169968),
    "WA": (47.400902, -121.490494), "WV": (38.491226, -80.954453),
    "WI": (44.268543, -89.616508), "WY": (42.755966, -107.302490),
    "DC": (38.907200, -77.036900)
}

STATE_NAME_TO_ABBR: Dict[str, str] = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY", "district of columbia": "DC"
}


def _find_geo_columns(df: pd.DataFrame) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    columns = list(df.columns)
    lower = {c.lower().strip(): c for c in columns}

    def pick(keyword: str) -> Optional[str]:
        preferred = [c for c in columns if "borrower" in c.lower() and keyword in c.lower()]
        if preferred:
            return preferred[0]
        for lc_name, original in lower.items():
            if keyword in lc_name:
                return original
        return None

    zip_col = pick("zip") or pick("postal")
    city_col = pick("city")
    state_col = pick("state")
    return zip_col, city_col, state_col


def _normalize_state_code(state_value: str) -> Optional[str]:
    if state_value is None:
        return None
    val = str(state_value).strip()
    if not val:
        return None
    if len(val) == 2 and val.isalpha():
        return val.upper()
    return STATE_NAME_TO_ABBR.get(val.lower())


def _borrower_geo_drop_filter(context: dict) -> list[str]:
    """Returns borrower geo source columns that should not be treated as categorical features."""
    data = context.get("data")
    if data is None or data.empty:
        return []

    geo_subset = get_stage_subset(context, entity="geographic", sub_filter="Borrower")
    if geo_subset is None or geo_subset.empty:
        geo_subset = data

    geo_like_cols = [
        c for c in geo_subset.columns
        if str(c).lower().strip() not in {"borrower_latitude", "borrower_longitude"}
    ]
    return list(dict.fromkeys(geo_like_cols))

def record_id_definition(context: dict, stage_cfg: dict) -> pd.DataFrame:
    """
    Establishes the universal anchor for the waterfall.
    If 'record_id' isn't in the data, it generates a sequence.
    The PipelineRunner detects this column and promotes it to the index.
    """
    data = context.get("data")
    if data is None:
        return pd.DataFrame()

    # If record_id already exists in the raw data, we use it; otherwise, create a sequence
    if 'record_id' not in data.columns:
        df_id = pd.DataFrame(index=data.index)
        df_id['record_id'] = range(len(data))
        return df_id
    
    return data[['record_id']]

def borrower_geo_coding(context: dict, stage_cfg: dict) -> pd.DataFrame:
    """
    Resolves borrower latitude/longitude using a strict fallback chain:
    ZIP -> CITY -> STATE centroid.
    """
    data = context.get("data")
    if data is None or data.empty:
        return pd.DataFrame(columns=["borrower_latitude", "borrower_longitude"])

    subset = get_stage_subset(context, entity="geographic", sub_filter="Borrower")
    geo_source = subset if not subset.empty else data
    zip_col, city_col, state_col = _find_geo_columns(geo_source)

    res = pd.DataFrame(index=data.index)
    res["borrower_latitude"] = np.nan
    res["borrower_longitude"] = np.nan

    country_code = str(context.get("config", {}).get("country_code", "us")).lower().strip()
    geocoder = pgeocode.Nominatim(country_code)

    if zip_col and zip_col in geo_source.columns:
        zip_digits = geo_source[zip_col].astype(str).str.extract(r"(\d{5})", expand=False)
        zip_idx = zip_digits.dropna().index
        if len(zip_idx) > 0:
            zip_lookup = geocoder.query_postal_code(zip_digits.loc[zip_idx].tolist())
            if isinstance(zip_lookup, pd.Series):
                zip_lookup = zip_lookup.to_frame().T
            if zip_lookup is not None and not zip_lookup.empty:
                lat_vals = zip_lookup["latitude"].to_numpy()
                lon_vals = zip_lookup["longitude"].to_numpy()
                res.loc[zip_idx, "borrower_latitude"] = lat_vals
                res.loc[zip_idx, "borrower_longitude"] = lon_vals

    city_cache: Dict[Tuple[str, Optional[str]], Tuple[float, float]] = {}
    unresolved = res[res["borrower_latitude"].isna()].index
    for idx in unresolved:
        city_value = str(geo_source.at[idx, city_col]).strip() if city_col and city_col in geo_source.columns else ""
        state_value = str(geo_source.at[idx, state_col]).strip() if state_col and state_col in geo_source.columns else ""
        state_code = _normalize_state_code(state_value)

        if city_value:
            cache_key = (city_value.lower(), state_code)
            if cache_key not in city_cache:
                safe_city_value = re.escape(city_value)
                try:
                    city_match = geocoder.query_location(safe_city_value)
                except Exception:
                    city_match = pd.DataFrame()

                if city_match is not None and not city_match.empty:
                    if state_code:
                        matching = city_match[city_match["state_code"].astype(str).str.upper() == state_code]
                        if not matching.empty:
                            city_match = matching
                    if not city_match.empty:
                        lat = city_match.iloc[0].get("latitude")
                        lon = city_match.iloc[0].get("longitude")
                        if pd.notna(lat) and pd.notna(lon):
                            city_cache[cache_key] = (float(lat), float(lon))

            if cache_key in city_cache:
                res.at[idx, "borrower_latitude"], res.at[idx, "borrower_longitude"] = city_cache[cache_key]
                continue

        if state_code and state_code in STATE_CENTROIDS:
            lat, lon = STATE_CENTROIDS[state_code]
            res.at[idx, "borrower_latitude"] = lat
            res.at[idx, "borrower_longitude"] = lon

    return res


def prepare_categorical_data(context: dict, stage_cfg: dict) -> pd.DataFrame:
    """
    Prepares categorical attributes as a standalone payload.
    This stage does not filter rows.
    """
    data = context.get("data")
    if data is None or data.empty:
        return pd.DataFrame()

    drop_filter = list(stage_cfg.get("drop_filter", []))
    drop_filter.extend(_borrower_geo_drop_filter(context))
    cat_subset = get_categorical_subset(context, drop_filter=drop_filter)
    if cat_subset.empty:
        cat_subset = pd.DataFrame(index=data.index)

    context["categorical_prepared"] = cat_subset.copy()
    return cat_subset


def prepare_numerical_data(context: dict, stage_cfg: dict) -> pd.DataFrame:
    """
    Prepares numeric attributes as a standalone payload.
    This stage does not filter rows.
    """
    data = context.get("data")
    if data is None or data.empty:
        return pd.DataFrame()

    drop_filter = {str(c).strip() for c in stage_cfg.get("drop_filter", [])}
    num_subset = data.select_dtypes(include=["number", "bool"]).copy()
    if drop_filter:
        keep_cols = [c for c in num_subset.columns if c not in drop_filter]
        num_subset = num_subset[keep_cols]

    context["numerical_prepared"] = num_subset.copy()
    return num_subset


def merge_categorical_and_numerical(context: dict, stage_cfg: dict) -> pd.DataFrame:
    """Merges categorical and numerical prepared payloads by record_id index."""
    data = context.get("data")
    if data is None or data.empty:
        return pd.DataFrame()

    cat_df = context.get("categorical_prepared")
    num_df = context.get("numerical_prepared")

    merged = merge_frames_by_index(
        left=cat_df,
        right=num_df,
        index=data.index,
        skip_existing_columns=True,
    )
    context["structured_base"] = merged.copy()
    return merged


def merge_with_borrower_geo(context: dict, stage_cfg: dict) -> pd.DataFrame:
    """Merges structured base with borrower geo encoding by record_id index."""
    data = context.get("data")
    if data is None or data.empty:
        return pd.DataFrame()

    base_df = context.get("structured_base")

    geo_cols = [
        c for c in ["borrower_latitude", "borrower_longitude"]
        if c in data.columns
    ]
    geo_df = data[geo_cols].copy() if geo_cols else pd.DataFrame(index=data.index)

    merged = merge_frames_by_index(
        left=base_df,
        right=geo_df,
        index=data.index,
        skip_existing_columns=True,
    )
    context["full_pre_filter_dataset"] = merged.copy()
    return merged

def low_count_featurization_of_cat_vars(context: dict, stage_cfg: dict) -> pd.DataFrame:
    """
    Two-pass low-count handling for categorical variables:
    1) Roll up rare levels into OTHERS.
    2) Sequentially drop rows when OTHERS support is below threshold.
    """
    data = context.get("data")
    if data is None or data.empty:
        return pd.DataFrame()

    drop_filter = list(stage_cfg.get("drop_filter", []))
    drop_filter.extend(_borrower_geo_drop_filter(context))
    cat_subset = get_categorical_subset(context, drop_filter=drop_filter)

    if cat_subset.empty:
        return pd.DataFrame(index=data.index, data={"placeholder_encoded": "n/a"})

    threshold = int(context.get("config", {}).get("MIN_SUPPORT_THRESHOLD_CAT_VARS", 5))

    rolled = cat_subset.copy()
    for col in rolled.columns:
        if rolled[col].dtype != object:
            rolled[col] = rolled[col].astype(object)
        counts = rolled[col].value_counts(dropna=False)
        rare_levels = counts[counts < threshold].index
        rare_mask = rolled[col].isin(rare_levels)
        rolled.loc[rare_mask, col] = "OTHERS"

    survivor_index = rolled.index
    triggered_attributes = []

    for col in rolled.columns:
        series = rolled.loc[survivor_index, col]
        others_mask = series == "OTHERS"
        others_count = int(others_mask.sum())

        if 0 < others_count < threshold:
            drop_idx = series[others_mask].index
            survivor_index = survivor_index.difference(drop_idx)
            triggered_attributes.append(col)

    if triggered_attributes:
        print(
            "   ⚠️ Low-support OTHERS triggered drops for: "
            + ", ".join(triggered_attributes)
            + f" (threshold={threshold})"
        )

    result = rolled.loc[survivor_index].copy()
    result.columns = [f"{c}_rcs" for c in result.columns]

    if result.empty:
        result = pd.DataFrame(index=survivor_index, data={"placeholder_rcs": "n/a"})

    return result

def loan_status_recoding(context: dict, stage_cfg: dict) -> pd.DataFrame:
    """
    Recodes the 'loanstatus' column into 'loan_status_r' based on specific rules.

    - Active loans: -1
    - Closed loans: 0
    - Distressed loans: 1

    Args:
        context: The execution context containing the 'data' DataFrame.
        stage_cfg: Configuration for the current stage (not directly used here but part of signature).

    Returns:
        pd.DataFrame: A DataFrame with 'record_id' as index and 'loan_status_r' as a column.
    """
    data = context.get("data")
    if data is None or data.empty:
        return pd.DataFrame(columns=["loan_status_r"])

    if 'loanstatus' not in data.columns:
        raise KeyError("Required column 'loanstatus' not found for loan status recoding.")

    recoded_status = pd.Series(index=data.index, dtype=float)
    status_text = data['loanstatus'].astype(str).str.upper().str.strip()

    active_pattern = r'ACTIVE|CURRENT|IN\s+DEFERMENT|DEFERMENT|CATCH[-\s]*UP'
    closed_pattern = (
        r'CLOSED|CANCELED|NOT\s+FUNDED|PAID\s+IN\s+FULL|PAID\s+IN\s+FULL\s*\(LIQ\)|'
        r'PREPAID\s+IN\s+FULL|ASSET\s+SALE|PURCH\(NOT\s*C/O\)'
    )
    distressed_pattern = (
        r'DISTRESSED|PAST\s*DUE|DELINQUENT|DEFAULT|CHARGED?[-\s]*OFF|'
        r'WRITEOFF|WRITE\s*OFF|NON[-\s]*PERFORMING'
    )

    recoded_status.loc[status_text.str.contains(active_pattern, regex=True, na=False)] = -1
    recoded_status.loc[status_text.str.contains(closed_pattern, regex=True, na=False)] = 0
    recoded_status.loc[status_text.str.contains(distressed_pattern, regex=True, na=False)] = 1

    unmatched_mask = data['loanstatus'].notna() & recoded_status.isna()
    if unmatched_mask.any():
        unexpected = sorted(data.loc[unmatched_mask, 'loanstatus'].astype(str).str.strip().unique().tolist())
        raise ValueError(f"Unexpected loanstatus values encountered: {unexpected[:10]}")

    result_df = pd.DataFrame(recoded_status, columns=['loan_status_r'])
    result_df.index.name = data.index.name
    return result_df


def hierarchical_low_count_var_encoding(context: dict, stage_cfg: dict) -> pd.DataFrame:
    """
    Hierarchical low-support recoding for NAICS-like codes.
    Low-support values are progressively right-masked until support is reached.
    """
    data = context.get("data")
    if data is None or data.empty:
        return pd.DataFrame(columns=["naicscode_rcs"])

    threshold = int(context.get("config", {}).get("MIN_SUPPORT_THRESHOLD_CAT_VARS", 5))
    source_col = stage_cfg.get("source_col", "naicscode")
    output_col = stage_cfg.get("output_col", "naicscode_rcs")
    mask_char = stage_cfg.get("mask_char", "*")

    if source_col not in data.columns:
        raise KeyError(f"Required column '{source_col}' not found for hierarchical low-count recoding.")

    recoded = hierarchical_recode_by_support_right(
        series=data[source_col],
        min_support=threshold,
        mask_char=mask_char,
        fallback_value="OTHERS",
    )

    return pd.DataFrame({output_col: recoded}, index=data.index)


def filter_modeling_universe(context: dict, stage_cfg: dict) -> pd.DataFrame:
    """Filters out active class from the modeling universe."""
    data = context.get("data")
    if data is None or data.empty:
        return pd.DataFrame()

    target_col = stage_cfg.get("target_col", "loan_status_r")
    drop_class = float(stage_cfg.get("drop_class", -1))

    # Preserve active rows for downstream scoring/reconciliation stages.
    context["active_holdout"] = data.loc[data[target_col] == drop_class].copy()

    filtered = filter_binary_universe(data, target_col=target_col, drop_class=drop_class)
    validate_binary_target(filtered, target_col=target_col, allowed=(0.0, 1.0))

    # Filtering stage returns index-only output so the runner updates survivors
    # without duplicating existing target columns in accumulated outputs.
    return pd.DataFrame(index=filtered.index)


def stratified_train_val_split(context: dict, stage_cfg: dict) -> pd.DataFrame:
    """Adds a train/validation split flag using stratified sampling on target."""
    data = context.get("data")
    if data is None or data.empty:
        return pd.DataFrame(columns=["dataset_split"])

    target_col = stage_cfg.get("target_col", "loan_status_r")
    split_col = stage_cfg.get("split_col", "dataset_split")
    random_state = int(stage_cfg.get("random_state", 42))
    val_size = float(context.get("config", {}).get("VALIDATION_SIZE", 0.2))

    split_df = assign_train_val_split(
        data=data,
        target_col=target_col,
        val_size=val_size,
        random_state=random_state,
        split_col=split_col,
    )
    return split_df


def target_encode_categorical_vars(context: dict, stage_cfg: dict) -> pd.DataFrame:
    """Fits TargetEncoder on train rows and transforms train/val categoricals."""
    data = context.get("data")
    if data is None or data.empty:
        return pd.DataFrame()

    target_col = stage_cfg.get("target_col", "loan_status_r")
    split_col = stage_cfg.get("split_col", "dataset_split")
    output_suffix = stage_cfg.get("output_suffix", "_te")

    if target_col not in data.columns:
        raise KeyError(f"Required target column '{target_col}' not found before target encoding.")
    if split_col not in data.columns:
        raise KeyError(f"Required split column '{split_col}' not found before target encoding.")

    train_df = data[data[split_col] == "train"]
    if train_df.empty:
        raise ValueError("Train split is empty; cannot fit target encoder.")

    exclude_cols = list(stage_cfg.get("exclude_cols", []))
    exclude_cols.extend(list(stage_cfg.get("drop_filter", [])))
    exclude_name_patterns = list(stage_cfg.get("exclude_name_patterns", []))
    exclude_cols.extend(_borrower_geo_drop_filter(context))
    if not exclude_cols and not exclude_name_patterns:
        raise ValueError(
            "Target encoding requires an explicit exclusion policy. "
            "Set 'exclude_cols' and/or 'exclude_name_patterns' in stage config."
        )
    for required_exclude in [target_col, split_col]:
        if required_exclude not in exclude_cols:
            exclude_cols.append(required_exclude)

    cat_cols = select_categorical_columns(
        data,
        exclude_cols=exclude_cols,
        exclude_name_patterns=exclude_name_patterns,
    )

    # If a rarity-encoded categorical exists (e.g., x_rcs), skip encoding its raw base (x).
    rcs_bases = {c[:-4] for c in cat_cols if c.endswith("_rcs")}
    if rcs_bases:
        cat_cols = [c for c in cat_cols if c not in rcs_bases]

    if not cat_cols:
        return pd.DataFrame(index=data.index)

    encoder = fit_target_encoder(train_df=train_df, y_col=target_col, cat_cols=cat_cols)
    context["target_encoder"] = encoder
    context["target_encoder_cols"] = cat_cols

    encoded_df = transform_with_encoder(data, encoder, cat_cols=cat_cols, suffix=output_suffix)

    active_holdout = context.get("active_holdout")
    if active_holdout is not None and not active_holdout.empty:
        context["active_encoded"] = transform_with_encoder(
            active_holdout,
            encoder,
            cat_cols=cat_cols,
            suffix=output_suffix,
        )

    return encoded_df


def harmonize_and_project_feature_space(context: dict, stage_cfg: dict) -> pd.DataFrame:
    """
    Learns a feature subset from train partition and projects modeled + active
    data into a canonical feature space for downstream merge and scoring.
    """
    data = context.get("data")
    if data is None or data.empty:
        return pd.DataFrame()

    target_col = stage_cfg.get("target_col", "loan_status_r")
    split_col = stage_cfg.get("split_col", "dataset_split")
    partition_col = stage_cfg.get("output_partition_col", "dataset_partition")
    min_unique = int(stage_cfg.get("min_unique", 2))
    exclude_candidate_name_patterns = list(stage_cfg.get("exclude_candidate_name_patterns", []))
    exclude_candidate_cols = set(stage_cfg.get("exclude_candidate_cols", []))
    if not exclude_candidate_cols and not exclude_candidate_name_patterns:
        raise ValueError(
            "Feature-space harmonization requires an explicit candidate exclusion policy. "
            "Set 'exclude_candidate_cols' and/or 'exclude_candidate_name_patterns' in stage config."
        )
    resolver = context.get("resolver")
    if resolver is None:
        raise ValueError("PathCoordinator resolver missing from context.")
    min_non_null_rate = float(resolver.feature_selection_min_non_null_rate)

    train_df = data.loc[data[split_col] == "train"]
    if train_df.empty:
        raise ValueError("Train split is empty; cannot perform feature selection.")

    candidate_cols = [
        c for c in data.columns
        if c.endswith("_te") or c.endswith("_rcs") or pd.api.types.is_numeric_dtype(data[c])
    ]
    if exclude_candidate_cols:
        candidate_cols = [c for c in candidate_cols if c not in exclude_candidate_cols]
    for reserved in [target_col]:
        if reserved in candidate_cols:
            candidate_cols.remove(reserved)

    selected_features = select_model_features(
        train_df=train_df,
        candidate_cols=candidate_cols,
        target_col=target_col,
        min_non_null_rate=min_non_null_rate,
        min_unique=min_unique,
        method=resolver.feature_selection_method,
        top_k=resolver.feature_selection_top_k,
        importance_floor=resolver.feature_selection_importance_floor,
        tree_model=resolver.feature_selection_tree_model,
        tree_n_estimators=resolver.feature_selection_tree_n_estimators,
        tree_learning_rate=resolver.feature_selection_tree_learning_rate,
        tree_max_depth=resolver.feature_selection_tree_max_depth,
        tree_subsample=resolver.feature_selection_tree_subsample,
        tree_random_state=resolver.feature_selection_tree_random_state,
        exclude_candidate_name_patterns=exclude_candidate_name_patterns,
        top_k_mode=resolver.feature_selection_top_k_mode,
        top_k_min=resolver.feature_selection_top_k_min,
        top_k_min_ratio=resolver.feature_selection_top_k_min_ratio,
        top_k_max=resolver.feature_selection_top_k_max,
        target_feature_count=resolver.feature_selection_target_feature_count,
        kneedle_sensitivity=resolver.feature_selection_kneedle_sensitivity,
        kneedle_curve=resolver.feature_selection_kneedle_curve,
        kneedle_direction=resolver.feature_selection_kneedle_direction,
        require_kneedle=resolver.feature_selection_require_kneedle,
        diagnostics_out=context.setdefault("feature_selection_diagnostics", {}),
    )
    if not selected_features:
        raise ValueError("No features selected for model space projection.")

    context["selected_features"] = selected_features

    diagnostics = context.get("feature_selection_diagnostics", {})
    importance_series = diagnostics.get("importance_series")
    selected_k = diagnostics.get("selected_k", len(selected_features))
    print(
        "   📊 Feature selection summary: "
        f"candidates={len(candidate_cols)}, selected={len(selected_features)}, "
        f"k={int(selected_k)}, mode={diagnostics.get('top_k_mode', 'unknown')}"
    )
    if importance_series is not None and len(importance_series) > 0:
        knee_curve_file = stage_cfg.get("knee_curve_file", "feature_selection_knee_curve.png")
        knee_curve_path = os.path.join(os.path.dirname(resolver.featurized_dataset_path), knee_curve_file)
        plot_feature_selection_knee_curve(
            importance_series=importance_series,
            selected_k=int(selected_k),
            output_path=knee_curve_path,
            title="SBA Feature Importance Knee Curve",
        )
        context["feature_selection_knee_curve_path"] = knee_curve_path
        print(f"   🖼️ Knee curve saved: {knee_curve_path}")

    modeled_features = project_feature_space(data, selected_features, fill_value=0.0)
    modeled_features[target_col] = data[target_col]
    modeled_features[split_col] = data[split_col]
    modeled_features[partition_col] = "modeled"
    context["modeled_projected"] = modeled_features

    active_holdout = context.get("active_holdout")
    active_encoded = context.get("active_encoded")
    if active_holdout is not None and not active_holdout.empty:
        active_base = active_holdout.copy()
        active_features = project_feature_space(active_base, selected_features, fill_value=0.0)
        if active_encoded is not None and not active_encoded.empty:
            for col in active_encoded.columns:
                if col in active_features.columns:
                    active_features[col] = active_encoded[col]
        active_features[target_col] = active_base.get(target_col, pd.Series(index=active_base.index))
        active_features[split_col] = "active"
        active_features[partition_col] = "active"
        context["active_projected"] = active_features
    else:
        context["active_projected"] = pd.DataFrame(columns=modeled_features.columns)

    return modeled_features


def merge_modeled_and_active_partitions(context: dict, stage_cfg: dict) -> pd.DataFrame:
    """Merges projected modeled partition with active partition into one aligned dataset."""
    modeled = context.get("modeled_projected")
    active = context.get("active_projected")

    if modeled is None or modeled.empty:
        return pd.DataFrame()
    if active is None:
        active = pd.DataFrame(columns=modeled.columns)

    all_cols = list(modeled.columns)
    for c in active.columns:
        if c not in all_cols:
            all_cols.append(c)

    modeled = modeled.reindex(columns=all_cols)
    active = active.reindex(columns=all_cols)
    merged = pd.concat([modeled, active], axis=0)
    merged = merged.sort_index(ascending=True)
    return merged