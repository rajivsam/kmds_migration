# Olist KMDS Migration Workspace

This workspace is the second instantiation of a real dataset modeled with KMDS tools. It demonstrates KMDS-driven cleaning, featurization, and spectral clustering using the Olist SP 2017 retail dataset.

## What this project illustrates

- Real dataset ingestion from raw Olist CSV exports
- Entity parsing, dataset cleaning, and quarantine handling
- Longitudinal feature engineering for weekly product affinity
- Spectral clustering and cluster advisor profiling
- KMDS helper artifact generation and knowledge graph integration
- Pre-clustering geometry auditing with `cluster-geometry-profiler` to separate true cluster structure from sparse or redundant product columns

The analytics narrative is centered on a simple principle: validation informs modeling. Before any cluster assignment is interpreted, the raw 52 x 9,367 product-week matrix is screened for sparsity, zero-spread features, and high Spearman redundancy. Only after that geometry audit do we choose and apply the clustering method that is consistent with the data’s structure. The profiler then reports structural diagnostics such as condition number, local intrinsic dimension, participation ratio, and feature-level cluster separation so the narrative clearly distinguishes data hygiene, method selection, and downstream cluster interpretation.

## Key files

- `config.yaml` — KMDS workspace and parser/cleaner configuration
- `featurizer_config.yaml` — longitudinal featurization pipeline settings
- `modeling_config.yaml` — clustering workflow definition
- `data/SP_2017_freq_prod_weekly_sales_prepared.csv` — prepared weekly product affinity matrix
- `models/spectral_clustering.py` — spectral clustering implementation
- `models/clustering_advisor.py` — cluster profiling and recommendation wrapper
- `notebooks/modeling_spectral_clustering.ipynb` — clustering execution and visualization
- `notebooks/modeling_clustering_advisor.ipynb` — advisor workflow exploration

## Setup

1. From the workspace root:
   ```bash
   cd /home/rajiv/programming/kmds_migration/olist_migration
   source .venv/bin/activate
   ```
2. Install dependencies if needed:
   ```bash
   pip install -r requirements.txt
   pip install pyarrow kmds-modeling
   ```

## Getting Started

1. Run the parser and cleaner:
   ```bash
   .venv/bin/classify-entities --config customer_config.yaml
   .venv/bin/clean-dataset --config customer_config.yaml --action full
   .venv/bin/classify-entities --config config.yaml
   .venv/bin/clean-dataset --config config.yaml --action full
   ```
2. Run the longitudinal featurization pipeline:
   ```bash
   python featurization_scripts/featurization.py
   ```
3. Confirm the prepared SP 2017 matrix exists:
   ```bash
   ls data/SP_2017_freq_prod_weekly_sales_prepared.csv
   ```
4. Run the clustering model:
   ```bash
   .venv/bin/python -c "from models.spectral_clustering import run_spectral_clustering; print(run_spectral_clustering('modeling_config.yaml', output_dir='models'))"
   ```
5. Run the clustering advisor:
   ```bash
   .venv/bin/python -c "from models.clustering_advisor import run_clustering_advisor; print(run_clustering_advisor('modeling_config.yaml'))"
   ```

## Recommended workflow

1. Parse and clean raw data with the KMDS parser and cleaner
2. Run the featurization pipeline to build longitudinal weekly affinity features
3. Validate the prepared SP 2017 product-week matrix
4. Run spectral clustering and clustering advisor workflows
5. Inspect generated artifacts in `models/` and `output/`

## Notes

- This project is modeled as a longitudinal dataset rather than cross-sectional.
- The KMDS tooling is configured to support real-data issues such as missing records, quarantine workflow output, and downstream model-ready feature artifacts.
