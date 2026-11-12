# California Housing Regression Example

This project is a KMDS-style machine learning workflow for a California Housing regression task. It follows the same repository and modeling discipline described in the project development document at [documents/california_housing_development_example_full_doc.md](documents/california_housing_development_example_full_doc.md), but focuses on a direct supervised regression problem rather than a featurization-heavy classification workflow.

## Project objective

The goal is to predict `MedHouseVal` (median house value) from the available numeric housing features using a regression model. The dataset is already prepared and cleaned, so the workflow begins with modeling rather than a custom feature-engineering pipeline.

## Why this project exists

This workspace demonstrates how KMDS can be used for a tabular regression use case with a clean, ready-to-model dataset. The project keeps the same repository conventions as the broader KMDS migration examples:

- structured project folders for data, config, models, outputs, and documentation
- project metadata in `pyproject.toml`
- a local virtual environment for reproducible Python dependencies
- model selection driven by validation performance
- final outputs saved under `output/`

## Dataset and modeling context

The working dataset is:

- [data/california_housing_prepared.csv](data/california_housing_prepared.csv)

The data dictionary is:

- [data_dictionary/california_housing_data_dictionary.csv](data_dictionary/california_housing_data_dictionary.csv)

The project is built around a real-world cross-sectional tabular dataset with numeric predictors such as:

- `MedInc`
- `HouseAge`
- `AveRooms`
- `AveBedrms`
- `Population`
- `AveOccup`
- `Latitude`
- `Longitude`
- target: `MedHouseVal`

The modeling task uses a train/validation/test split and evaluates model performance using mean squared error (MSE). The validation set is used for tuning, and the test set is reserved for final evaluation.

## Candidate models

The project compares the following regression models:

1. Gradient boosted trees
2. Random forest

The tuning objective is to keep the training and validation errors close while maintaining strong generalization performance.

## Repository structure

```text
california_housing/
├── agent_documents/
├── config.yaml
├── data/
├── data_dictionary/
├── documents/
├── models/
├── notebooks/
├── output/
├── pyproject.toml
├── README.md
├── project_knowledge_graph.xml
└── .venv/
```

## Setup

Create the Python environment and install the project package:

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

## Dependency setup

The project metadata declares the required dependencies in [pyproject.toml](pyproject.toml):

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

The dataset is already cleaned and prepared, so no additional featurization step is required before model training.

## Recommended workflow

1. Load the prepared dataset from `data/california_housing_prepared.csv`.
2. Confirm that the predictors are numeric and the target is continuous.
3. Split the dataset into train, validation, and test sets.
4. Train the gradient boosting and random forest regressors.
5. Tune hyperparameters using the validation set.
6. Select the model with the smallest validation MSE while keeping train and validation error aligned.
7. Evaluate the final model on the hold-out test set.
8. Save metrics and model artifacts to `output/`.

## Output artifacts

This workflow writes the final project artifacts under [output/](output/):

- [output/california_housing_model_metrics.json](output/california_housing_model_metrics.json)
- [output/gradient_boosting_california_housing_model.pkl](output/gradient_boosting_california_housing_model.pkl)
- [output/full_service_report.json](output/full_service_report.json)
- [output/kmds_summary.json](output/kmds_summary.json)

The project also includes a generated knowledge graph at [project_knowledge_graph.xml](project_knowledge_graph.xml).

## Modeling summary

The project document identifies the tuned gradient boosting regressor as the preferred model. A representative result from the documented workflow is:

- train MSE: 0.2034
- validation MSE: 0.2610
- test MSE: 0.2299
- test R²: 0.8261

This indicates strong predictive performance while maintaining a reasonable train/validation gap and stable hold-out results.

## Related documentation

- [documents/california_housing_development_example_full_doc.md](documents/california_housing_development_example_full_doc.md)
- [agent_documents/modeling_requirements.md](agent_documents/modeling_requirements.md)
- [config.yaml](config.yaml)
- [models/train_california_housing_model.py](models/train_california_housing_model.py)

This project is intended as a direct, reproducible regression example within the KMDS ecosystem and serves as a benchmark for continuous-target modeling on a prepared, real-world dataset.
