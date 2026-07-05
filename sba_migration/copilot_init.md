# Copilot Init

This file records the exact initialization and modeling workflow for the `sba_migration` workspace so the process can be recreated consistently.

## Workspace initialization

1. Start in the `sba_migration` workspace.
2. Run workspace initialization steps in this order:
   - `init-workspace`
   - `location-helper .dataset-bootstrap`
   - `bootstrap-config`

These steps ensure the repository is pointed at the correct SBA workspace, the dataset metadata is bootstrapped, and the modeling config is initialized.

## Data preparation workflow

1. Clean the raw SBA dataset using the notebook:
   - `notebooks/clean_sba_dataset.ipynb`
2. Derive geographic clustering features using the notebook:
   - `notebooks/clustering_feature_derivation.ipynb`
3. Run the feature advisor example to inspect feature suggestions and decide on feature engineering:
   - `notebooks/feature_advisor_sba_example.ipynb`
4. Based on the advisor output, decide how to featurize the dataset and update the featurization pipeline.

## Featurization pipeline execution

1. Execute the chosen featurization pipeline in `featurization_scripts/`.
2. Confirm the output data is written to the workspace featurization output path, typically:
   - `data/featurization/featurized_data.csv`
   - `data/featurization/model_ready_numeric_data.csv`
3. Validate the dataset contains the expected modeling columns, including `loan_status_r` and geographic feature columns.

## Modeling workflow

1. Initialize on the documents under `agent_documents/` and read:
   - `agent_documents/agent_init_modeling.md`
   - `agent_documents/sba_modeling_requirements.md`
   - `agent_documents/sba_problem_framing_collab.md`
2. Use the local `models/sba_example/` implementation for the SBA modeling workflow.
3. Run the modeling pipeline from the `sba_migration` workspace, not from the separate `kmds-modeling` repo.
4. The modeling workflow should:
   - load `data/featurization/model_ready_numeric_data.csv`
   - filter out active loans (`loan_status_r == -1`)
   - train/validate on labeled rows only
   - derive `hdgc` and `hdbc`
   - train gradient boosting and random forest candidates
   - calibrate probabilities using isotonic regression
   - choose a threshold using ROC
   - score the active set and export artifacts

## Reproduce results next time

To reproduce the full flow next time:

1. Start with the same workspace and virtual environment.
2. Re-run the initialization steps if needed:
   - `init-workspace`
   - `location-helper .dataset-bootstrap`
   - `bootstrap-config`
3. Clean and prepare data with:
   - `notebooks/clean_sba_dataset.ipynb`
   - `notebooks/clustering_feature_derivation.ipynb`
   - `notebooks/feature_advisor_sba_example.ipynb`
4. Execute the featurization pipeline and verify the featurized output.
5. Run the local modeling workflow under `models/sba_example/`.
6. Use the `agent_documents/` files as the authoritative reference for the modeling approach and requirements.

## Important note

The modeling results should be generated from the local `sba_migration` workspace code, not from the separate `kmds-modeling` repo, unless the package is explicitly installed and configured to use this workspace.
