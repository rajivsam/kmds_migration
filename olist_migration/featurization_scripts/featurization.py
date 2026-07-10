from pathlib import Path
import pandas as pd
import yaml


class FeaturizationPathCoordinator:
    def __init__(self, config):
        self.config = config
        self.working_dir = Path(config["working_dir"])
        self.output_dir = self.working_dir / config.get("featurization_output_dir", "data")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def merged_raw_path(self):
        return self.working_dir / self.config["merged_raw_file"]

    @property
    def clean_dataset_output_path(self):
        return self.working_dir / self.config.get("dd_cleaner_output_dir", "data/dd_cleaner") / self.config.get("clean_output_filename", "olist_daily_orders_prepared_clean.csv")

    @property
    def featurization_input_path(self):
        return self.working_dir / self.config.get("featurization_input_data", self.config.get("merged_raw_file", ""))

    @property
    def metadata_table_path(self):
        return self.working_dir / self.config["metadata_file"]

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
    if coord.featurization_input_path.exists():
        print(f"Loading featurization input dataset from {coord.featurization_input_path}")
        df = pd.read_csv(coord.featurization_input_path, parse_dates=["order_purchase_timestamp"], low_memory=False)
        df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
        context.df = df
        return df

    if coord.merged_raw_path.exists():
        print(f"Loading merged raw dataset from {coord.merged_raw_path}")
        df = pd.read_csv(coord.merged_raw_path, parse_dates=["order_purchase_timestamp"], low_memory=False)
        df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
        context.df = df
        return df

    if coord.clean_dataset_output_path.exists():
        print(f"Loading cleaned dataset from {coord.clean_dataset_output_path}")
        df = pd.read_csv(coord.clean_dataset_output_path, parse_dates=["order_purchase_timestamp"], low_memory=False)
        df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
        context.df = df
        return df

    raise FileNotFoundError(
        f"Neither featurization input dataset, merged raw dataset, nor cleaned dataset could be found."
        f" Expected input file at {coord.featurization_input_path}, merged raw file at {coord.merged_raw_path}, or cleaned file at {coord.clean_dataset_output_path}."
    )


def validate_required_columns(context, stage_cfg=None):
    df = context.df.copy() if context.df is not None else load_raw_data(context)
    required_columns = ["order_item_id", "price", "product_id", "order_purchase_timestamp", "customer_state"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns for featurization: {missing_columns}")

    mask = df["order_item_id"].notna() & df["price"].notna()
    dropped = len(df) - int(mask.sum())
    if dropped > 0:
        print(f"Dropped {dropped} rows missing order_item_id or price")
    df = df[mask].copy()
    context.df = df
    return df


def build_sp_weekly_product_matrix(context, stage_cfg=None):
    df = context.df.copy() if context.df is not None else load_raw_data(context)
    df["order_purchase_timestamp"] = df["order_purchase_timestamp"].dt.to_period("D").dt.to_timestamp()
    df["year"] = df["order_purchase_timestamp"].dt.year
    df["woy"] = df["order_purchase_timestamp"].dt.isocalendar().week
    df_sp = df[(df["customer_state"] == "SP") & (df["year"] == 2017)].reset_index(drop=True)
    df_freq_prod = df_sp.pivot_table(
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
