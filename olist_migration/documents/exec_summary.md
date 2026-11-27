# Executive Summary: Olist Regional Demand Segmentation

## The problem

A retailer should not assume that thousands of SKUs have the same demand behavior throughout the year. This case study asks whether the São Paulo 2017 weekly sales matrix contains distinct operating regimes while avoiding conclusions driven by sparse, constant, or redundant product columns.

## Scope and current method

The workflow selects 20,044 order-item records from the complete 2017 calendar year and São Paulo market. It builds a 52-week by 9,367-product revenue matrix, where each cell is the sum of item prices for one product in one week.

The matrix is then audited by the [`cluster_feature_analysis`](https://github.com/rajivsam/cluster_feature_analysis) profiler before the final geometry-aware analysis:

1. remove sparse or near-degenerate columns;
2. remove zero-spread columns;
3. remove highly redundant Spearman proxies;
4. diagnose the retained geometry; and
5. profile retained features after clustering.

The persisted audit reduces **9,367 candidate product features to 870 retained features**. The profiler reports a nonlinear-manifold geometry and a seven-dimensional reduced diagnostic representation.

## Verified result

- **52 week observations** are clustered.
- **870 retained product features** are used in the analysis.
- **8,497 product columns (90.7%)** are removed by the three screening gates.
- The observed week-cluster sizes are **23, 12, 9, and 8**.
- The filtered export contains 52 rows, 870 original retained feature values, and one cluster column.
- Every retained feature is profiled; the report includes 870 post-clustering feature profiles.

The measured result is a four-regime weekly segmentation supported by screened product behavior. It is not a clustering of all 9,367 SKUs. Retained product IDs are model features, not cluster members.

## Why it is actionable

The retained-feature workflow provides a defensible queue for investigation:

1. characterize the four week regimes;
2. identify retained products that separate the regimes;
3. join those signals to category, margin, lead time, stock, and promotion data; and
4. test differentiated planning rules before operational use.

The analysis does not prove that a regime is seasonal, promotional, or evergreen, and it does not demonstrate realized inventory savings. Those interpretations require profiling and controlled validation.

## Evidence

- [`SP_2017_cluster_feature_report.json`](../data/SP_2017_cluster_feature_report.json)
- [`SP_2017_dropped_features.csv`](../data/SP_2017_dropped_features.csv)
- [`SP_2017_filtered_original_features.csv`](../data/SP_2017_filtered_original_features.csv)
- [`SP_2017_freq_prod_weekly_sales_prepared.csv`](../data/SP_2017_freq_prod_weekly_sales_prepared.csv)

Older files under `models/` describe a previous 9,367-column spectral co-clustering experiment. They are historical evidence, not the current analysis result.
