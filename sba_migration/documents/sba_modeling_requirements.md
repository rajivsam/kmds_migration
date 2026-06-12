# SBA Modeling Requirements

## Purpose
This document summarizes the SBA modeling pipeline requirements for the KMDS `kmds-modeling` framework. It is intended to capture the exact solution approach before implementation.

## Data source
- Use `featurization.notebook_utils` to resolve the featurization workspace and load `model_ready_df`.
- The source dataset is the KMDS model-ready export from featurization.
- The notebook `notebooks/clustering_feature_derivation.ipynb` confirms the dataset contains `loan_status_r`, `borrower_latitude`, and `borrower_longitude`.
- In the SBA dataset, `loan_status_r` values are:
  - `-1`: active loan subset
  - `0`: good loans
  - `1`: distressed / bad loans

## Training / validation split
- Remove the active loan subset (`loan_status_r == -1`) before training.
- The remaining dataset (`loan_status_r` in {0, 1}) is used for model development.
- Split the development dataset into training and validation sets.
- Use the same row indices for feature engineering and model development so that train/validation splits are preserved across both stages.
- Preserve index values within transformer operations to maintain data provenance.

## Feature engineering requirements
- Build a dedicated feature transformer within the framework.
- The transformer must be fit only on the training set and then applied to validation and active sets.
- Derive two geographic cluster-distance features from `borrower_latitude` and `borrower_longitude`:
  - `hdgc`: distance to the nearest good cluster
  - `hdbc`: distance to the nearest bad cluster
- Use the good subset (`loan_status_r == 0`) and bad subset (`loan_status_r == 1`) within the training set to learn separate cluster structures.
- Use haversine distance because the geographic attribute is latitude/longitude.
- Prefer spectral clustering and select the number of clusters using a spectral-gap statistic.
- If spectral clustering is not viable, fall back to density-based clustering using HDBSCAN.
- The derived features should be computed based only on the training subset cluster structure and then appended to the transformed feature table for validation and active rows.

## Model development requirements
- Train and compare two model families:
  - Gradient Boosted Trees
  - Random Forests
- Use probability output from each candidate model.
- Calibrate probability estimates using isotonic regression.
- Use ROC methodology to choose an operating threshold for classifying loans as good/bad.
- The validation set is used both for model selection and threshold tuning.

## Active set scoring
- After model tuning and calibration, transform the active set (`loan_status_r == -1`) with the learned cluster-based features.
- Score the active set with the calibrated model and the selected threshold.
- Output active-set probabilities and thresholded predictions for pick-up by downstream KMDS processes.

## ML-Ops artifact output
- Serialize all required artifacts into the ML-Ops export folder.
- At minimum, write:
  - the final trained model object
  - the fitted transformer pipeline
  - the probability calibrator
  - metadata describing: feature names, target variable, threshold, and model family
- Artifacts should be written in a standard format such that downstream KMDS tools can pick them up.

## Requirements summary
1. Load `model_ready_df` using `featurization.notebook_utils` from the featurization workspace.
2. Filter out active loans (`loan_status_r == -1`).
3. Split the remaining labeled dataset into training and validation.
4. Derive only two new geographic features: `hdgc` and `hdbc`.
5. Prefer spectral clustering with spectral-gap selection for good/bad geographic clusters.
6. Fall back to HDBSCAN if spectral clustering is not possible.
7. Train gradient boosting and random forest models.
8. Calibrate probabilities with isotonic regression.
9. Tune classification threshold using ROC.
10. Score the active set and serialize artifacts.

## Assumptions and clarifications
- The model-ready dataset is expected in the featurization workspace resolved by `build_notebook_resolver` from the notebook directory.
- The SBA problem is binary classification for `loan_status_r` with the active rows unlabeled.
- The model-development stage only uses labeled rows (`0` and `1`); active rows are held out for scoring only.
- Clustering is applied separately to the good and bad subsets in the training fold; derived distances are used as features for all rows.
- The final exported prediction should include both probability and binary decision using the tuned threshold.

## Implementation checkpoint
This document is the basis for implementation. Once agreed, the next step is to implement:
- `sba_modeling.SBAFeatureTransformer`
- training/validation split and dataset pipeline
- spectral/HDBSCAN cluster derivation
- gradient boosting and random forest candidates
- isotonic calibration
- active set scoring and artifact serialization
