from pathlib import Path
import pandas as pd
import yaml

from dd_cleaner.notebook_utils import (
    PathCoordinator as CleanerPathCoordinator,
    get_cleaned_data,
    get_raw_data,
)


class FeaturizationPathCoordinator:
    def __init__(self, config):
        self.config = config
        self.working_dir = Path(config["working_dir"])
        self.cleaner_coord = CleanerPathCoordinator(working_dir=self.working_dir)
        self.output_dir = self.working_dir / config.get("featurization_output_dir", "data")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def raw_dataset_path(self):
        return self.cleaner_coord.raw_dataset_path

    @property
    def clean_dataset_output_path(self):
        return self.cleaner_coord.clean_dataset_output_path

    @property
    def metadata_table_path(self):
        return self.cleaner_coord.metadata_table_path

    @property
    def featurized_path(self):
        return self.output_dir / self.config["featurized_data_file"]

    @property
    def sp_subset_path(self):
        return self.output_dir / self.config["sp_subset_file"]

    @property
    def sp_weekly_revenue_path(self):
        return self.output_dir / self.config["sp_weekly_revenue_file"]

    @property
    def sp_freq_prod_path(self):
        return self.output_dir / self.config["sp_freq_prod_file"]

    @property
    def sp_freq_prod_parquet(self):
        return self.output_dir / self.config["sp_freq_prod_parquet"]


class SimpleContext:
    def __init__(self, config, coordinator):
        self.config = config
        self.coord = coordinator
        self.df = None


def load_config(config_path: Path):
    with config_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_raw_data(context, stage_cfg=None):
    coord = context.coord
    if coord.clean_dataset_output_path.exists():
        print(f"Loading cleaned dataset via notebook utils from {coord.clean_dataset_output_path}")
        context.df = get_cleaned_data(coord.cleaner_coord)
        context.df["order_purchase_timestamp"] = pd.to_datetime(context.df["order_purchase_timestamp"])
        return context.df

    if coord.raw_dataset_path.exists():
        print(f"Loading raw dataset via notebook utils from {coord.raw_dataset_path}")
        context.df = get_raw_data(coord.cleaner_coord)
        context.df["order_purchase_timestamp"] = pd.to_datetime(context.df["order_purchase_timestamp"])
        return context.df

    raise FileNotFoundError(
        f"Neither cleaned nor raw input dataset could be found."
        f" Expected cleaned file at {coord.clean_dataset_output_path} or raw file at {coord.raw_dataset_path}."
    )


def build_order_level_dataset(context, stage_cfg=None):
    df = context.df.copy() if context.df is not None else load_raw_data(context)
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    context.df = df
    context.df.to_csv(context.coord.featurized_path, index=False)
    return context.df


def derive_sp_2017_subset(context, stage_cfg=None):
    df = context.df.copy()
    df["year"] = df["order_purchase_timestamp"].dt.year
    df["month"] = df["order_purchase_timestamp"].dt.month
    df["woy"] = df["order_purchase_timestamp"].dt.isocalendar().week
    df_sp = df[(df["customer_state"] == "SP") & (df["year"] == 2017)].reset_index(drop=True)
    df_sp.to_csv(context.coord.sp_subset_path, index=False)
    context.df = df_sp
    return df_sp


def build_sp_weekly_product_matrix(context, stage_cfg=None):
    df = context.df.copy()
    df_weekly_revenue = df.groupby(["year", "woy"], observed=True)["price"].sum().reset_index()
    df_weekly_revenue.columns = ["year", "woy", "weekly_revenue"]
    df_weekly_revenue.to_csv(context.coord.sp_weekly_revenue_path, index=False)
    df_freq_prod = df.pivot_table(
        index="woy",
        columns="product_id",
        values="price",
        aggfunc="sum",
        fill_value=0
    ).reset_index()
    df_freq_prod.to_csv(context.coord.sp_freq_prod_path, index=False)
    df_freq_prod.to_parquet(context.coord.sp_freq_prod_parquet, index=False)
    return df_freq_prod


def run_pipeline(config_path: Path):
    config = load_config(config_path)
    coord = FeaturizationPathCoordinator(config)
    context = SimpleContext(config, coord)
    for stage_cfg in config.get("pipeline", []):
        method = globals()[stage_cfg["method"]]
        print(f"Running stage: {stage_cfg['name']}")
        method(context, stage_cfg)
    return context


if __name__ == "__main__":
    config_path = Path(__file__).resolve().parent.parent / "featurizer_config.yaml"
    run_pipeline(config_path)
