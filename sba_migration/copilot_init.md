# Project Initialization Helper

This file captures the current workspace setup and the commands needed to reinitialize and continue work in the SBA migration project.

## Project context

- Repository/workspace: `sba_migration`
- Primary use case: SBA loan risk modeling with geographic/cluster-based feature engineering
- Main data flow:
  - raw dataset inspection and cleaning via the notebooks in `notebooks/`
  - workspace configuration through `config.yaml` and `model_config.yaml`
  - featurization using the KMDS pipeline and `featurizer_config.yaml`
  - local modeling via the implementation under `models/sba_example/`
- Key target variables: `loan_status_r`, `borrower_latitude`, `borrower_longitude`, `hdgc`, `hdbc`

## Current stop point

- The SBA workspace is already bootstrapped with the expected config files.
- The data-cleaning and feature-derivation notebooks are in place and should be the default restart point.
- The expected featurized modeling output is:
  - `data/featurization/model_ready_numeric_data.csv`
- The authoritative modeling guidance is in:
  - `agent_documents/agent_init_modeling.md`
  - `agent_documents/sba_modeling_requirements.md`
  - `agent_documents/sba_problem_framing_collab.md`
- The local modeling workflow must run from the `sba_migration` workspace, not the separate `kmds-modeling` repo, unless explicitly installed for this workspace.

## Important files

- `config.yaml` — workspace-level KMDS configuration
- `model_config.yaml` — model configuration and pipeline defaults
- `featurizer_config.yaml` — featurization settings and output schema
- `notebooks/clean_sba_dataset.ipynb` — SBA cleaning workflow
- `notebooks/clustering_feature_derivation.ipynb` — geographic cluster feature derivation
- `notebooks/feature_advisor_sba_example.ipynb` — feature engineering advisor example
- `agent_documents/agent_init_modeling.md` — install/runtime troubleshooting notes
- `agent_documents/sba_modeling_requirements.md` — modeling requirements and implementation checkpoint
- `agent_documents/spatial_featurization_design.md` — geographic feature design context
- `models/sba_example/` — local SBA model implementation and candidate classes
- `data/featurization/` — featurization output directory

## Environment setup

```bash
cd /home/rajiv/programming/kmds_migration/sba_migration
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install dd-parser-cleaner kmds-featurization kmds-modeling
```

If the environment already exists:

```bash
cd /home/rajiv/programming/kmds_migration/sba_migration
source .venv/bin/activate
```

## Workspace reinitialization

Run these steps in order if a fresh startup is needed:

```bash
init-workspace
location-helper .dataset-bootstrap
bootstrap-config
```

These steps ensure the workspace points at the correct SBA project, bootstraps dataset metadata, and initializes the modeling configuration.

## Data preparation workflow

1. Clean the raw SBA dataset using:
   - `notebooks/clean_sba_dataset.ipynb`
2. Derive geographic clustering features using:
   - `notebooks/clustering_feature_derivation.ipynb`
3. Review the feature advisor example to choose or confirm the final featurization plan:
   - `notebooks/feature_advisor_sba_example.ipynb`
4. Update the featurization pipeline if needed and rerun the feature prep.

## Featurization execution

Run the workspace featurization pipeline and validate output:

```bash
cd /home/rajiv/programming/kmds_migration/sba_migration
source .venv/bin/activate
ls data/featurization
python - <<'PY'
import pandas as pd
from pathlib import Path
path = Path('data/featurization/model_ready_numeric_data.csv')
print('exists:', path.exists())
if path.exists():
    df = pd.read_csv(path)
    print(df.shape)
    print([c for c in ['loan_status_r', 'borrower_latitude', 'borrower_longitude'] if c in df.columns])
PY
```

Expected deliverable:
- `data/featurization/model_ready_numeric_data.csv`
- modeling columns ready for training and active-set scoring

## Modeling workflow

1. Read the initialization and requirement docs first:
   - `agent_documents/agent_init_modeling.md`
   - `agent_documents/sba_modeling_requirements.md`
   - `agent_documents/sba_problem_framing_collab.md`
2. Run the local modeling workflow under `models/sba_example/`.
3. Use the model-ready dataset and keep these requirements:
   - filter out active loans (`loan_status_r == -1`)
   - train/validate only on labeled rows (`0` and `1`)
   - derive `hdgc` and `hdbc` from geographic cluster distance features
   - train gradient boosting and random forest candidates
   - calibrate probabilities with isotonic regression
   - choose threshold using ROC
   - score the active set and export artifacts
4. Export the final handoff bundle to the workspace output or ML-Ops directory as configured by the model config.

## Recommended next-session restart sequence

```bash
cd /home/rajiv/programming/kmds_migration/sba_migration
source .venv/bin/activate

# If needed
init-workspace
location-helper .dataset-bootstrap
bootstrap-config

# Prepare the data
# notebooks/clean_sba_dataset.ipynb
# notebooks/clustering_feature_derivation.ipynb
# notebooks/feature_advisor_sba_example.ipynb

# Validate featurization output
ls data/featurization

# Run the local SBA modeling workflow from this workspace
```

## Notes

- Keep the modeling work anchored to the local workspace instead of the external `kmds-modeling` repo.
- The active-set scoring step is a key requirement: unlabeled rows are not used in training but must be scored after the model is tuned.
- If runtime issues appear, start by checking the active Python environment, the installed package, and the path in `model_config.yaml`/`config.yaml`.
- Treat `agent_documents/` as the canonical requirements/reference set for this migration.

## Stand by

This workspace is ready to resume from the notebook + featurization + local-modeling path. If you want, the next step can be to validate the SBA data files, run the feature pipeline, or start the modeling implementation from the current state.
