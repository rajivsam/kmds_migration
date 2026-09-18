# SBA Loan Classification

## Problem statement

The U.S. Small Business Administration (SBA) publishes loan-level performance data on a regular schedule, covering loans that are paid off, charged off, or still active. Because the SBA guarantees a substantial share of the portfolio, default prediction is an important risk-management problem affecting lending policy, portfolio monitoring, and operational planning. The dataset is strongly imbalanced, with far more paid-off loans than charged-off loans, which makes classification both practically relevant and methodologically challenging.

## Dataset and scope

This case study uses the SBA loan portfolio data processed through the KMDS migration workflow. The raw data are first normalized and cleaned using the dd-parser-cleaner pipeline, and the structured output is then used for downstream modeling. The problem is framed as a supervised binary classification task in which the historical portfolio is used to develop a default-risk model, while active loans are reserved for scoring and monitoring.

The modeling scope is limited to the labeled historical subset for training and evaluation. Active loans are excluded from the model-fitting step and only scored after the final decision rule has been selected. This preserves the operational distinction between historical model development and portfolio monitoring for current loans.

## Preprocessing choices

The raw SBA records are cleaned and normalized before modeling so that the data are suitable for downstream feature engineering and tabular learning. The KMDS workflow records these preprocessing steps explicitly rather than treating them as incidental. This includes the data-cleaning and schema normalization steps provided by dd-parser-cleaner, along with the organization of the dataset into a consistent modeling table suitable for feature generation and experimentation.

The model-ready dataset retains the relevant borrower-level metadata and geographic fields needed for the risk analysis. The active-loan subset is held out before model training so that the final risk scores are derived from a portfolio that remains operationally distinct from the labeled training data.

## Feature engineering and representation choices

The solutioning process is grounded in human agency and domain-specific feature design. Geographic information is encoded into latitude and longitude features so that spatial structure in borrower risk can be captured. To create a compact and interpretable representation, the training data are partitioned into good and bad loan subsets, and clusters are learned within each subset. For each loan, the distance to the nearest good and bad cluster is computed, producing a similarity feature that captures how similar a loan is to historically good versus bad local patterns.

This yields a compact representation of default risk based on local geographic structure rather than a large and opaque feature set. In this way, the engineered features are both operationally meaningful and aligned with the underlying risk-management question.

## Modeling choices and why they were selected

For the predictive task, ensemble tree-based methods are a natural fit for tabular credit-risk data. The case study evaluates both bagging and boosting strategies, including gradient boosted trees and random forests. These models are appropriate because they perform well on tabular features with nonlinear interactions and are widely used in loan default prediction settings.

To improve calibration, the resulting probability estimates are refined using isotonic regression. The final operating threshold is selected on the validation set using the receiver operating characteristic curve. The resulting threshold is then used to score the held-out evaluation data and the active loan portfolio, producing risk estimates suitable for portfolio monitoring and management.

## Evaluation criteria

The evaluation is based on model discrimination and calibration rather than on a single thresholdless metric alone. The primary model assessment uses the validation set and ROC-based threshold selection to determine the decision boundary. This is an operationally relevant criterion because the goal is not only to rank risk but also to translate that ranking into actionable portfolio decisions.

The chosen threshold is then applied to score the held-out data and the active portfolio, producing a decision rule that is both auditable and relevant to risk review. This design keeps the modeling decision tied to stakeholder needs around portfolio monitoring and intervention.

## Key outputs

The key outputs of the SBA case study include the cleaned dataset, the featurized model-ready table, the engineered geographic similarity features, the trained ensemble models, the calibrated probability outputs, and the final thresholded risk scores for the active portfolio. The modeling artifacts are retained in the KMDS workspace so that preprocessing, feature engineering, model selection, and thresholding decisions remain traceable.

## Interpretation for stakeholders

This case study highlights the operational value of KMDS for reproducible credit-risk modeling. The framework makes preprocessing, feature engineering, calibration, and threshold selection explicit rather than implicit. As a result, the final predictions are not only statistically grounded but also reviewable by stakeholders who need to understand why a loan is flagged as higher risk and how the decision rule was selected.

The resulting risk scores are designed to support portfolio review and intervention planning rather than act as an autonomous or final credit decision. This aligns the model with the decision context in which it is used: a monitoring and early-warning system for active SBA loans.

## Design decisions that were revisited or changed

The key design choice in this case study is to keep the feature representation intentionally compact and interpretable. Instead of expanding the model with broad and opaque feature sets, the workflow emphasizes a small number of meaningful features derived from borrower geography and historical loan outcomes. This supports both robustness and transparency in a high-stakes financial use case.

The project also distinguishes clearly between the historical labeled portfolio and the active scoring population. This prevents leakage between training and operational use and ensures that the final scores correspond to a real monitoring use case rather than a retrospective reconstruction of the same data used to fit the model.

## Links to notebooks / scripts / outputs

- Notebook: notebooks/clean_sba_dataset.ipynb
- Notebook: notebooks/clustering_feature_derivation.ipynb
- Notebook: notebooks/feature_advisor_sba_example.ipynb
- Requirement document: agent_documents/sba_modeling_requirements.md
- Problem framing document: agent_documents/sba_problem_framing_collab.md
- Configuration: model_config.yaml
- Featurization configuration: featurizer_config.yaml
- Modeling implementation: models/sba_example/
- Model-ready dataset: data/featurization/model_ready_numeric_data.csv
