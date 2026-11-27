# Clustering Task Initialization Template

This template documents the local task setup for Olist SP 2017 spectral co-clustering.

## Intent
- Task: `CLUSTERING`
- Domain: Olist customer purchasing behavior in São Paulo, 2017
- Input: weekly product activity matrix from featurization
- Goal: discover seasonal and product affinity clusters jointly across weeks and products

## Configuration
Use `modeling_config.yaml` in the workspace root with the following core values:

```yaml
data:
  working_dir: /home/rajiv/programming/kmds_migration/olist_migration
  index_column: woy
  model_ready_data_file: SP_2017_freq_prod_weekly_sales_prepared.parquet
  featurization_output_dir: "."
  modeling_output_dir: models

project:
  name: "olist_sp2017_clustering"
  experiment_version: "0.1.0"
  task_type: "CLUSTERING"
  description: "Spectral co-clustering for Olist SP 2017 weekly product activity"

algorithm:
  model_family: spectral_coclustering
  n_clusters: null
  embedding_dim: 4
  random_state: 42
  use_spectral_gap_analysis: true
```

## Implementation Steps
1. Load the prepared weekly product matrix from `data/SP_2017_freq_prod_weekly_sales_prepared.parquet`.
2. Apply TF-IDF normalization across weeks and products to reduce the influence of globally dominant products.
3. Build the normalized bipartite affinity matrix:
   - `B = D_W^{-1/2} A D_P^{-1/2}`
4. Compute the SVD of `B`.
5. Assemble the joint embedding matrix `Z` from scaled week and product singular vectors.
6. Use a symmetric-normalized-Laplacian eigengap rule instead of a fixed cluster constant. Preserve the primary `k=2` gap as the theoretical macro-partition, then select the first substantial secondary gap at least 75% as large as the primary. The current provisional solution is `k=4`.
7. Run `KMeans` on `Z` to produce week and product cluster labels.

## Output Artifacts
- `models/spectral_gap.csv`
- `models/week_clusters.csv`
- `models/product_clusters.csv`
- `models/week_embeddings.csv`
- `models/product_embeddings.csv`
- `models/cluster_counts.csv`
- `models/spectral_clustering_summary.md`

## Why Spectral Clustering
The attached `rationale_for_spectral_clustering.md` shows that the week-product dataset is best modeled as a bipartite affinity graph rather than a flat Euclidean feature matrix. The spectral approach:
- respects the dual week/product manifold structure,
- normalizes against high-volume evergreen products,
- isolates seasonal shopping regimes with joint week-product coherence.

Experts on the data science team agree that for SP 2017, spectral co-clustering is a better fit than standard flat clustering because it preserves the underlying bipartite graph topology and yields interpretable week/product segmentations.
