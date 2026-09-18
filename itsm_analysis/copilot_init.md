# ITSM Analysis Project Bootstrap

This workspace is already initialized and verified for the ITSM survival-analysis workflow.

## Project snapshot

- Workspace: `itsm_analysis`
- Goal: Kaplan-Meier analysis of ticket resolution times by support group
- Canonical output field: `survival_time_days`
- Legacy compatibility alias: `duration_days` (deprecated; retained only for older consumers)

## Authoritative project files

- README: `README.md`
- Data-prep notes: `agent_docs/data_prep_doc.md`
- Modeling summary: `documents/modeling_summary.md`
- Data-prep notebook: `notebooks/create_itsm_survival_pipeline.ipynb`
- Modeling notebook: `notebooks/create_itsm_survival_kaplan_meier_model.ipynb`
- Featurization logic: `featurization_scripts/featurization.py`
- Project config: `config.yaml`
- Featurizer config: `featurizer_config.yaml`

## Verified outputs currently in the workspace

- `data/dd_cleaner/itsm_ticket_survival_dataset.csv`
- `data/dd_cleaner/itsm_ticket_survival_km_summary.csv`
- `data/featurization/itsm_survival_model_ready_numeric_data.csv`
- `data/featurization/itsm_KM_data.csv`
- `data/featurization/itsm_ticket_survival_dataset.csv`
- `models/itsm_ticket_survival_km_summary.csv`
- `models/itsm_ticket_survival_km.png`

## Environment and startup

```bash
cd /home/rajiv/programming/kmds_migration/itsm_analysis
source .venv/bin/activate
```

If the environment needs reinstalling:

```bash
cd /home/rajiv/programming/kmds_migration/itsm_analysis
.venv/bin/python -m pip install --upgrade pip setuptools wheel
.venv/bin/python -m pip install -e .
.venv/bin/python -m pip install nbformat nbconvert nbclient ipykernel
```

## Reproduction sequence

```bash
cd /home/rajiv/programming/kmds_migration/itsm_analysis
source .venv/bin/activate

# 1) regenerate the survival dataset
.venv/bin/jupyter nbconvert --to notebook --execute --inplace notebooks/create_itsm_survival_pipeline.ipynb

# 2) regenerate the Kaplan-Meier model summary and plot
.venv/bin/jupyter nbconvert --to notebook --execute --inplace notebooks/create_itsm_survival_kaplan_meier_model.ipynb
```

## Important implementation note

The notebook and pipeline are aligned to the same canonical duration variable: `survival_time_days`.

Older or legacy references to `duration_days` should be treated as deprecated compatibility aliases only. The production workflow should use `survival_time_days` consistently to avoid schema drift between data preparation and the model.

## Final wrap-up

This project is in a good working state for KMDS-based incident survival analysis. The data-prep notebook, the model notebook, and the generated summary/plot artifacts are all aligned to the same workspace and are ready to resume or extend without reinitializing the whole project.
