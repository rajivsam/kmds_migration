# Geometry-Aware Rationale for Spectral Clustering

## Status

This document explains why spectral clustering remains a valid candidate after the updated [`cluster_feature_analysis`](https://github.com/rajivsam/cluster_feature_analysis) workflow. It supersedes the earlier assumption that spectral co-clustering should consume every one of the 9,367 product columns.

The current modeling object is a **52-by-870 retained week-feature matrix**. The 52 week rows receive cluster labels; product IDs are retained explanatory features.

## Why feature screening comes first

The original matrix has 9,367 candidate product columns and only 52 observations. Before constructing a similarity graph or embedding, the profiler removes columns that are sparse, constant for the observed sample, or redundant proxies.

The screening sequence is:

1. 9,367 to 2,720 through sparsity screening.
2. 2,720 to 1,270 through zero-spread screening.
3. 1,270 to 870 through Spearman-redundancy screening.

This is not supervised feature selection. The three gates are independent of cluster labels and preserve an auditable rationale for every removed feature.

## Geometry diagnosis

The retained matrix is diagnosed as a nonlinear manifold. The profiler reports seven reduced diagnostic dimensions and recommends spectral clustering or HDBSCAN as geometry-aware method families.

Spectral clustering is suitable when the useful structure is expressed through neighborhood connectivity or graph smoothness rather than convex Euclidean separation. Its typical stages are:

1. construct an affinity graph from the retained feature representation;
2. derive a graph Laplacian and low-dimensional spectral embedding;
3. partition the embedded week observations; and
4. profile the retained features that distinguish the resulting groups.

## Why not cluster the raw 9,367-column matrix?

Clustering all original columns would mix signal-bearing product activity with:

- columns observed in too few weeks;
- effectively constant columns;
- highly correlated proxies; and
- high-magnitude activity that can distort the sample geometry.

The 8,497 dropped columns are still documented in the drop report. Removing them from the model basis is not equivalent to deleting the transaction records or denying product existence.

## Current result

The data-driven cluster count is selected from the largest singular-gap in the normalized affinity spectrum instead of a fixed `n_clusters` value. In the current matrix, the largest positive gap sits between the second and third singular values, so the spectral-gap heuristic selects `k = 2` for the KMeans stage. This keeps the split tied to the observed geometry of the weekly product matrix and makes the partition reproducible when the dataset changes.

The retained-feature report, week-to-calendar mapping, repeatability checks, and business enrichment remain required before assigning semantic names to any labeling produced by the spectral-gap heuristic.

## Evaluation

The rationale should be evaluated with:

- graph/embedding diagnostics from the profiler report;
- cluster stability across random states;
- sensitivity to reasonable values of the cluster count and neighborhood parameters;
- feature-level separation among retained features; and
- operational validation against a relevant baseline.

The earlier bipartite co-clustering rationale remains useful as an historical modeling experiment, but it is not the canonical basis for the current 870-feature week analysis.
