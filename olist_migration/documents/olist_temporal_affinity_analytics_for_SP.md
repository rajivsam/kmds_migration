# Olist Temporal Affinity Analytics for São Paulo

## Objective

This analysis identifies weekly demand regimes in the São Paulo 2017 marketplace data. It preserves the link between calendar weeks and product revenue while screening out product columns that cannot contribute reliable structure.

## Data preparation

The KMDS pipeline joins orders, order items, and customer geography, selects São Paulo transactions from 2017, and aggregates item prices by ISO week and product ID.

The source analytical matrix is:

- 52 week rows;
- 9,367 product columns;
- one value per week-product pair representing weekly item-price revenue.

The matrix is sparse and much wider than it is tall, so raw scale and column count must not be confused with useful information.

## Geometry-audited workflow

The canonical analysis uses [`cluster_feature_analysis`](https://github.com/rajivsam/cluster_feature_analysis) through the `cluster-geometry-profiler` package.

### 1. Screen features before clustering

The profiler applies three label-independent gates:

| Gate | Input | Output | Dropped | Drop rate for this stage |
| --- | ---: | ---: | ---: | ---: |
| Sparsity | 9,367 | 2,720 | 6,647 | 71.0% |
| Zero spread | 2,720 | 1,270 | 1,450 | 53.3% |
| Spearman redundancy | 1,270 | 870 | 400 | 31.5% |

The three stages retain **870 original product features** and remove **8,497**, or 90.7% of the candidate columns.

### 2. Diagnose geometry

The retained 52-by-870 matrix is diagnosed as a nonlinear manifold. The report records seven reduced diagnostic dimensions and recommends spectral clustering or HDBSCAN as suitable geometry-aware families.

Useful diagnostics include:

- sample-to-feature ratio;
- condition number;
- participation ratio;
- local intrinsic dimension;
- geodesic/euclidean ratio; and
- separation between convex and connectivity-oriented partitions.

### 3. Cluster week observations

The current filtered dataset contains one row per week and 870 retained product features. The exported `cluster` field partitions the 52 rows into four regimes with sizes:

- cluster 0: 23 weeks;
- cluster 1: 12 weeks;
- cluster 2: 9 weeks; and
- cluster 3: 8 weeks.

Cluster numbers are identifiers. Semantic names such as “baseline,” “holiday,” or “promotion” should be assigned only after profiling the week and product evidence.

### 4. Profile retained features

The profiler retains original feature values in the filtered dataset and profiles all 870 retained features after clustering. The report ranks them using Kruskal-Wallis epsilon squared, cluster mutual information, and dispersion reduction, with cluster-conditioned median, MAD, and IQR summaries.

## Current outputs

- [`SP_2017_cluster_feature_report.json`](../data/SP_2017_cluster_feature_report.json) — screening, geometry diagnostics, and retained-feature profiles.
- [`SP_2017_dropped_features.csv`](../data/SP_2017_dropped_features.csv) — one audited row for each of 8,497 removed features.
- [`SP_2017_filtered_original_features.csv`](../data/SP_2017_filtered_original_features.csv) — 52 rows, 870 retained product features, and cluster labels.

The earlier `models/` spectral co-clustering outputs are preserved as a prior experiment. They used the unpruned 9,367-column representation and should not be presented as the current canonical findings.

## Operational use

The four week regimes can direct focused inventory, staffing, merchandising, and forecast review. The strongest retained product features can help explain which demand patterns separate those regimes.

Before action, analysts should:

1. map row order to ISO week labels in the reporting layer;
2. enrich retained products with category and margin data;
3. check cluster stability under repeated runs and reasonable cluster counts;
4. link week regimes to calendar events; and
5. compare any proposed differentiated policy with the existing operating rule.

## Conclusion

The updated analysis is not “spectral clustering on 9,367 products.” It is a screened, geometry-informed segmentation of 52 weeks using 870 auditable product features, followed by post-clustering feature profiling. This makes the result easier to reproduce, explain, and validate.
