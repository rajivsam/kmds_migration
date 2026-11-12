# Project Initialization Helper

This file captures the current workspace setup and the commands needed to resume the California Housing regression task.

## Project context

- Repository/workspace: `california_housing`
- Primary use case: regression on a real-world cross-sectional dataset with many numeric attributes and geographic heterogeneity
- Dataset status: already cleaned and prepared; no additional featurization step is needed
- Candidate models: gradient boosted trees and random forest
- Objective: minimize MSE and report hold-out error on a test set
- Split strategy: create train, validation, and test sets; use validation to tune model parameters
- Model selection rule: tune parameters so train and validation error are as close as possible

## Current stop point

- The project is already bootstrapped as a standard Python workspace under this folder.
- The prepared dataset is available in `data/` and is suitable for direct modeling.
- The authoritative requirements for this task are in `agent_documents/modeling_requirements.md`.
- This workspace should remain focused on the California Housing regression workflow rather than the SBA migration workflow.

## Important files

- `README.md` — project overview and workflow summary
- `config.yaml` — workspace-level project configuration
- `pyproject.toml` — project metadata and Python dependency setup
- `data/california_housing_prepared.csv` — prepared dataset for modeling
- `data/dd_cleaner/california_housing_prepared_clean.csv` — cleaned data artifact
- `data_dictionary/california_housing_data_dictionary.csv` — attribute schema and descriptions
- `agent_documents/modeling_requirements.md` — task specification for the regression benchmark
- `models/` — place for model training code and trained artifacts
- `output/` — final metrics, evaluation artifacts, and model outputs
- `notebooks/` — optional exploratory or validation notebooks

## Environment setup

```bash
cd /home/rajiv/programming/kmds_migration/california_housing
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

If the environment already exists:

```bash
cd /home/rajiv/programming/kmds_migration/california_housing
source .venv/bin/activate
```

## Recommended modeling workflow

1. Load the prepared California Housing dataset.
2. Confirm that all attributes are numeric and that no additional feature engineering is required.
3. Separate the target from predictors.
4. Create a train, validation, and test split.
5. Train the candidate models:
   - gradient boosted trees
   - random forest
6. Use MSE as the training and evaluation loss.
7. Tune hyperparameters on the validation set.
8. Prefer parameter combinations where train and validation error are similar, as close as possible.
9. Freeze the best configuration and evaluate on the hold-out test set.
10. Report final test-set error and save the trained model and metrics to `output/`.

## Implementation constraints

- Use a standard regression objective with MSE.
- Do not perform a second or hidden data split during model training if the dataset is already prepared.
- Use the validation set for model selection and tuning.
- Keep the train/validation gap as small as possible while avoiding overfitting.
- Keep all modeling work in this local workspace.
- Save final results in a reproducible, reviewable form under `output/`.

## Example starter commands

```bash
cd /home/rajiv/programming/kmds_migration/california_housing
source .venv/bin/activate
python - <<'PY'
import pandas as pd
from pathlib import Path
path = Path('data/california_housing_prepared.csv')
if path.exists():
    df = pd.read_csv(path)
    print(df.shape)
    print(df.head())
    print(df.dtypes.head())
else:
    print('Prepared dataset not found')
PY
```

## Modeling objective statement

This is a regular regression task on a real-world cross-sectional dataset. All attributes are numeric, the data span multiple geographies, and the distribution is expected to have heterogeneity. Because the dataset is already clean and prepared, no additional featurization is needed. The model candidates are gradient boosted trees and random forest. Use MSE as the loss, create train, validation, and test splits, and use the validation set to tune the model parameters. The tuning objective is to keep the training and validation error similar, and the final evaluation should report the hold-out error on the test set.

## Stand by

This workspace is ready to resume the California Housing modeling workflow. The next step can be to inspect the prepared dataset, create the train/validation/test split, tune the candidate models, and report the final test-set MSE.
