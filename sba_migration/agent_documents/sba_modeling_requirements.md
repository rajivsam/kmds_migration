# SBA Modeling Requirements

## Purpose
This document captures the final SBA modeling approach for the KMDS `kmds-modeling` framework. The selected design is a single-stage recall-first screening model: it ranks probability of default and selects the final operating threshold to maximize recall for downstream review, with the understanding that richer loan-level balance and cost data could be used later to support a utility-based operating policy.

## Data source
- Use `featurization.notebook_utils` to resolve the featurization workspace and load the model-ready dataset.
- The source dataset is the KMDS model-ready export from featurization.
- The dataset contains `loan_status_r`, `borrower_latitude`, `borrower_longitude`, and the loan amount signal `grossapproval`.
- In the SBA dataset, `loan_status_r` values are:
  - `-1`: active loan subset
  - `0`: good loans
  - `1`: distressed / bad loans

## Training / validation split
- Remove the active loan subset (`loan_status_r == -1`) before model development.
- Use the remaining labeled rows (`loan_status_r` in {0, 1}) for training and validation.
- If `dataset_partition` is present in the model-ready data, use it as the canonical split source:
  - `train`
  - `validation`
  - `test`
  - `active`
- Do not create a second random split inside the modeling package when the canonical partition already exists.

## Feature engineering requirements
- Build a dedicated feature transformer within the framework.
- Fit the transformer only on the training set and apply it to validation, test, and active rows.
- Derive two geographic cluster-distance features from `borrower_latitude` and `borrower_longitude`:
  - `hdgc`: distance to the nearest good cluster
  - `hdbc`: distance to the nearest bad cluster
- Use the good subset (`loan_status_r == 0`) and bad subset (`loan_status_r == 1`) within the training set to learn cluster structure.
- Use haversine distance because the geographic attribute is latitude/longitude.
- Prefer spectral clustering and use a spectral-gap statistic to pick cluster count when feasible.
- If spectral clustering is not viable, fall back to density-based clustering using HDBSCAN.
- The derived features should be computed from training-only cluster structure and then appended consistently to validation, test, and active rows.
- Create a loan-age / exposure feature named `loan_age_months` when the raw dates are available. Use `firstdisbursementdate` if present; when missing, fall back to `approvaldate`. If both are missing, use a conservative default of 24 months to keep the feature usable.
- Create an exposure-weighted utility feature named `default_utility_score` using the loan amount and the age-adjusted exposure term.

## Recall-first screening policy
The current operating policy is a single-stage recall-first screening design. The goal is to maximize the share of true defaults captured for downstream review rather than to optimize a business utility function based on loan-loss assumptions.

### Why this remains the default
- The available SBA data does not consistently provide the loan-payment, remaining-balance, payoff, and amortization fields needed for a precise expected-loss calculation.
- Without reliable loan-level cost and exposure data, a utility model is only a proxy and may be misleading.
- For this project, the reliable and defensible default is to prioritize recall so that the review queue is broad enough to capture likely distressed loans.

### Final threshold policy
- Tune the validation threshold to maximize recall while keeping precision at a usable level.
- Keep enough sensitivity to recover the largest practical share of true defaults for downstream review workflows.
- This is the project’s operating policy unless a future business requirement adds complete loan-level payment, balance, and cost information that supports a more precise utility model.

## Modeling design

### Primary classifier: recall-driven screening model
- The SBA model remains a single-stage classifier whose operating point is chosen to maximize recall for screening.
- The model is still calibrated with probability outputs and tuned on validation data.
- The threshold policy is chosen to favor coverage of likely defaulting loans rather than a business-loss optimization based on incomplete cost information.

### Candidate models
- Train and compare the candidate model families:
  - Gradient Boosted Trees
  - Random Forests
- Use calibrated probability outputs for each candidate model.

### Calibration and threshold tuning
- Calibrate model probabilities with isotonic regression.
- Evaluate candidate models on validation data using PR-AUC, precision, recall, and F2.
- Tune the decision threshold on the validation set to maximize recall while keeping precision usable for review.
- Final operating points emphasize screening coverage and should not pretend to be a precise loss-optimization policy without complete loan-cost data.

## Model development requirements
- Read the model-ready source file and partition by `dataset_partition` when present.
- Use the canonical labeled data for training and evaluation:
  - train set for fitting
  - validation set for threshold selection
  - test set for final reporting
  - active set for scoring only after tuning
- Train the final classifier on the full labeled training set using the recall-first decision policy.
- Select the final threshold based on validation performance with recall as the primary objective.
- Report precision, recall, PR-AUC, balanced accuracy, F2, and Brier score on the test set using the final threshold.
- Use the final summary to explain that richer loan-balance and cost data could support a later utility-based policy.

## Active set scoring
- Transform the active set (`loan_status_r == -1` and `dataset_partition == "active"`) with the learned cluster-based features.
- Score the active set with the final model.
- Output the calibrated probability and final binary decision for the active population.
- Final reporting should clearly distinguish:
  - model score distribution
  - recall-first threshold-selected positive predictions
  - test-set performance summary

## ML-Ops artifact output
- Serialize all required artifacts into the ML-Ops export folder.
- At minimum, write:
  - trained model object
  - fitted transformer pipeline
  - calibrator
  - threshold metadata
  - model family and feature metadata
  - validation performance metrics
- Artifacts should be written in a standard format so downstream KMDS tools can consume them.

## Requirements summary
1. Load the model-ready dataset from the featurization workspace.
2. Use `dataset_partition` as the canonical split source when present.
3. Do not create a second random split inside the modeling package if the partition is already available.
4. Build and apply the geographic feature transformer on the training set and then to validation, test, and active rows.
5. Derive the two geographic features: `hdgc` and `hdbc`.
6. Add `loan_age_months` when it is available and keep the date fallback rule (`firstdisbursementdate` -> `approvaldate` -> 24 months default).
7. Prefer spectral clustering with spectral-gap selection for good/bad geographic clusters; fall back to HDBSCAN if needed.
8. Train the final model as a recall-first screening classifier.
9. Tune the threshold to maximize recall while keeping precision usable for review.
10. Score the active set with the final model and emit the final defaulting decision.
11. Serialize the trained model, calibrator, transformer, and metrics as ML-Ops artifacts.
12. Note that a later utility-based policy may be introduced only when richer loan-balance and cost data become available.

## Assumptions and clarifications
- The model-ready dataset is expected in the featurization workspace resolved by the project tooling.
- The SBA problem is binary classification for `loan_status_r` with active rows unlabeled.
- Model development uses only labeled rows (`0` and `1`) for training and evaluation.
- Active rows remain separate and are scored only after model tuning.
- The selected design is a single-stage recall-first model for this project phase.
- If `firstdisbursementdate` is missing, the fallback is `approvaldate`; if both are missing, use a conservative default age assumption to keep the screening model operational.
- A future utility-based policy can be revisited only if reliable loan-balance, payment, and cost information is available in the data.eep the utility feature valid.
## Implementation checkpoint
This document is the basis for implementation. Once agreed, the next step is to implement:
- `sba_modeling.SBAFeatureTransformer`
- training/validation/test partitions and dataset pipeline
- single-stage utility-based model training and calibration
- validation-time threshold tuning for utility-based operating point
- active-set scoring and artifact serialization
