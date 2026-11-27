## Overview

This document summarizes the Olist unsupervised migration use case for the current KMDS session. It describes how the dataset was prepared, how `dd_parser_cleaner` was applied, and how the featurization pipeline was constructed for a São Paulo 2017 subset.

## Initialization

The workspace was already initialized with the KMDS directory layout and a working `config.yaml` in the repo root.

Expected directories used in this session:

- `data/`
- `data_dictionary/`
- `documents/`
- `notebooks/`
- `data/dd_cleaner/`

## The Dataset

The primary driver for this migration workflow is the Olist orders dataset. The pipeline is built around orders, with order items joined for transactional detail and customers used for metadata enrichment and a separate cleanup workstream.

For this unsupervised use case:

- `olist_orders_dataset_raw.csv` is the main driver of the pipeline and the core dataset for feature preparation.
- `olist_order_items_dataset_raw.csv` is joined to orders at the order-item level to support order-level feature assembly.
- `olist_customers_dataset.csv` is used for customer metadata and a separate customer cleaner workstream.

## Workflow Summary

### 1. Featurization pipeline setup

A config-driven featurization pipeline was created in `featurizer_config.yaml`.
The pipeline defines these stages:

1. `load_raw_data` — load orders, order items, and customers.
2. `build_order_level_dataset` — merge the raw tables into a prepared order-level dataset.
3. `derive_sp_2017_subset` — filter orders to São Paulo, 2017.
4. `build_sp_weekly_product_matrix` — create weekly revenue and product pivot artifacts.

The output files are written to `data/`:

- `olist_daily_orders_prepared.csv`
- `SP_2017_orders_filtered_prepared.csv`
- `SP_2017_weekly_revenue_prepared.csv`
- `SP_2017_freq_prod_weekly_sales_prepared.csv`
- `SP_2017_freq_prod_weekly_sales_prepared.parquet`

### 2. Customer metadata and cleaning workstream

A dedicated customer config file was added: `customer_config.yaml`.
A customer-specific data dictionary was created at `data_dictionary/customer_data_dictionary.csv`.

This allowed a separate `dd_parser_cleaner` run for the customer dataset, isolated from the orders workflow.

### 3. Parser and Cleaner commands

The customer workflow executed successfully with:

- `classify-entities --config customer_config.yaml`
- `clean-dataset --config customer_config.yaml --action full`

This produced a customer clean output file:

- `data/dd_cleaner/olist_customers_dataset_clean.csv`

and customer profiling artifacts:

- `documents/dd_cleaner/olist_customers_dataset_profiling_report.md`
- `documents/dd_cleaner/olist_customers_dataset_profiling_report.json`

The customer handshake file was configured as:

- `customer_parser_cleaner_handshake.md`

### 4. Reports and recommendations

The customer cleaner run performed the diagnostic suite but did not produce customer-specific cleaning actions beyond asserting column health.

Existing shared recommendation artifacts from the orders workflow remain present in `documents/dd_cleaner/cleaning_recommendations.md` and `documents/dd_cleaner/cleaning_matrix_actions_only.csv`, but the new customer run did not add separate actions to those files.

### 5. Geometry-aware feature analysis

The weekly product matrix is passed to `cluster-geometry-profiler` from
[`cluster_feature_analysis`](https://github.com/rajivsam/cluster_feature_analysis).
The profiler audits 9,367 candidate product columns, retains 870, and records
all 8,497 removals by screening gate and rationale.

The retained 52-by-870 matrix has four persisted week clusters with sizes
17, 18, 9, and 8. Current outputs are:

- `data/SP_2017_cluster_feature_report.json`
- `data/SP_2017_dropped_features.csv`
- `data/SP_2017_filtered_original_features.csv`

Product IDs in the retained matrix are model features; they are not members
of four product clusters. Earlier `models/` co-clustering files should be
treated as historical artifacts from the unpruned representation.

## Working with What `dd_parser_cleaner` Generates

### Handshake document

The new customer handshake file is:

- `documents/dd_cleaner/customer_parser_cleaner_handshake.md`

It is the main schema verification artifact for customer metadata, and it captures:

- inferred dataset type (`cross-sectional`)
- entity assignment for customer and geographic fields
- attribute coverage and matching between dictionary and raw input

### Cleaner outputs

The cleaner generated:

- `data/dd_cleaner/olist_customers_dataset_clean.csv`
- `documents/dd_cleaner/olist_customers_dataset_profiling_report.md`
- `documents/dd_cleaner/olist_customers_dataset_profiling_report.json`

These are the customer-specific cleaned dataset and quality profile.

### Featurization

Featurization was added to the workflow summary as a downstream step.
The unsupervised use case currently supports:

- preparing order-level features from joined orders + order items + customers
- filtering by São Paulo 2017
- exporting weekly product and revenue matrices for unsupervised or graph-based analysis

The featurization pipeline is driven by `featurizer_config.yaml`, so the feature preparation contract is explicit and repeatable.

## Exit Criteria

For this session, the migration activity is complete when:

- the customer-specific parser/cleaner workflow is isolated with `customer_config.yaml`
- the customer data dictionary is present at `data_dictionary/customer_data_dictionary.csv`
- the customer handshake artifact is `customer_parser_cleaner_handshake.md`
- the customer cleaned output exists at `data/dd_cleaner/olist_customers_dataset_clean.csv`
- the orders-driven featurization pipeline is configured and produces the expected SP 2017 artifacts
- the profiler output accounts for all 9,367 candidate product features
- the current documentation consistently reports 870 retained features

## Notes

- `orders` remains the main pipeline driver.
- `order_items` is treated as a stable join input and not cleaned separately in this session.
- `customers` is handled via a separate customer cleaner workstream.
- Featurization is explicitly supported in the migration workflow to connect cleaned data to analysis-ready features.
- Feature screening, geometry diagnosis, clustering, and feature profiling are separate auditable stages.
