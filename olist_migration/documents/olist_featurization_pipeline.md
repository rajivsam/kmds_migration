# Olist Featurization and Analysis Pipeline

## Pipeline intent

This pipeline converts the Olist transaction sources into a São Paulo 2017 weekly product-revenue matrix and a screened representation suitable for geometry-aware clustering.

## Configuration and path resolution

`featurizer_config.yaml` centralizes the input and output paths. The implementation uses the KMDS `dd_cleaner.notebook_utils.PathCoordinator` contract, loading the cleaned orders authority dataset when available and falling back to configured raw inputs only when required.

## Preparation stages

1. `load_raw_data`
   - Load orders, order items, and customers.
   - Join transaction details and customer geography.
2. `build_order_level_dataset`
   - Parse timestamps and construct the prepared order-level data.
3. `derive_sp_2017_subset`
   - Add year, month, and ISO week fields.
   - Select São Paulo transactions from 2017.
4. `build_sp_weekly_product_matrix`
   - Aggregate weekly revenue.
   - Pivot product IDs into candidate feature columns.

The primary prepared matrix is `data/SP_2017_freq_prod_weekly_sales_prepared.csv`: 52 week rows and 9,367 product-revenue candidates.

## Feature-advisor output

The KMDS feature advisor provides encoding recommendations for the transactional metadata. That output is useful for understanding the order-level preparation stages, but the weekly matrix already encodes product activity as numeric feature columns. The feature-advisor recommendation is not a substitute for pre-clustering feature hygiene.

The advisor artifact remains at `data/data/feature_advisor/feature_advisor_recommendations.md`.

## Profiler screening

The downstream `cluster-geometry-profiler` package from [`cluster_feature_analysis`](https://github.com/rajivsam/cluster_feature_analysis) audits the 52-by-9,367 matrix:

- sparsity: 9,367 to 2,720 features;
- zero spread: 2,720 to 1,270 features;
- Spearman redundancy: 1,270 to 870 features.

The 870 retained features, not the original 9,367 candidate columns, form the current clustering basis. Seven reduced dimensions are reported for geometry diagnosis. The profiler exports retained original values rather than relabeling transformed coordinates as source features.

## Post-screen outputs

- `data/SP_2017_cluster_feature_report.json`
- `data/SP_2017_dropped_features.csv`
- `data/SP_2017_filtered_original_features.csv`

The filtered dataset contains 52 rows, 870 retained product features, and one cluster label. The report contains 8,497 drop records and 870 retained-feature profiles.

## Usage

Run the preparation pipeline with:

```bash
.venv/bin/python featurization_scripts/featurization.py
```

Then run the notebook or client workflow that uses `ClusterGeometryProfiler` to regenerate the report, drop file, and filtered dataset. Validate that:

- the input matrix still has 52 weekly observations;
- retained feature names match the report;
- the filtered feature count is 870;
- every original feature is accounted for as retained or dropped; and
- any persisted cluster and figure outputs come from the same executed analysis run.

## Design boundary

Featurization creates candidate product-week features. The profiler decides which candidates enter the clustering geometry. Clustering assigns labels to week observations. Post-clustering profiling explains feature separation. These are separate stages and should not be documented as a single feature-selection/modeling step.
