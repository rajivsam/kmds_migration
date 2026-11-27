---
## Inventory segmentation as a supply-chain problem

Retailers manage large, heterogeneous assortments across distribution networks. A uniform operating policy ignores differences in demand frequency, seasonality, revenue, and volatility. Static ABC analysis is useful when a single value or volume criterion is sufficient, but it does not represent temporal demand structure by itself.

Unsupervised segmentation can help discover groups for further investigation. It is not an inventory policy on its own: cluster structure must be joined to margin, lead time, service targets, inventory position, and demand-forecast performance.

## Why clustering must follow feature hygiene

The Olist São Paulo 2017 matrix begins with 9,367 sparse product-revenue columns and only 52 weekly observations. If all columns are passed directly to clustering, near-constant, extremely sparse, or redundant columns can dominate the geometry without carrying a useful demand signal.

The current workflow uses `cluster-geometry-profiler` to screen:

- sparse or nearly degenerate columns;
- zero-spread columns; and
- highly redundant Spearman proxies.

This reduces the analytical basis to 870 retained product features. The profiler diagnoses nonlinear geometry, reports a seven-dimensional reduced diagnostic representation, and supports post-clustering profiling of the retained features.

## What is clustered in this implementation

The rows of the retained 52-by-870 matrix are weeks. The four current cluster labels therefore identify weekly demand regimes, not membership of 9,367 SKUs in product clusters.

This distinction keeps the business claim aligned with the evidence:

- retained product IDs are explanatory features;
- week observations receive cluster labels;
- feature profiles identify products associated with regime separation; and
- operational meaning still has to be validated.

## Evaluation

The segmentation should be evaluated by:

- repeatability across random states;
- stability across reasonable cluster counts;
- interpretable week and retained-feature profiles;
- separation that survives geometry-appropriate validation; and
- improved planning decisions against an existing policy.

Inventory savings, service-level improvements, or forecast uplift are not established by cluster presence alone.

See [the implementation summary](olist_temporal_affinity_analytics_for_SP.md) and [the full use case](olist_usecase_summary.md).
