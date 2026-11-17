# SBA Modeling Requirements

## Prologue: Why this is the recall-first screener design
The original project objective was to build an operational SBA intervention model that could identify at-risk loans early enough to support action, while staying faithful to the data actually available in the project. We explored two stronger business-framed alternatives before settling on the final design:

1. A cascading / two-stage screening design in which a first model filters the population and a second stage refines the candidate set using a utility-based rule.
2. A loan-level utility-threshold policy that converts a calibrated default probability into an action decision using expected payback versus expected default loss.

These approaches are reasonable in principle, and they were worth testing as a modeling experiment. However, in this SBA dataset the positive class is too sparse and the available features are not rich enough to support a stable second-stage model or a reliable economic decision rule without introducing substantial proxy error and leakage risk. In particular:

- the distressed outcomes are a small minority of labeled loans;
- the available data does not include robust loan-by-loan repayment schedules, true residual exposure, actual servicing costs, or SBA fee schedules;
- a utility-driven or cascading design is therefore not well supported by the current feature set and would effectively be learning from proxies rather than true economic behavior;
- without materially better features, the model is not able to produce a stable and defensible action target that is both interpretable and operationally useful.

This is the reason the project settles on the original recall-maximizing screener design: a single-stage classifier trained on the available surveillance features, with a validation threshold chosen to maximize recall and recover as many true distressed loans as possible. This design is the best fit for the current data quality and feature availability.

## Purpose
This document captures the selected SBA modeling approach for the KMDS `kmds-modeling` framework. The chosen design is a single-stage recall-maximizing screener, not a utility-tuned cascade. The model estimates the default probability for each loan and then applies a threshold selected on the validation set to maximize recall subject to the operational constraints of the available data.

## Data source
- Use `featurization.notebook_utils` to resolve the featurization workspace and load the model-ready dataset.
- The source dataset is the KMDS model-ready export from featurization.
- The dataset contains the existing loan outcome, location, and amount features required for modeling, and it must also include the newly required loan-age and residual-balance attributes.
- In the SBA dataset, `loan_status_r` values are:
  - `-1`: active loan subset
  - `0`: good loans
  - `1`: distressed / bad loans

## Feature engineering requirements
- Build a dedicated feature transformer within the framework.
- Fit the transformer only on the training set and apply it to validation, test, and active rows.
- Keep the geographic cluster-distance features from `borrower_latitude` and `borrower_longitude`:
  - `hdgc`: distance to the nearest good cluster
  - `hdbc`: distance to the nearest bad cluster
- Use the good subset (`loan_status_r == 0`) and bad subset (`loan_status_r == 1`) within the training set to learn cluster structure.
- Use haversine distance because the geographic attribute is latitude/longitude.
- Prefer spectral clustering and use a spectral-gap statistic to pick cluster count when feasible.
- If spectral clustering is not viable, fall back to density-based clustering using HDBSCAN.
- The derived features should be computed from training-only cluster structure and then appended consistently to validation, test, and active rows.
- Add a new loan-age feature named `loan_age` that represents the number of scheduled payments that should have been made. Use the following rule:
  - if `firstdisbursementdate` is available, compute the payment count from the difference between `asofdate` and `firstdisbursementdate`
  - else use `approvaldate`
  - if neither date is available, use a conservative fallback of 24 months
  - the value should be stored as an integer count of payment periods in the same unit used by the loan product schedule (monthly where available)
- Add a new balance feature named `estimated_balance` or `residual_amount`, whichever is available in the data. This is a required model feature because it represents the amount still exposed to loss or recovery.
- If neither balance field is present, construct a proxy using the remaining principal logic consistent with the loan age and term, so the feature remains available for training.
- Include `loan_age` and `estimated_balance` or `residual_amount` in both the training and scoring pipelines so the model sees both exposure and repayment age.

## Selected operating design: single-stage recall-maximizing screener
The final operating policy is to keep the modeling problem as a standard supervised default-risk screen, tuned to recall rather than a utility-derived action threshold.

### Decision goal
The primary goal is to recover the largest possible fraction of truly distressed loans while keeping the model transparent and consistent with the available data. The project does not currently have enough loan-level economic detail to justify a financially optimized per-loan thresholding rule. The screening model should therefore maximize recall on the validation set before the final test evaluation.

### Validation thresholding rule
- Train the candidate models on the canonical train split.
- Calibrate probability outputs using isotonic regression.
- On the validation set, sweep candidate thresholds over the calibrated probability scores.
- Select the threshold that maximizes recall while respecting the project’s minimum operating constraints and the practical actionability of the resulting positive set.
- Freeze that threshold before test-set evaluation.
- Do not replace the threshold with a utility-derived formula unless a richer and more reliable economic feature set is later added to the project.

This is the chosen operating design because it remains faithful to the actual modeling signal available in the data and because the existing feature set is too sparse for a stable utility-driven second-stage intervention policy.

## Training / validation split
- Remove the active loan subset (`loan_status_r == -1`) before training.
- The remaining dataset (`loan_status_r` in {0, 1}) is used for model development.
- If `dataset_partition` is present in the model-ready data, use it as the canonical split source:
  - `train`
  - `validation`
  - `test`
  - `active`
- Do not create a second random split inside the modeling package when the canonical partition already exists.

## Model development requirements
- Train and compare two model families:
  - Gradient Boosted Trees
  - Random Forests
- Use probability output from each candidate model.
- Calibrate probability estimates using isotonic regression.
- Use the validation set to select the threshold that maximizes recall and to compare candidate model behavior.
- Use the final, fixed threshold on the held-out test set for unbiased evaluation.
- Report the standard classification metrics, including precision, recall, PR-AUC, and balanced accuracy, alongside the final action count.

## Active set scoring
- After calibration, score the active set using the frozen screening threshold.
- Keep the active loan subset separate from training and evaluation.
- Export the scored active set with the model probability, threshold decision, and supporting loan-level attributes for downstream review.
- The active-set output is intended to support operational triage, not as a replacement for a richer economic decision model.

## Practical interpretation
This design is intentionally conservative: it maximizes the chance of catching the loans that matter most under the current feature set, while staying honest about the limits of the available data. The project explicitly recognizes that more complex cascade and utility-based approaches were explored, but the data is too sparse and too weakly specified for them to be the reliable default policy. The recall-first screener is therefore the correct production baseline for the current SBA migration.
e active set (`loan_status_r == -1` and `dataset_partition == "active"`) with the learned cluster-based features and the required loan-age/residual inputs.
- Score the active set with the calibrated model to obtain `p_default`.
- Apply the per-loan utility threshold to generate the final `action` flag for each active loan.
- Output active-set probabilities and utility-driven action flags for downstream KMDS review processes.

## ML-Ops artifact output
- Serialize all required artifacts into the ML-Ops export folder.
- At minimum, write:
  - the final trained model object
  - the fitted transformer pipeline
  - the probability calibrator
  - threshold metadata and loan-level action rule details
  - feature metadata including `loan_age` and `estimated_balance` / `residual_amount`
  - model family and performance metrics
- Artifacts should be written in a standard format such that downstream KMDS tools can pick them up.

## Requirements summary
1. Load the model-ready dataset from the featurization workspace.
2. Use `dataset_partition` as the canonical split source when present.
3. Do not create a second random split inside the modeling package if the partition is already available.
4. Build and apply the geographic feature transformer on the training set and then to validation, test, and active rows.
5. Derive the geographic features: `hdgc` and `hdbc`.
6. Add `loan_age` to the model feature set using the date-derived payment-count rule.
7. Add `estimated_balance` or `residual_amount` to the model feature set, using a real field when available and a proxy when not.
8. Train gradient boosting and random forest models.
9. Calibrate probabilities with isotonic regression.
10. Compute the per-loan action threshold from the expected payback and default utilities.
11. Tag each loan as `1` when `p_default >= p_threshold` and `0` otherwise.
12. Score the active set using the utility-driven action rule and serialize the final artifacts.

## Assumptions and clarifications
- The model-ready dataset is expected in the featurization workspace resolved by the project tooling.
- The SBA problem is binary classification for `loan_status_r` with active rows unlabeled.
- Model development uses only labeled rows (`0` and `1`) for training and evaluation.
- Active rows remain separate and are scored only after model tuning and calibration.
- The final action rule is a loan-level utility policy based on `p_default`, the expected profit from repayment, and the expected loss from default.
- The financial cost proxy uses a notional guarantee-fee assumption of `3.5%` of principal so that default costs reflect a realistic SBA underwriting cost.

## Implementation checkpoint
This document is the basis for implementation. Once agreed, the next step is to implement:
- `sba_modeling.SBAFeatureTransformer`
- training/validation split and dataset pipeline
- geographic clustering and new utility inputs (`loan_age`, `estimated_balance` / `residual_amount`)
- gradient boosting and random forest candidates
- isotonic calibration
- utility-based decision rule generation for active-set action tagging
- artifact serialization and reporting
