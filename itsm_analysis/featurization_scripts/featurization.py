import os
import pandas as pd


def ticket_survival_summary(context: dict, stage_cfg: dict) -> pd.DataFrame:
    """Build a survival-ready dataset for ticket resolution time analysis."""
    data: pd.DataFrame = context["data"].copy()

    if "number" in data.columns:
        data["subject_id"] = data["number"]

    if "subject_id" not in data.columns:
        raise KeyError("Expected 'number' or 'subject_id' column in the input data.")

    for required in ["assignment_group", "opened_at", "closed_at"]:
        if required not in data.columns:
            raise KeyError(f"Expected '{required}' column in the input data.")

    for col in ["opened_at", "closed_at", "resolved_at"]:
        if col in data.columns:
            data[col] = pd.to_datetime(data[col], errors="coerce")

    data["assignment_group"] = data["assignment_group"].fillna("?").astype(str)
    data = data.loc[data["assignment_group"] != "?"].copy()

    timestamp_cols = [c for c in ["opened_at", "closed_at", "resolved_at"] if c in data.columns]
    observation_end = data[timestamp_cols].max().max()
    observation_start = observation_end - pd.Timedelta(days=365)

    data = data.loc[
        (data["opened_at"] > observation_start)
        & (data["opened_at"] <= observation_end)
    ].copy()

    data["_final_sort_time"] = data[["opened_at", "closed_at", "resolved_at"]].max(axis=1)
    data = data.sort_values(
        ["subject_id", "_final_sort_time", "opened_at"],
        ascending=[True, False, False],
    )
    final_idx = data.groupby("subject_id", sort=False).head(1).index
    final = data.loc[final_idx].copy()
    final = final.drop(columns=["_final_sort_time"], errors="ignore")

    final["survival_event"] = (
        final["incident_state"].fillna("").astype(str).str.lower().isin(
            {"closed", "resolved"}
        )
    ).astype(int)

    final["survival_duration_days"] = (
        final["closed_at"] - final["opened_at"]
    ).dt.total_seconds() / 86400.0

    censored_mask = final["survival_event"] == 0
    if censored_mask.any():
        final.loc[censored_mask, "survival_duration_days"] = (
            observation_end - final.loc[censored_mask, "opened_at"]
        ).dt.total_seconds() / 86400.0

    final["duration_days"] = final["survival_duration_days"]

    resolver = context.get("resolver")
    if resolver is None:
        raise KeyError("Pipeline context must include 'resolver' for output path resolution.")

    raw_dir = os.path.join(
        resolver.working_dir,
        "data",
        resolver.config.get("dd_cleaner_output_dir", "dd_cleaner"),
    )
    os.makedirs(raw_dir, exist_ok=True)
    raw_file = resolver.config.get("survival_event_data_file", "itsm_ticket_survival_dataset.csv")
    raw_path = os.path.join(raw_dir, raw_file)

    raw_columns = [
        "subject_id",
        "assignment_group",
        "incident_state",
        "opened_at",
        "closed_at",
        "survival_event",
        "duration_days",
    ]
    if "number" in final.columns:
        raw_columns.insert(0, "number")

    final.loc[:, [c for c in raw_columns if c in final.columns]].to_csv(raw_path, index=False)
    print(f"Wrote raw event survival dataset ({len(final)} rows) to: {raw_path}")

    threshold = int(resolver.config.get("MIN_EVENT_COUNT_THRESHOLD", 20))
    group_stats = final.groupby("assignment_group").agg(
        total=("subject_id", "size"),
        closed=("survival_event", "sum"),
    )
    group_stats["open"] = group_stats["total"] - group_stats["closed"]
    group_stats["open_pct"] = group_stats["open"] / group_stats["total"]
    eligible_groups = group_stats.loc[
        (group_stats["closed"] >= threshold) & (group_stats["open_pct"] <= 0.70)
    ].index.tolist()
    print(f"Groups with >= {threshold} closed tickets: {len(group_stats[group_stats['closed'] >= threshold])}")
    print(f"Groups passing censoring guard (open_pct <= 0.70): {len(eligible_groups)}")

    final = final.loc[final["assignment_group"].isin(eligible_groups)].copy()

    km_pr_dir = os.path.join(
        resolver.working_dir,
        "data",
        resolver.config.get("featurization_output_dir", "featurization"),
    )
    os.makedirs(km_pr_dir, exist_ok=True)

    km_file = resolver.config.get("itsm_KM_data_file", "itsm_KM_data.csv")
    pr_file = resolver.config.get("itsm_PR_data_file", "itsm_PR_data.csv")

    km_groups = group_stats[group_stats["closed"] >= threshold].index.tolist()
    pr_groups = group_stats[group_stats["closed"] < threshold].index.tolist()

    km_df = final[final["assignment_group"].isin(km_groups)].copy()
    pr_df = final[final["assignment_group"].isin(pr_groups)].copy()

    km_path = os.path.join(km_pr_dir, km_file)
    pr_path = os.path.join(km_pr_dir, pr_file)
    km_df.to_csv(km_path, index=False)
    pr_df.to_csv(pr_path, index=False)

    print(f"Wrote Kaplan-Meier data ({len(km_df)} rows, {len(km_groups)} groups) to: {km_path}")
    print(f"Wrote parametric regression data ({len(pr_df)} rows, {len(pr_groups)} groups) to: {pr_path}")

    return final
