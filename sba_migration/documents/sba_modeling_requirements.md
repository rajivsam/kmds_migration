# SBA Modeling Requirements

## Prologue: Why this is the recall-first screener design

The project objective is to identify at-risk SBA loans early enough to support intervention while remaining faithful to the data available in the repository. The project explored cascading models and utility-based action rules, but the positive class is sparse and the available data does not support a stable second-stage model or a reliable loan-level economic decision rule.

In particular:

- distressed outcomes are a small minority of labeled loans;
- the dataset does not provide sufficiently rich repayment schedules, residual exposure, servicing costs, or fee information for a defensible utility calculation;
- traditional in-model feature selection is unstable under the current sparsity and column distributions;
- a second-stage or utility-tuned model would introduce substantial proxy error and leakage risk.

The selected design is therefore a recall-oriented screening pipeline with:

1. a calibrated Stage-1 default-probability model;
2. Stage-2 threshold tuning on the validation set using cumulative gains, lift, and the elbow method; and
3. Stage-3 evaluation and active-loan scoring with that threshold frozen.

## Purpose

This document defines the selected SBA modeling approach for the KMDS `kmds-modeling` framework. The model estimates a calibrated default probability for each loan. Stage 2 converts that score into an operational screening cutoff using the validation gains curve. The cutoff is selected without using the test or active sets.

## Data source and target

- Use `featurization.notebook_utils` to resolve the featurization workspace and load the model-ready dataset.
- Use the KMDS model-ready export as the source dataset.
- Treat the problem as binary classification for labeled loans:
  - `loan_status_r == 0`: good loan;
  - `loan_status_r == 1`: distressed or defaulted loan;
  - `loan_status_r == -1`: active, unlabeled loan.
- Remove active rows before model training, validation, and test evaluation.
- If `dataset_partition` is present, use it as the canonical split source:
  - `train`
  - `validation`
  - `test`
  - `active`
- Do not create another random split when the canonical partition is available.

## Feature screening requirement

Traditional feature selection is not required and should not be added to the modeling pipeline. The low positive-class density makes such selection unreliable in this dataset.

Use the five predictor columns selected by the [imbalanced feature screener tool](https://github.com/rajivsam/imbalanced_feature_screener/tree/master):

- `initialinterestrate`
- `bankcity`
- `approvaldate`
- `terminmonths`
- `bankname`

These columns are the fixed screening feature set for this baseline. `loan_status_r` and `dataset_partition` are used as target and split metadata, respectively, and are not model predictors.

The preprocessing pipeline must still:

- fit preprocessing only on the training split;
- parse and transform `approvaldate` into deterministic numeric representations;
- impute missing predictor values using training-derived values;
- encode categorical fields such as `bankcity` and `bankname` consistently across all splits; and
- reject the scoring run if a required predictor is missing.

Do not silently add engineered geographic, loan-age, balance, or utility features to this baseline. Any future change to the fixed five-feature set must be justified with a rerun of the feature screener and recorded as a versioned requirements change.

## Stage 1: Train and calibrate the ranking model

### Candidate model families

Train and compare:

- Gradient Boosted Trees; and
- Random Forests.

Fit candidate models only on the canonical training split. Each candidate must emit a probability-like score. Calibrate the selected or candidate model probabilities with isotonic regression using training-derived calibration data according to the project's model-fitting convention; validation rows must remain available as untouched inputs for Stage-2 tuning.

The Stage-1 output required for Stage 2 is a calibrated `p_default` score for every validation loan, along with its loan identifier and true `loan_status_r`.

## Stage 2: Tune the review cutoff on validation data

Stage 2 converts operational review capacity into a frozen risk threshold. It uses only Stage-1 outputs and labels from the held-out validation split. The test and active splits must not influence model, calibration, elbow, percentile, or score-threshold selection.

### Score and rank

For the calibrated Stage-1 model:

1. Score every validation loan and store `p_default`.
2. Sort loans by `p_default` in descending order.
3. Use a deterministic tie-breaking rule based on a stable loan identifier, while recording the policy used for ties.
4. Define review cutoffs at a documented resolution, with percentiles as the default and deciles allowed when validation size makes percentiles unstable.

### Build the gains and lift table

At every evaluated cutoff `k%`, calculate:

- **Population reviewed:** the percentage of validation loans in the ranked prefix.
- **Defaults captured:** the count and percentage of all true validation defaults in the prefix.
- **Precision at `k%`:** the share of reviewed loans in the prefix that are true defaults.
- **Cumulative gains:** `100 * defaults_in_top_k / total_validation_defaults`. This is recall at `k%`.
- **Lift at `k%`:** `cumulative_gains(k%) / k%`, with gains and population expressed on the same percentage scale.

Plot cumulative gains and lift against the percentage of the validation population reviewed. The gains chart must include the random-selection baseline and visually identify the selected `k%` elbow.

### Select the elbow cutoff

The default cutoff selection method is **elbow-driven**. Select the point where the cumulative gains curve begins to flatten, so that additional reviewed loans capture materially fewer additional defaults.

The elbow calculation must be reproducible rather than chosen solely by visual judgment. Use an elbow or knee method applied to the validation gains curve, such as maximum curvature or maximum deviation from the line joining the curve endpoints. Persist:

- the detected elbow population percentage `k%`;
- the cumulative gains and lift at that point;
- the marginal gain from the preceding cutoff;
- the exact calibrated `p_default` at the boundary; and
- the detection parameters and method version.

If a documented review-capacity constraint exists, a capacity-driven cutoff may override the elbow cutoff. In that case, record the known capacity, the capacity-derived `k%`, and the reason for the override. Do not tune `k%` using test performance.

### Convert `k%` to a frozen threshold

- When loans are scored as a complete batch, the operational rule may select the top-ranked `k%`.
- When loans are scored individually or over time, persist the calibrated `p_default` at the selected `k%` boundary as `p_threshold`.
- For score ties at the boundary, use the documented deterministic policy. The policy must be identical during test and active scoring.
- Freeze `k%`, `p_threshold`, tie handling, and the selected Stage-1 model before evaluating the test split.

## Stage 3: Unbiased evaluation and scoring

### Held-out test evaluation

Apply the frozen Stage-1 model and Stage-2 cutoff unchanged to the test set:

- report the percentage and count of loans selected for review;
- report precision, recall, PR-AUC, and balanced accuracy;
- report cumulative gains and lift at the frozen `k%`;
- compare realized test recall with the validation gains at the selected cutoff; and
- do not retune the model or threshold after observing test results.

### Active-loan scoring

After test evaluation:

- score the active split with the frozen calibrated model;
- apply the frozen `k%` rank rule for batch scoring or the frozen `p_threshold` for individual scoring;
- export `p_default`, the threshold or percentile decision, and the final review flag for downstream triage;
- keep active loans separate from training, validation, and evaluation; and
- treat the output as a recall-oriented review screen, not a financial utility decision.

## ML-Ops artifact output

Serialize the required artifacts into the ML-Ops export folder. At minimum, write:

- the final trained model object;
- the fitted preprocessing transformer;
- the probability calibrator;
- the fixed Stage-2 percentile and score-threshold metadata;
- elbow-method parameters and the selected cutoff rationale;
- the validation gains/lift table and gains/lift charts;
- the exact five-feature metadata and feature-screener version or source reference;
- model-family selection and performance metrics; and
- the loan-level test or active action rule details.

Artifacts must be sufficient for downstream KMDS tools to reproduce the frozen scoring behavior without rerunning Stage-2 selection.

## Requirements summary

1. Load the model-ready dataset from the featurization workspace.
2. Use `dataset_partition` as the canonical split source when present.
3. Use only `initialinterestrate`, `bankcity`, `approvaldate`, `terminmonths`, and `bankname` as predictors.
4. Do not add a traditional feature-selection step.
5. Fit preprocessing, gradient boosted trees, and random forests on the training split.
6. Calibrate model probabilities, producing Stage-1 `p_default` scores.
7. Build validation-only cumulative gains and lift curves from ranked validation scores.
8. Select `k%` with the reproducible elbow method unless a documented capacity constraint overrides it.
9. Convert the selected `k%` into a frozen calibrated score threshold for individual scoring.
10. Apply the frozen model and cutoff unchanged to the test and active splits.
11. Export the gains/lift evidence, threshold metadata, metrics, and reproducible model artifacts.

## Assumptions and clarifications

- The model-ready dataset is expected in the featurization workspace resolved by the project tooling.
- Model development uses only labeled good and distressed rows.
- Active rows remain unlabeled and are scored only after model and threshold selection are frozen.
- The fixed feature screen reflects the external imbalanced feature screener result, not a feature-importance ranking learned by the Stage-1 model.
- Lift is undefined at `0%`; the gains/lift table therefore starts at the first nonzero evaluated cutoff.
- A capacity-driven override is an operational exception, not an alternative model-training objective.

## Implementation checkpoint

This document is the basis for implementation alignment and result evaluation. Implementation should cover:

- loading the canonical train, validation, test, and active partitions;
- preprocessing the fixed five-feature predictor set;
- training and calibrating candidate Stage-1 models;
- validation-only gains and lift table generation;
- reproducible elbow detection and cutoff persistence;
- frozen test-set evaluation and active-set scoring; and
- artifact serialization and reporting.
