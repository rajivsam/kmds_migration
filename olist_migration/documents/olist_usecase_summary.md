# Regional Temporal Demand Segmentation with Unsupervised Learning

## Executive proposition

The Olist São Paulo case study converts a transaction history into an auditable segmentation of weekly demand regimes. The result is not a prediction of a target variable. It identifies which weeks differ in their screened product-demand profiles and which retained products best explain those differences.

## Business decision

A regional retail team needs to decide whether the same operating posture is appropriate throughout the year. The supported question is:

> Which São Paulo 2017 weeks form distinct demand regimes, and which retained product features characterize those regimes?

The output is a decision-support queue. Inventory orders, safety stock, margins, lead times, stock availability, and service levels are not present in the analytical matrix.

## Scope

The public Olist data contain 112,650 cleaned order-item records. The analysis selects São Paulo transactions from 2017 because it combines the largest represented market with a complete calendar year. This retains 20,044 item records.

The transaction-level data become:

- 52 weekly observations;
- 9,367 candidate product-revenue features; and
- item-price revenue as the matrix value.

## Feature hygiene and geometry audit

The current workflow uses the [`cluster_feature_analysis`](https://github.com/rajivsam/cluster_feature_analysis) profiler before interpreting geometry or cluster structure.

| Screening stage | Candidate input | Dropped | Retained output |
| --- | ---: | ---: | ---: |
| Sparsity | 9,367 | 6,647 | 2,720 |
| Zero spread | 2,720 | 1,450 | 1,270 |
| Spearman redundancy | 1,270 | 400 | 870 |

The analysis therefore uses **870 retained product features**, not all 9,367 source columns. The removed 8,497 columns represent 90.7% of the original candidate space. The stage percentages are calculated against each stage’s input.

The report diagnoses a nonlinear manifold and records seven reduced diagnostic dimensions. `SpectralClustering` or HDBSCAN is recommended as a geometry-aware family; Euclidean clustering is not assumed to be valid solely because it is convenient.

## Current result

The current notebook execution loads the raw São Paulo 2017 product-by-week matrix and applies the three required `cluster_feature_analysis` screening gates. It then constructs a mutual 10-nearest-neighbor graph using cosine distance and per-week local RBF scaling, with each point's sigma fitted from its seventh-nearest-neighbor distance. The symmetric normalized Laplacian is evaluated rather than the singular values of the bipartite matrix.

In theory, the standard eigengap heuristic identifies the dominant `k=2` macro-partition. Practical spectral clustering also investigates secondary eigengaps when they expose finer, useful structure. The model applies a declared secondary-gap rule: select the first later gap that is at least 75% as large as the primary gap. The `k=4` gap is 0.0686, or 81% of the primary 0.0846 gap, so `k=4` is the single provisional solution presented by this project.

The resulting week-cluster counts are:

| Cluster | Weeks | Share of year |
| --- | ---: | ---: |
| 0 | 17 | 32.7% |
| 1 | 18 | 34.6% |
| 2 | 9 | 17.3% |
| 3 | 8 | 15.4% |

This is an eigengap-derived four-regime model, not a blend of validation metrics. Geometric validation favors `k=4` relative to its neighboring candidates: silhouette is 0.657, Davies-Bouldin is 0.580, and Calinski-Harabasz is 104.55. The `k=2` silhouette is not used as a competing proof because its one-dimensional embedding can make coarse separation look artificially ideal. The local-sigma perturbation check is stable (neighbor ranks 6-8 produce ARI 1.0).

The stricter 50-run, 80% week-subsampling check gives mean ARI approximately 0.57. That is moderate rather than the >0.75-0.80 benchmark for a strongly stable segmentation. The four-regime result is therefore defensible as an exploratory planning segmentation, but not yet as a production-stable taxonomy.

The provisional four clusters are operationally distinguishable by revenue and activity breadth: mean weekly revenue is approximately 32.1k, 60.1k, 26.1k, and 43.9k for clusters 0-3, while mean active products are approximately 235, 440, 175, and 322. These profiles provide utility beyond the coarse split, while requiring calendar and category validation before policy use.

The output is week clustering, not a product taxonomy. The 870 retained product IDs are explanatory features for week-level separation; the model does not assign all 9,367 source SKUs to business product clusters.

## Retained-feature profiling

All 870 retained features receive a post-clustering profile:

- Kruskal-Wallis epsilon squared;
- cluster mutual information;
- dispersion reduction;
- normalized entropy;
- global median, MAD, and IQR; and
- cluster-conditioned median, MAD, and IQR.

This separates pre-clustering feature hygiene from post-clustering feature importance.

## Operational meaning

Use the result in stages:

1. Map cluster labels back to ISO week and calendar-event context.
2. Review the highest-separating retained product features.
3. Enrich the findings with category, margin, inventory, lead time, and promotion data.
4. Test regime-specific policies against the existing uniform policy.
5. Check whether the structure is stable across repeated runs and plausible cluster counts.

## KMDS contribution

The reusable contribution is a governed evidence path:

1. state the decision;
2. define the market and time boundary;
3. preserve raw and derived analytical grains;
4. distinguish candidate, dropped, retained, and reduced dimensions;
5. audit every removal;
6. diagnose geometry before selecting a model family;
7. separate clustering from post-clustering feature profiling; and
8. bound operational interpretation.

## Evidence and limitations

Canonical evidence:

- [`SP_2017_freq_prod_weekly_sales.csv`](../data/SP_2017_freq_prod_weekly_sales.csv)
- [`SP_2017_cluster_feature_report.json`](../data/SP_2017_cluster_feature_report.json)
- [`SP_2017_dropped_features.csv`](../data/SP_2017_dropped_features.csv)
- [`SP_2017_filtered_original_features.csv`](../data/SP_2017_filtered_original_features.csv)
- [`spectral_gap.csv`](../models/spectral_gap.csv)
- [`week_clusters.csv`](../models/week_clusters.csv)
- [`week_affinity.csv`](../models/week_affinity.csv)
- [`spectral_gap_stability.csv`](../models/spectral_gap_stability.csv)
- [`cluster_validation.csv`](../models/cluster_validation.csv)
- [`week_cluster_domain_profile.csv`](../models/week_cluster_domain_profile.csv)

Earlier `models/product_clusters.csv` and related co-clustering outputs belong to a previous unpruned experiment. Preserve them as historical evidence, but do not combine their product-cluster counts with the current week-regime result.

The artifacts do not establish stability across years or seasonal regimes, a causal calendar explanation, realized inventory savings, or forecast uplift. Inventory economics are outside the available data.
