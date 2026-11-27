# Olist Marketplace Modeling Summary

## Problem statement

The objective is to discover demand regimes across the 52 weeks of São Paulo 2017 without imposing a target variable or treating thousands of sparse product columns as equally informative.

## Dataset and analytical grain

The source workflow creates a 52-row by 9,367-column weekly product-revenue matrix. Rows are weeks; columns are product IDs; cells contain summed item-price revenue.

This orientation is important:

- source columns are Olist order, item, and customer fields;
- candidate features are the 9,367 product-revenue columns;
- retained features are the 870 columns that survive profiler screening;
- reduced coordinates are seven diagnostic dimensions; and
- clustered observations are the 52 weeks.

## Preprocessing

The KMDS preparation workflow cleans and joins the relevant Olist tables, selects São Paulo 2017, and aggregates item prices into the weekly product matrix.

The geometry profiler then applies:

1. sparsity screening: 9,367 to 2,720;
2. zero-spread screening: 2,720 to 1,270; and
3. Spearman-redundancy screening: 1,270 to 870.

The 8,497 dropped features are recorded with their gate, statistic, threshold, rationale, and proxy where applicable. Filtered exports contain the original values of the retained features, not embedding coordinates.

## Model selection

The retained matrix is diagnosed as a nonlinear manifold. The current analysis is therefore geometry-aware rather than a default Euclidean clustering of all raw columns. The profiler recommends spectral clustering or HDBSCAN for this geometry and reports seven reduced diagnostic dimensions.

The cluster count is not hard-coded. The implementation builds a mutual 10-nearest-neighbor graph with self-tuning local RBF bandwidth and evaluates the symmetric normalized Laplacian. The primary eigengap gives `k=2`; the first later gap meeting the declared 75%-of-primary threshold gives the provisional operational selection `k=4` (gap 0.0686 versus 0.0846).

## Post-clustering evaluation

Evaluation is diagnostic rather than a supervised score:

- geometry statistics support the selected method family;
- the provisional partition contains 17, 18, 9, and 8 weeks;
- Kruskal-Wallis epsilon squared and mutual information rank retained-feature separation;
- dispersion reduction and median/MAD/IQR summaries characterize cluster-conditioned behavior; and
- bandwidth sensitivity is strong (ARI 1.0 for sigma-neighbor ranks 6-8), while 50-run 80% week-subsampling stability is moderate (mean ARI about 0.57); `k=4` is therefore provisional rather than production-stable.

## Canonical outputs

- [`SP_2017_cluster_feature_report.json`](../data/SP_2017_cluster_feature_report.json)
- [`SP_2017_dropped_features.csv`](../data/SP_2017_dropped_features.csv)
- [`SP_2017_filtered_original_features.csv`](../data/SP_2017_filtered_original_features.csv)
- [`SP_2017_freq_prod_weekly_sales_prepared.csv`](../data/SP_2017_freq_prod_weekly_sales_prepared.csv)

## Legacy outputs

The earlier `models/` spectral co-clustering artifacts cluster both sides of the unpruned bipartite matrix and report product memberships across 9,367 SKUs. They answer a different question and predate the current feature-hygiene workflow. Keep them for provenance, but do not present their 8,661-product dominant cluster or other product counts as current results.

## Interpretation boundary

The current evidence supports:

- four observed week regimes;
- an auditable 870-feature basis; and
- ranked retained products for regime explanation.

It does not establish:

- semantic labels for the regimes;
- that the four regimes are stable across years or under strong data perturbation;
- realized forecast, inventory, or margin improvement; or
- a direct product-level segmentation policy.

## Related implementation references

- [Featurization pipeline](olist_featurization_pipeline.md)
- [Temporal analytics method](olist_temporal_affinity_analytics_for_SP.md)
- [Use-case summary](olist_usecase_summary.md)
- [Modeling observations](modeling_results_observations.md)
