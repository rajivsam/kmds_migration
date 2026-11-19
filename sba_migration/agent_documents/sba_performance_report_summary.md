# SBA Modeling Workflow Performance Summary

## Prologue

Several modeling approaches were evaluated during this project, including broader feature engineering, recall-first threshold diagnostics, and calibrated gains/lift-based cutoff tuning. The low prevalence of distressed loans and the sparse, correlated raw feature space made the retained feature set a decisive part of model performance.

Earlier work with a broader, manually engineered feature set produced weak ranking and collapsed to a zero-score threshold that effectively required reviewing the full population. The project therefore used the [imbalanced feature screener](https://github.com/rajivsam/imbalanced_feature_screener) to define a compact, externally ranked feature contract. The current baseline is the top five features from the screener's ranked report:

- `bankname`
- `bankcity`
- `initialinterestrate`
- `bankstreet`
- `terminmonths`

These five features are fixed for the current run. Feature count and membership remain experimental parameters: future runs can vary `top_k` through the screener, but must record the selected list and compare the result on the same canonical train/validation/test partitions. The current five-feature cap is retained because it materially improved both discrimination and the usable operating cutoff over the broader feature set.

## Selected workflow

The featurization notebook train-fits median numeric imputation and M-estimate categorical encoding for the five selected features. Gradient boosted trees and random forests are then trained on the canonical training partition, probabilities are calibrated with isotonic regression, and the validation cumulative gains curve determines the frozen Stage-2 review cutoff.

## Stage-1 model comparison

On the validation set, the Stage-1 champion was the gradient boosting model:

- `gradient_boosting`: PR-AUC = 0.7560
- `random_forest`: PR-AUC = 0.7237

The gradient boosting model was selected as the champion and used for Stage-2 cutoff tuning and subsequent evaluation.

## Validation cutoff

The reproducible maximum-distance elbow selected `k = 20.00%` of the ranked validation population. The exact decile table boundary is 20.0027% because the 7,509-row validation set does not divide evenly into ten groups.

At this operating point:

- selected batch cohort: 1,502 validation loans
- cumulative gains / batch recall: 86.21%
- lift at the selected batch percentile: 4.31
- cutoff boundary precision in the ranked gains table: 39.55%
- frozen calibrated probability threshold: 0.069643
- realized validation review count after applying `score >= threshold`: 1,543
- realized validation review rate: 20.55%
- realized validation precision: 38.76%
- realized validation recall: 86.79%
- validation PR-AUC: 0.7560

The small difference between the 20% batch cohort and the realized 20.55% threshold population is caused by score ties at the selected probability boundary. The batch percentile and the tie-expanded realized threshold result are reported separately.

## Held-out test performance

The frozen 0.069643 cutoff was applied unchanged to the held-out test partition.

- test rows: 7,510
- actual defaults: 690
- selected for review: 1,468
- reviewed population: 19.55%
- precision: 38.76%
- recall / cumulative gains: 82.46%
- F1: 52.73%
- PR-AUC: 0.7421
- balanced accuracy: 0.8464
- realized lift: 4.22

## Comparison with the broader feature set

The five-feature screen changed the operating policy from a non-discriminating result into a practical review queue:

| Metric | Prior broader feature set | Five-feature screen |
|---|---:|---:|
| Validation PR-AUC | 0.1673 | 0.7560 |
| Validation F1 at frozen cutoff | 0.1681 | 0.5358 |
| Test PR-AUC | 0.1523 | 0.7421 |
| Test F1 | 0.1683 | 0.5273 |
| Test review rate | 100.0% | 19.55% |
| Test lift | 1.00 | 4.22 |

## Interpretation

The operating point is suitable for a human review queue: it captures approximately 82.5% of true test defaults while reviewing approximately 19.5% of the population. Among flagged loans, approximately 38.8% are true defaults, compared with a 9.2% overall default prevalence.

These are screening metrics, not final adjudication metrics. Feature selection materially affects this result, so `top_k`, retained feature identities, and the screener version/configuration should be treated as controlled modeling parameters. The frozen threshold and feature screen should remain unchanged when comparing future runs unless the experiment explicitly changes the feature-selection configuration and re-completes the validation tuning process.
