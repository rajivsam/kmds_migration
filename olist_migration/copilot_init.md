# Project Initialization Helper

This file captures the current workspace setup and the commands needed to reinitialize and continue work in the Olist migration project.

## Project Context

- Repository: `olist_migration`
- Primary use-case: Olist temporal affinity analytics for São Paulo 2017
- Main data flow:
  - `dd_parser_cleaner` parsing and cleaning
  - featurization pipeline driven by `featurizer_config.yaml`
  - clustering modeling pipeline driven by `modeling_config.yaml`
- Key focus: product-week affinity for SP 2017 using KMDS featurization outputs

## Session updates

- Data scientist executed `dd-parser-cleaner` workflows with `classify-entities` and `clean-dataset` to validate and clean customer/order data.
- A KMDS helper summary artifact was generated at `output/full_service_report.json`.
- `kmds-data-helper` was used to ingest that helper output and create `data/kmds/project_knowledge_graph.xml`.
- `kmds-ui` can be launched via `.venv/bin/kmds-workbench` and viewed at `http://127.0.0.1:8050`.
- The parent repository `.gitignore` was updated to ignore large Olist migration files from `olist_migration/data/`.

## Current stop point

- `notebooks/raw_datafile_creation.ipynb` has been updated and now produces the week × product_id revenue matrix for SP 2017.
- The latest generated file is `data/SP_2017_weekly_product_revenue_by_product_id.csv`.
- Next pickup: validate this dataset, confirm the schema, and wire it into the downstream featurization/modeling workflow.

## Important files

- `config.yaml` — main KMDS workspace configuration
- `customer_config.yaml` — parser/cleaner config for customer metadata
- `featurizer_config.yaml` — featurization pipeline configuration
- `modeling_config.yaml` — local clustering model configuration
- `data/SP_2017_freq_prod_weekly_sales_prepared.csv` — SP 2017 product-week affinity matrix
- `data/SP_2017_weekly_product_revenue_by_product_id.csv` — current week × product_id revenue matrix output from `notebooks/raw_datafile_creation.ipynb`
- `documents/olist_featurization_pipeline.md` — featurization pipeline documentation
- `agent_documents/olist_temporal_affinity_analytics_for_SP.md` — use case summary
- `agent_documents/clustering_task_initialization.md` — clustering task template
- `agent_documents/agent_instructions_for_clustering.md` — agent-facing clustering guidelines
- `notebooks/modeling_spectral_clustering.ipynb` — clustering model execution and visualization
- `notebooks/modeling_clustering_advisor.ipynb` — clustering advisor execution
- `models/spectral_clustering.py` — spectral clustering implementation
- `models/clustering_advisor.py` — advisor wrapper for cluster profiling

## Environment setup

```bash
cd /home/rajiv/programming/kmds_migration/olist_migration
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # if present
pip install pyarrow
pip install kmds-modeling
``` 

If you already have the venv, just activate it:

```bash
cd /home/rajiv/programming/kmds_migration/olist_migration
source .venv/bin/activate
```

## Featurization and modeling interface discovery

### Featurization (`kmds-featurization`)
- Package name: `kmds-featurization`
- Import path: `import featurization`
- Top-level exports: `FeatureAdvisorPromptConfig`, `FeatureAdvisorUtil`
- Subpackages available: `featurization.cli`, `featurization.core`, `featurization.feature_advisor_util`, `featurization.notebook_utils`, `featurization.utils`
- `get_package_info()` is not available in this package; use `dir()`/`pkgutil.iter_modules()` instead.
- Example runtime inspection:
  ```bash
  python - <<'PY'
  import featurization, pkgutil
  print('featurization path:', featurization.__file__)
  print('exports:', [n for n in dir(featurization) if not n.startswith('_')])
  print('submodules:', [m.name for m in pkgutil.iter_modules(featurization.__path__)])
  PY
  ```
- Key interfaces to inspect:
  - `featurization.FeatureAdvisorPromptConfig`
  - `featurization.FeatureAdvisorUtil`
  - `featurization.core` subpackage for additional runtime helpers

### Modeling (`kmds_modeling`)
- Import path: `import kmds_modeling`
- Main exports: `BaseFeatureTransformer`, `BaseModelCandidate`, `ExperimentRunner`, `core`
- `ExperimentRunner` behavior:
  - Initialized with a config path like `modeling_config.yaml`
  - Loads YAML config and resolves paths with `PathCoordinator`
  - Reads the model-ready dataset CSV from `path_coordinator.model_ready_dataset_path`
  - Sets `self.X` and `self.y` from the configured `target_variable`
  - Supports additional feature transformers with `register_transformer()`
  - Runs evaluation via `run_evaluation()` and exports champion models via `export_champion()`
  - Supports task types: `TABULAR_CLASSIFICATION`, `TABULAR_REGRESSION`, `GRAPH_NODE_CLASSIFICATION`, `GRAPH_NODE_REGRESSION`, `GRAPH_DISCOVERY`, `CLUSTERING`
- Abstract interfaces:
  - `BaseFeatureTransformer`: implement `fit(X, y=None)`, `transform(X)`, optional `fit_transform(X, y=None)`
  - `BaseModelCandidate`: accepts `hyperparameters`, implement `fit(X_train, y_train)`, `predict_proba(X)`
- Useful core helpers:
  - `kmds_modeling.core.PathCoordinator`
  - `kmds_modeling.core.ModelAdvisor`
  - `kmds_modeling.core.build_notebook_resolver`
  - `kmds_modeling.core.get_modeling_artifact_paths`
  - `kmds_modeling.core.load_model_ready_dataset`
  - `kmds_modeling.core.load_workspace_config`
  - `kmds_modeling.core.resolve_notebook_workspace_root`
- Example runtime inspection:
  ```bash
  python - <<'PY'
  import inspect
  import kmds_modeling
  from kmds_modeling import core
  print('kmds_modeling path:', kmds_modeling.__file__)
  print('exports:', [n for n in dir(kmds_modeling) if not n.startswith('_')])
  print('core exports:', [n for n in dir(core) if not n.startswith('_')])
  print(inspect.getsource(kmds_modeling.ExperimentRunner))
  PY
  ```

### Exact config keys used by `kmds_modeling`
- `data.working_dir`
- `data.index_column`
- `data.model_ready_data_file`
- `data.featurization_output_dir`
- `data.modeling_output_dir`
- `project.name`
- `project.experiment_version`
- `project.task_type`
- `project.description`
- `algorithm.model_family`
- `algorithm.n_clusters`
- `algorithm.embedding_dim`
- `algorithm.random_state`
- `algorithm.use_spectral_gap_analysis`

> Note: `kmds_modeling.ExperimentRunner._load_data()` expects `project.target_variable` to exist, since it uses that key to split `X` and `y`. The current `modeling_config.yaml` in this repo does not define `project.target_variable`, so direct use of `ExperimentRunner` may require either adding this key or using a clustering-specific wrapper that bypasses the target split.

## Recommended workflow

1. Run parser + cleaner for customer or orders data as needed:
   ```bash
   .venv/bin/classify-entities --config customer_config.yaml
   .venv/bin/clean-dataset --config customer_config.yaml --action full
   .venv/bin/classify-entities --config config.yaml
   .venv/bin/clean-dataset --config config.yaml --action full
   ```
   - The featurization pipeline now uses the KMDS `dd_cleaner.notebook_utils` PathCoordinator to resolve input datasets.
   - It reads the cleaned dataset from `data/dd_cleaner/olist_daily_orders_prepared_clean.csv` when available.
2. Run the featurization pipeline:
   ```bash
   python featurization_scripts/featurization.py
   ```
3. Validate the SP 2017 prepared artifact and the week × product_id matrix:
   ```bash
   ls data/SP_2017_freq_prod_weekly_sales_prepared.csv
   ls data/SP_2017_weekly_product_revenue_by_product_id.csv
   ```
4. Run the clustering model:
   ```bash
   .venv/bin/python -c "from models.spectral_clustering import run_spectral_clustering; print(run_spectral_clustering('modeling_config.yaml', output_dir='models'))"
   ```
5. Run the clustering advisor:
   ```bash
   .venv/bin/python -c "from models.clustering_advisor import run_clustering_advisor; print(run_clustering_advisor('modeling_config.yaml'))"
   ```
6. Build the KMDS helper artifact and knowledge graph:
   ```bash
   python - <<'PY'
   from pathlib import Path, json
   workspace = Path('.')
   helper = {
       'project_summary': 'Generated by KMDS helper integration script.',
       'metadata': {'generated_by': 'kmds-data-helper', 'source': 'repo artifacts'}
   }
   (workspace / 'output' / 'full_service_report.json').write_text(json.dumps(helper, indent=2), encoding='utf-8')
   PY
   .venv/bin/kmds-kb --workspace . \
     --project-file data/kmds/project_knowledge_graph.xml \
     --workflow-name olist_migration_kmds \
     --mode auto \
     --workflow-type application
   ```
7. Launch the KMDS UI:
   ```bash
   .venv/bin/kmds-workbench
   ```
   Then open `http://127.0.0.1:8050` in your browser.
8. Open the notebooks for inspection:
   - `notebooks/modeling_spectral_clustering.ipynb`
   - `notebooks/modeling_clustering_advisor.ipynb`

## Key artifacts to inspect

- `models/spectral_gap.csv`
- `models/week_clusters.csv`
- `models/product_clusters.csv`
- `models/cluster_counts.csv`
- `models/week_embeddings.csv`
- `models/product_embeddings.csv`
- `models/spectral_clustering_summary.md`
- `models/advisor/clustering_advisor_recommendation.json`
- `output/full_service_report.json`
- `data/kmds/project_knowledge_graph.xml`

## Notes for next session

- Always start from the workspace root.
- Use `modeling_config.yaml` for the clustering workflow; it is the single source of truth for modeling inputs.
- If the notebook imports fail, ensure `sys.path` includes the workspace root or run a notebook kernel from the project root.
- The clustering workflow is driven by the prepared SP 2017 week-product matrix and the spectral co-clustering implementation in `models/`.
- Use `agent_documents/agent_instructions_for_clustering.md` for agent-facing implementation guidance.
- Keep `data/SP_2017_freq_prod_weekly_sales_prepared.csv` as the canonical affinity input for this project.
