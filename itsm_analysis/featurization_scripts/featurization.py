import os
import pandas as pd


def ticket_survival_summary(context: dict, stage_cfg: dict) -> pd.DataFrame:
    """Build a survival-ready dataset for ticket resolution time analysis."""
    data: pd.DataFrame = context["data"].copy()

    # Normalize timestamps
    for col in ["opened_at", "closed_at"]:
        if col in data.columns:
            data[col] = pd.to_datetime(data[col], errors="coerce")

    # Use ticket number as subject identifier.
    data = data.rename(columns={"number": "subject_id"})
    if "subject_id" not in data.columns:
        raise KeyError("Expected 'number' or 'subject_id' column in the input data.")

    # Event definition: Closed is the event of interest; all other states are censored.
    closed_states = {"closed"}
    data["survival_event"] = (
        data["incident_state"].fillna("").astype(str).str.lower().isin(closed_states)
    ).astype(int)

    # Compute duration in days from opened_at to closed_at.
    data["survival_duration_days"] = (
        data["closed_at"] - data["opened_at"]
    ).dt.total_seconds() / 86400.0

    # Observation cutoff: one year back from the last closed_at timestamp.
    observation_end = data["closed_at"].max() if data["closed_at"].notna().any() else data["opened_at"].max()
    observation_start = observation_end - pd.Timedelta(days=365)
    data = data[data["opened_at"] >= observation_start].copy()

    # Select the final row for each ticket subject by the latest closed_at timestamp.
    last_idx = (
        data.sort_values(["subject_id", "closed_at"], ascending=[True, True])
        .groupby("subject_id", sort=False)
        .tail(1)
        .index
    )
    final = data.loc[last_idx, ["subject_id", "assignment_group", "survival_event", "survival_duration_days"]].copy()

    # Split the data by assignment_group event count for Kaplan-Meier vs parametric regression.
    resolver = context.get("resolver")
    if resolver is None:
        raise KeyError("Pipeline context must include 'resolver' for output path resolution.")

    output_dir = os.path.join(
        resolver.working_dir,
        "data",
        resolver.config.get("featurization_output_dir", "featurization"),
    )
    os.makedirs(output_dir, exist_ok=True)

    threshold = int(resolver.config.get("MIN_EVENT_COUNT_THRESHOLD", 20))
    km_file = resolver.config.get("itsm_KM_data_file", "itsm_KM_data.csv")
    pr_file = resolver.config.get("itsm_PR_data_file", "itsm_PR_data.csv")

    group_counts = final.groupby("assignment_group").size()
    km_groups = group_counts[group_counts > threshold].index.tolist()
    pr_groups = group_counts[group_counts <= threshold].index.tolist()

    km_df = final[final["assignment_group"].isin(km_groups)].copy()
    pr_df = final[final["assignment_group"].isin(pr_groups)].copy()

    km_path = os.path.join(output_dir, km_file)
    pr_path = os.path.join(output_dir, pr_file)
    km_df.to_csv(km_path, index=False)
    pr_df.to_csv(pr_path, index=False)

    print(
        f"Wrote Kaplan-Meier data ({len(km_df)} rows, {len(km_groups)} groups) to: {km_path}"
    )
    print(
        f"Wrote parametric regression data ({len(pr_df)} rows, {len(pr_groups)} groups) to: {pr_path}"
    )

    return final
