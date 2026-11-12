# California Housing Regression with KMDS - A Step-by-Step Guide

This document describes the KMDS-based development workflow for the California Housing regression project. The project follows the same general repository and environment setup pattern as the SBA migration example, but the modeling task is different: the dataset is already clean and prepared, there is no featurization step to build, and the objective is to predict a continuous target using regression models.

The work is grounded in the project requirements in [../agent_documents/modeling_requirements.md](../agent_documents/modeling_requirements.md), which specify the modeling objective, train/validation/test split strategy, and the evaluation criteria.

## 1. Repository setup

Create a project repository for the California Housing effort and keep the modeling work inside this workspace. The project structure is intentionally similar to the SBA example, with the following important folders:

- [../data/](../data/)
- [../data_dictionary/](../data_dictionary/)
- [../documents/](../documents/)
- [../models/](../models/)
- [../notebooks/](../notebooks/)
- [../output/](../output/)
- [../agent_documents/](../agent_documents/)

This project already includes the prepared data file at [../data/california_housing_prepared.csv](../data/california_housing_prepared.csv), which is the canonical input for the modeling workflow.

## 2. UV project initialization

Because the KMDS ecosystem is designed to work with UV-based environments, initialize the Python project with UV and create a local virtual environment.

```bash
cd /home/rajiv/programming/kmds_migration/california_housing
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

This follows the same pattern as the SBA example: a local project environment, reproducible Python dependencies, and a workspace ready for KMDS utilities and model development.

## 3. Install KMDS and supporting dependencies

The project depends on the same class of tooling used across the KMDS migration work.

Relevant package setup from the project metadata:

```toml
[project]
name = "california-housing"
requires-python = ">=3.13"
dependencies = [
    "dd-parser-cleaner==1.2.0",
    "kmds-featurization>=0.4",
    "kmds-modeling>=0.3",
]
```

The California Housing task differs from the SBA example in one important way: no feature engineering or featurization pipeline is required because the dataset is already processed and ready to model. However, the project still uses the KMDS-style setup, repository conventions, and model-development discipline.

## 4. Workspace initialization and configuration bootstrap

The workspace is initialized as a standard KMDS project. The configuration file [../config.yaml](../config.yaml) is the working configuration for the repository and captures the dataset metadata and data-cleaning context.

This project already contains the prepared dataset and the dictionary file:

- [../data/california_housing_prepared.csv](../data/california_housing_prepared.csv)
- [../data_dictionary/california_housing_data_dictionary.csv](../data_dictionary/california_housing_data_dictionary.csv)

The configuration is intentionally lightweight because the dataset is already clean and because the objective is regression rather than a complex featurization workflow. There is no need to run a custom feature-advisor workflow or create new derived spatial variables for this project.

## 5. Data dictionary and parser review

In the KMDS workflow, the data dictionary and parser output help establish dataset structure, attribute types, and metadata quality. This dataset is already aligned with the project assumptions:

- all attributes are numeric
- the target is continuous
- there are multiple geographic observations and therefore likely heterogeneity
- the dataset is already cleaned and prepared

That means the project moves quickly from configuration to modeling, unlike the SBA example where featurization and geographic clustering were central to the implementation.

## 6. Clean dataset and data prep review

The prepared dataset and the cleaned duplicate are both present in the workspace:

- [../data/california_housing_prepared.csv](../data/california_housing_prepared.csv)
- [../data/dd_cleaner/california_housing_prepared_clean.csv](../data/dd_cleaner/california_housing_prepared_clean.csv)

This confirms that the "data engineering" stage has already been completed and the modeling phase can begin directly. In other words, the project follows the same KMDS structure but skips the heavy featurization layer because that work was already done upstream.

The schema is straightforward:

- MedInc
- HouseAge
- AveRooms
- AveBedrms
- Population
- AveOccup
- Latitude
- Longitude
- MedHouseVal

The target variable is `MedHouseVal`, while the remaining fields are numeric predictors.

## 7. Modeling requirements and workflow

The project requirements in [../agent_documents/modeling_requirements.md](../agent_documents/modeling_requirements.md) specify the essential modeling contract:

- use a real-world cross-sectional dataset
- all attributes are numeric
- the dataset spans multiple geographies and shows heterogeneity
- no featurization is needed because the data are already prepared
- compare regression models
- use MSE as the loss function
- create train, validation, and test sets
- use the validation set for hyperparameter tuning
- tune parameters so that the train and validation errors are as close as possible
- report the hold-out performance on the test set

This is conceptually similar to the SBA example in terms of KMDS setup and discipline, but it is a more direct supervised learning problem: the work is focused on model selection, validation tuning, and final hold-out evaluation rather than feature engineering or domain-specific transformations.

## 8. Model candidates

The project uses the two requested candidate models:

1. Gradient boosted trees
2. Random forest

These are standard regression baselines for this type of tabular dataset and are well suited to nonlinear relationships between the housing features and median home value.

## 9. Train, validation, and test split

The data were split into three partitions to match the modeling requirement:

- training set: 70%
- validation set: 15%
- test set: 15%

The split was performed with a fixed random seed so the evaluation is reproducible.

This pattern mirrors the SBA workflow, where the modeling step reads clean feature data and uses a held-out validation set for model choice. In this project, however, there is no second stage of featurization after the split, because the dataset is already in its final numerical form.

## 10. Validation-based tuning and model selection

The validation set is used to compare candidate hyperparameter options and select the configuration that balances:

- low validation MSE
- low train MSE
- a small gap between train and validation error

This is consistent with the requirement that train and validation error should be as close as possible. The chosen configuration therefore balances predictive power with generalization.

## 11. Final model selection and performance

The best model was the gradient boosting regressor with the following tuned parameters:

- n_estimators = 500
- learning_rate = 0.05
- max_depth = 3
- subsample = 0.9

The final validation and hold-out results were:

- train MSE: 0.2034
- validation MSE: 0.2610
- train/validation gap: 0.0575
- test MSE: 0.2299
- test R²: 0.8261

This indicates the model captures a substantial portion of the variance in median house value while remaining reasonably stable across train and validation behavior.

The random forest regressor was also evaluated as a candidate, but the gradient boosting model was preferred because it delivered stronger validation performance with a smaller train/validation discrepancy.

## 12. KMDS knowledge graph generation with the helper utility

The project also incorporates the KMDS knowledge graph helper workflow, which ingests repository artifacts and creates a structured project knowledge graph from the project summary and model outputs. This is the same conceptual pattern used in the broader KMDS ecosystem for turning repository artifacts into a graph-based representation of the work.

The helper utility expects a repository-style layout with folders such as:

- `documents/`
- `notebooks/`
- `data_dictionary/`
- `output/`
- `models/`

For this California Housing project, the helper was run against the workspace root and given the project output artifacts that summarize the modeling work. The command used was:

```bash
cd /home/rajiv/programming/kmds-data-helper
uv run kmds-kb --workspace /home/rajiv/programming/kmds_migration/california_housing --project-file /home/rajiv/programming/kmds_migration/california_housing/project_knowledge_graph.xml --mode auto
```

This utility scans the expected workspace structure, discovers the generated helper JSON output, and writes a KMDS ontology-style knowledge graph to the project file:

- [../project_knowledge_graph.xml](../project_knowledge_graph.xml)

The helper output artifacts used for the graph generation were generated as part of the project workflow:

- [../output/full_service_report.json](../output/full_service_report.json)
- [../output/kmds_summary.json](../output/kmds_summary.json)

These files summarize the project context, evaluation design, and performance findings, which are then represented in the KMDS graph as exploratory observations and workflow-level metadata. In this project, the generated graph includes the modeling objective, the regression setting, the selected model choice, and the performance summary of the tuned gradient boosting model.

This step is useful because it gives the repository a machine-readable understanding of the project structure and the modeling decisions taken, making the project easier to query, inspect, and integrate with downstream KMDS tooling.

## 13. Output and artifact generation

The modeling workflow writes the key artifacts to the project output folder:

- [../output/california_housing_model_metrics.json](../output/california_housing_model_metrics.json)
- [../output/gradient_boosting_california_housing_model.pkl](../output/gradient_boosting_california_housing_model.pkl)

The training script that produced these artifacts is here:

- [../models/train_california_housing_model.py](../models/train_california_housing_model.py)

The project also includes a KMDS knowledge graph generated using the helper utility:

- [../project_knowledge_graph.xml](../project_knowledge_graph.xml)

## 14. Why this project is similar to the SBA example

Even though the data science task is different, the KMDS workflow remains structurally similar to the SBA migration example:

- a standard project repository and configuration layout
- a clean, prepared dataset that becomes the modeling input
- a modeling contract defined through project documentation and agent instructions
- validation-driven model selection
- reproducible outputs under a project-level `output/` directory
- a final model bundle that is ready for reporting and downstream use

The principal difference is that the California Housing task did not require feature engineering or featurization. The data quality and preprocessing work were already completed upstream, so the modeling phase could focus directly on candidate selection, tuning, and evaluation.

## 15. Final project summary

This project demonstrates a disciplined KMDS-aligned workflow for a tabular regression benchmark where the data is already processed, numeric, and ready for supervised learning. The setup mirrors the SBA project’s repository conventions and modeling rigor, without the geospatial featurization step that was central to the SBA use case.

The practical outcome is a tuned gradient boosting regressor that performs well on the hold-out test set and provides a clean, reusable benchmark for future work on this dataset.
