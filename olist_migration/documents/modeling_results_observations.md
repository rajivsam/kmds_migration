# Modeling Results Observations

## Verified result

The current analysis audits the São Paulo 2017 week-by-product matrix with `cluster-geometry-profiler` and then clusters 52 weekly observations over the retained original product features. The cluster count is selected from the largest gap in the normalized singular spectrum rather than from a hard-coded constant. On the current matrix, the largest positive gap is between the second and third singular values, so the spectral-gap heuristic selects `k = 2` for the KMeans stage.

The final persisted outputs therefore show:

| Item | Current result |
| --- | ---: |
| Candidate product features | 9,367 |
| Retained product features | 870 |
| Dropped product features | 8,497 |
| Total profiler pruning | 90.7% |
| Reduced diagnostic dimensions | 7 |
| Week observations | 52 |
| Spectral-gap-based cluster count | 2 |

## Screening observations

The screening gates are label-independent and sequential, so each percentage uses the input to that stage:

1. Sparsity removes 6,647 of 9,367 candidates (71.0%), leaving 2,720.
2. Zero spread removes 1,450 of 2,720 candidates (53.3%), leaving 1,270.
3. Spearman redundancy removes 400 of 1,270 candidates (31.5%), leaving 870.

Together, these gates remove 8,497 of the original 9,367 columns. The drop export records a gate, statistic, threshold, rationale, and proxy where applicable for every removed feature.

## Geometry observations

The profiler diagnoses a **nonlinear-manifold** geometry and recommends a geometry-aware clustering family rather than treating Euclidean geometry as self-evident. The report records a local intrinsic dimension of approximately 5.37, a participation ratio of approximately 44, and a geodesic/euclidean ratio of approximately 1.44.

## Post-clustering observations

All 870 retained product features are ranked in the retained-feature profile. The ranking uses:

- Kruskal-Wallis epsilon squared;
- cluster mutual information; and
- dispersion reduction.

It also preserves normalized entropy and cluster-conditioned median, MAD, and IQR summaries. These are descriptions of feature separation after clustering, not causal claims about why demand changed.

## Business interpretation boundary

- The largest week regime contains 23 of 52 weeks, but it is not automatically an “evergreen” segment.
- The smaller week regimes identify periods for investigation, not confirmed holiday or promotion effects.
- Retained product IDs are explanatory features of the week regimes; they are not product-cluster assignments.
- Product, category, calendar, price, margin, stock, and promotion profiling is required before changing an operating policy.

## Historical artifacts

The previous `models/product_clusters.csv` and its 8,661-SKU dominant-cluster observation came from an earlier 9,367-column co-clustering workflow. Do not combine those counts with the current four week-regime result or describe them as post-screening outcomes.
