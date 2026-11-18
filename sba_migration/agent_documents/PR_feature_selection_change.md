# PR: Support Fixed External Feature Screens

## Status

The SBA implementation in this repository has been updated without requiring an immediate upstream package checkout. This PR specification records the corresponding `kmds-featurization` change needed when that package is opened.

## Problem

`tabular.feature_space.select_model_features` currently learns a model-based feature subset. For sparse SBA outcomes, the project now uses a separately produced fixed screen based on the latest externally screened pool:

- `bankname`
- `initialinterestrate`
- `terminmonths`
- `borrstreet`
- `sbadistrictoffice`
- `projectcounty`
- `bankstate`
- `borrcity`
- `processingmethod`
- `loan_age_months`

Traditional feature selection must not rerun against this screen. The model-ready projection must preserve these raw fields so the modeling package can fit train-only imputation and categorical encoding without re-learning a feature subset.

## Package change

Add an explicit fixed-screen mode to the feature-space API, or add a small sibling helper, with an interface equivalent to:

```python
project_fixed_feature_screen(
    data,
    predictors,
    target_col,
    partition_col,
)
```

Required behavior:

1. Validate every configured predictor exists in the input.
2. Do not invoke `select_model_features`, train an importance model, or generate a knee chart.
3. Preserve predictor names, values, data types, and row index.
4. Include target and partition metadata in the model-ready output.
5. Align active rows to exactly the same columns.
6. Fail explicitly on missing configured predictors.
7. Emit diagnostics describing the screen source and whether selection was fixed or learned.

## Configuration

Allow a pipeline stage to declare:

```yaml
feature_selection_mode: fixed
required_predictors:
  - bankname
  - initialinterestrate
  - terminmonths
  - borrstreet
  - sbadistrictoffice
  - projectcounty
  - bankstate
  - borrcity
  - processingmethod
  - loan_age_months
```

Existing learned-selection configurations must remain unchanged when the new mode is absent or set to `learned`.

## Acceptance criteria

- `fixed` mode performs no tree fitting and has no dependency on feature-importance configuration.
- Missing or misspelled predictors raise a clear error.
- Train, validation, test, and active partitions contain only the configured predictors plus required metadata.
- Categorical and date values remain raw for train-fitted modeling preprocessing.
- Learned mode remains backward compatible.
- Unit tests cover fixed projection, missing predictors, active alignment, and learned-mode compatibility.

## Local implementation already completed

`featurization_scripts/featurization.py` now bypasses `select_model_features` and uses the explicit `required_predictors` projection configured in `featurizer_config.yaml`. The upstream package enhancement is therefore not blocking this SBA experiment, but it removes duplicated orchestration and makes the fixed-screen behavior reusable.

## Validation command after upstream implementation

Run the relevant package tests plus an SBA featurization regeneration, then confirm the model-ready header contains:

```text
bankname,initialinterestrate,terminmonths,borrstreet,sbadistrictoffice,projectcounty,bankstate,borrcity,processingmethod,loan_age_months,loan_status_r,dataset_partition
```
