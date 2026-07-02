# Olist Featurization Pipeline

This document describes the Olist featurization pipeline for the SP 2017 clustering dataset. The pipeline is intentionally focused on raw-to-prepared feature generation, not model training.

## Pipeline intent

The goal is to build the exact dataset required by the final spectral coclustering notebook: a clean SP 2017 order-level dataset and a product-week sales matrix.

## PathCoordinator and configuration

The pipeline uses `featurizer_config.yaml` to centralize paths, raw file names, and output artifacts. The implementation now uses the KMDS `dd_cleaner.notebook_utils` `PathCoordinator` contract instead of hardcoded file paths. That means the pipeline resolves all input files through the KMDS workspace configuration and loads the cleaned orders dataset directly from the cleaner output when available.

The current workflow is:
- `classify-entities` and `clean-dataset --config config.yaml --action full` run for orders and customers data to generate the cleaned authority dataset.
- `olist_order_items_dataset_raw.csv` remains a simple raw join input and does not require cleaning.
- `featurization_scripts/featurization.py` now uses the `PathCoordinator` interface to load the cleaned dataset from `data/dd_cleaner/olist_daily_orders_prepared_clean.csv` when present, and falls back to raw input only if needed.

## Stage contract

Each stage follows the contract: `method(context, stage_cfg) -> DataFrame`.
- `context` holds the resolved paths and the current working dataset.
- `stage_cfg` is the stage dictionary from the config pipeline list.

## Stages

1. `load_raw_data`
   - Loads `olist_orders_dataset_raw.csv`, `olist_order_items_dataset_raw.csv`, and `olist_customers_dataset_raw.csv`.
   - Merges orders and order items.
   - Adds customer geography from the customers table.

2. `build_order_level_dataset`
   - Ensures timestamp parsing.
   - Produces `olist_daily_orders_prepared.csv`.

3. `derive_sp_2017_subset`
   - Adds `year`, `month`, and `woy` fields.
   - Filters to `customer_state == 'SP'` and `year == 2017`.
   - Produces `SP_2017_orders_filtered_prepared.csv`.

4. `build_sp_weekly_product_matrix`
   - Aggregates weekly revenue into `SP_2017_weekly_revenue_prepared.csv`.
   - Builds the product-week matrix and saves both CSV and parquet artifacts.

## Feature advisor results

The feature advisor service was executed using rule-based recommendations for a graph-modeling intent. The generated recommendations are available under `data/data/feature_advisor/feature_advisor_recommendations.md`.

The advisor output for this dataset suggests:
- `low_count_cat_var_encoding + target_encoding` for categorical fields such as `order_id`, `customer_id`, `order_purchase_timestamp`, `product_id`, `customer_city`, and `customer_state`.
- `No encoding required` for numeric fields such as `order_item_id`, `price`, `customer_zip_code_prefix`, `freq_cust`, and `freq_purch_prod`.
- `Review metadata` for time-derived fields `year`, `month`, and `woy`, since they do not fit a standard categorical/numeric/text featurization pattern in the advisor rules.

These recommendations were generated from the feature advisor service with `model_intent='graph'` and the current metadata table.

## Unsupervised graph model decision

This pipeline is designed for an unsupervised, graph-based analysis rather than a supervised prediction model. That means:
- The focus is on building the node/edge-level data representation needed for the spectral coclustering workflow.
- No explicit feature selection stage is performed in this iteration.
- The final representation is the product-week revenue matrix used by the SP 2017 spectral coclustering notebook.

Given the unsupervised nature, we do not apply a train/validation feature selection step. Instead, the emphasis is on preserving the raw graph structure and the prepared weekly product matrix that feeds the clustering algorithm.

## Output artifacts

- `data/olist_daily_orders_prepared.csv`
- `data/SP_2017_orders_filtered_prepared.csv`
- `data/SP_2017_weekly_revenue_prepared.csv`
- `data/SP_2017_freq_prod_weekly_sales_prepared.csv`
- `data/SP_2017_freq_prod_weekly_sales_prepared.parquet`

## Usage

Run the pipeline via the notebook or by executing:

```bash
python featurization_scripts/featurization.py
```

This pipeline is designed to support the final clustering notebook without adding any modeling logic.
