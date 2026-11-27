# KMDS Toolkit Usage Summary

## Purpose

This document records the current Olist workflow and the responsibility of each KMDS component. The analytical story now includes pre-clustering feature hygiene and geometry diagnosis from `cluster-geometry-profiler`.

## Toolkit components

1. **`dd-parser-cleaner`**
   - Profiles and cleans the order and customer metadata.
   - Runs through `classify-entities` and `clean-dataset`.
   - Produces cleaned data and schema/quality reports.

2. **Featurization pipeline**
   - Uses `featurizer_config.yaml` and `featurization_scripts/featurization.py`.
   - Builds the São Paulo 2017 weekly revenue matrix from prepared transactional data.
   - Produces 52 week rows and 9,367 candidate product-revenue columns.

3. **Feature advisor**
   - Recommends encodings for transactional and derived metadata.
   - Its output remains in `data/data/feature_advisor/feature_advisor_recommendations.md`.
   - It informs preparation; it is not the pre-clustering feature-screening report.

4. **`cluster-geometry-profiler`**
   - Supplies the current feature-hygiene and geometry-analysis layer.
   - Package origin: [`cluster_feature_analysis`](https://github.com/rajivsam/cluster_feature_analysis).
   - Applies sparsity, zero-spread, and Spearman-redundancy gates.
   - Reduces 9,367 candidate product features to 870 retained features.
   - Diagnoses geometry and produces post-clustering retained-feature profiles.

5. **Modeling implementation**
   - Clusters 52 weekly observations over the 870 retained product features.
   - The geometry report recommends spectral clustering or HDBSCAN for the diagnosed nonlinear manifold.
   - The persisted filtered dataset contains four week clusters with sizes 17, 18, 9, and 8.

6. **`kmds-data-helper`**
   - Ingests generated project summaries into the KMDS knowledge graph.
   - The graph artifact is `data/kmds/project_knowledge_graph.xml`.
   - Existing graph observations must be refreshed before they are treated as evidence for the new 870-feature workflow.

7. **`kmds-ui`**
   - Provides interactive inspection of the generated KMDS graph.

## Current execution path

### 1. Profile and clean

Run the parser and cleaner against the configured order and customer datasets. Preserve the generated profiling and handshake reports as data-quality evidence.

### 2. Prepare the weekly matrix

Run:

```bash
.venv/bin/python featurization_scripts/featurization.py
```

Verify `data/SP_2017_freq_prod_weekly_sales_prepared.csv` has 52 weekly observations and 9,367 candidate product-revenue columns.

### 3. Audit features and geometry

Run the client workflow backed by `ClusterGeometryProfiler` and regenerate:

- `data/SP_2017_cluster_feature_report.json`
- `data/SP_2017_dropped_features.csv`
- `data/SP_2017_filtered_original_features.csv`

Verified screening progression:

| Stage | Input | Output | Dropped |
| --- | ---: | ---: | ---: |
| Sparsity | 9,367 | 2,720 | 6,647 |
| Zero spread | 2,720 | 1,270 | 1,450 |
| Spearman redundancy | 1,270 | 870 | 400 |

### 4. Interpret the current result

The filtered dataset is 52-by-870 with one cluster column. The profiler report has a 870-row retained-feature profile and an 8,497-row drop report. The provisional spectral solution has four week-cluster sizes of 17, 18, 9, and 8. The `k=4` choice comes from a substantial secondary eigengap, with moderate 80% subsampling ARI documented as a limitation.

Retained product IDs are features that differentiate weeks. They are not current product-cluster assignments.

### 5. Publish refreshed KMDS evidence

After documentation and notebook outputs are regenerated from the same profiler run, rebuild the helper artifact and KMDS graph:

```bash
.venv/bin/kmds-kb --workspace . \
  --project-file data/kmds/project_knowledge_graph.xml \
  --workflow-name olist_migration_kmds \
  --mode auto \
  --workflow-type application
```

Do not reuse graph observations from the earlier 9,367-column co-clustering run as if they described the screened 870-feature result.

## Canonical artifact inventory

- `data/SP_2017_freq_prod_weekly_sales_prepared.csv`
- `data/SP_2017_cluster_feature_report.json`
- `data/SP_2017_dropped_features.csv`
- `data/SP_2017_filtered_original_features.csv`
- `documents/olist_temporal_affinity_analytics_for_SP.md`
- `documents/modeling_summary.md`
- `documents/olist_usecase_summary.md`

## Legacy artifact boundary

Files such as `models/product_clusters.csv`, `models/week_clusters.csv`, and `models/spectral_clustering_summary.md` document the earlier bipartite co-clustering experiment on the unpruned matrix. Preserve them for provenance, but label them historical when used in current reporting.
