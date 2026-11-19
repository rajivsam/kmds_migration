# Revised SBA Featurization Requirements

## Objective

This document defines a clear, modular featurization pipeline for the SBA migration workspace. The goal is to construct a final numeric training, validation, and test dataset that is safe for downstream modeling, uses the train split to fit all learned transformations, and preserves a single authoritative `dataset_partition` label for every row.

The featurization workflow is designed to align with the project requirements already captured in `agent_documents/test_train_split_rework.md`, the spatial design notes in `agent_documents/spatial_featurization_design.md`, and the benchmark logic in the imbalanced feature screener notebook reference.

## Reference baseline

The reference feature screening notebook is:

- https://github.com/rajivsam/imbalanced_feature_screener/blob/master/notebooks/feature_screener_sba.ipynb

The notebook demonstrates the raw SBA feature universe to evaluate, while explicitly removing post-outcome leakage fields such as:

- `loanstatus`
- `paidinfulldate`
- `chargeoffdate`
- `grosschargeoffamount`

The featurized modeling contract is capped at the five highest-ranked features in the screener report, in rank order:

1. `bankname`
2. `bankcity`
3. `initialinterestrate`
4. `bankstreet`
5. `terminmonths`

This top-five cap is used as the complete raw feature universe. Geospatial borrower features and clustering-derived features are outside this final contract and are therefore not exported to modeling.

## Core requirements

### 1. Canonical input contract

The featurization notebook must load the canonical SBA development partitions from `documents/dd_cleaner/`:

- `sba_user_cleaned_raw_training.csv`
- `sba_user_cleaned_raw_validation.csv`
- `sba_user_cleaned_raw_test.csv`

These files are the authoritative data source. The notebook must not re-split the dataset internally. It must instead preserve the row-level assignment already captured in the canonical persisted data and add or validate a single `dataset_partition` column that is used by modeling.

### 2. Leakage-safe candidate universe

The candidate and final feature set is restricted to the five ranked features listed above. `initialinterestrate` and `terminmonths` are numeric; `bankname`, `bankcity`, and `bankstreet` are categorical.

The notebook must explicitly remove or ignore leak-prone outcome-derived fields before encoding or modeling.

### 3. Train-first fit policy

All fit-based transformations must be learned using the training data only. The validation and test partitions are transformed using the learned parameters from train without refitting.

This includes categorical encoding and numeric missing-value imputation.

The implementation must enforce the rule:

- fit on train
- transform validation and test
- never refit on validation or test rows

### 4. Category encoding using M-estimate target encoding

The categorical variables in the selected feature set must be encoded using `category_encoders.MEstimateEncoder`.

This stage is responsible for converting categorical fields into numeric target-informed representations while guarding against leakage.

Recommended behavior:

- fit the encoder on the training partition only
- transform validation and test partitions using the frozen encoder state
- keep numeric/binary fields in their original numeric form where they are already valid
- keep unseen categories safe by using the encoder's built-in handling for unknown or missing values

### 5. Final output contract

The notebook must produce a final numeric model-ready dataset that is suitable for modeling. The expected outputs are:

- `data/featurization/train_numeric_data.csv`
- `data/featurization/validation_numeric_data.csv`
- `data/featurization/test_numeric_data.csv`
- `data/featurization/model_ready_numeric_data.csv` (combined, multi-partition file with `dataset_partition`)

The combined output must contain:

- numeric engineered feature columns
- `loan_status_r`
- `dataset_partition`
- no leakage columns from the raw outcome post-processing fields

The final row-level contract is:

- each row belongs to exactly one partition: `train`, `validation`, or `test`
- the split assignment must be deterministic and consistent with the canonical cleaned raw splits
- no hidden random re-split is allowed inside the modeling pipeline

## Required notebook structure

The implementation notebook should be organized into the following stages:

1. Data loading and validation
2. Explicit top-five feature selection
3. Numeric train-only median imputation
4. Train-only M-estimate categorical encoding
5. Final assembly and export

This modular order makes the notebook easier to maintain and easier to reason about when the feature design changes.

## Acceptance criteria

The implementation is considered complete when:

- the notebook loads the canonical raw training/validation/test partitions
- the training split is used to fit all learned transformations
- the validation and test partitions are transformed using the learned artifacts
- categorical variables are encoded with `MEstimateEncoder`
- the model-ready output contains exactly the five ranked raw features after numeric encoding
- final numeric outputs are saved to the configured featurization output directory
- the final model-ready combined file contains a stable `dataset_partition` column and the target `loan_status_r`

This gives the project a reproducible, leakage-safe featurization pipeline that is ready for downstream modeling.
