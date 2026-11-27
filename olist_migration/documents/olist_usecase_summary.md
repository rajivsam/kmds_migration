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

The filtered export has 52 rows, 870 retained original product values, and a cluster label. Four week regimes contain:

| Cluster | Weeks | Share of year |
| --- | ---: | ---: |
| 0 | 23 | 44.2% |
| 1 | 12 | 23.1% |
| 2 | 9 | 17.3% |
| 3 | 8 | 15.4% |

The current result does not assign 9,367 products to product clusters. Product IDs are features that differentiate weekly observations. A product is described by its ability to separate week regimes, not by membership in one of the four current clusters.

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

- [`SP_2017_freq_prod_weekly_sales_prepared.csv`](../data/SP_2017_freq_prod_weekly_sales_prepared.csv)
- [`SP_2017_cluster_feature_report.json`](../data/SP_2017_cluster_feature_report.json)
- [`SP_2017_dropped_features.csv`](../data/SP_2017_dropped_features.csv)
- [`SP_2017_filtered_original_features.csv`](../data/SP_2017_filtered_original_features.csv)

Earlier `models/product_clusters.csv` and related co-clustering outputs belong to a previous unpruned experiment. Preserve them as historical evidence, but do not combine their product-cluster counts with the current week-regime result.

The current artifacts do not demonstrate cluster stability, a causal calendar explanation, realized inventory savings, or forecast uplift. Inventory economics are outside the available data.
