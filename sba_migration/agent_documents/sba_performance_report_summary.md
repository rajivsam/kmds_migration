# SBA Modeling Workflow Performance Summary

## Prologue

Several modeling approaches were evaluated during this project, including broader feature engineering, recall-maximizing threshold sweeps, and more complex multi-stage and utility-oriented designs. The main limitation was the sparse nature of the available predictors and the low prevalence of distressed loans: traditional in-model feature selection was not stable enough to support a defensible operating policy.

To address that limitation, the project used the [imbalanced feature screener](https://github.com/rajivsam/imbalanced_feature_screener/tree/master) to identify a fixed external screen. In the current run, the selected screened predictors are:

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

Those externally screened features were fixed for the model, and a calibrated Stage-1 model was used to rank validation loans by predicted default risk. The project then used cumulative gains and lift curves with an elbow method to tune the Stage-2 review cutoff. This feature-screening and gains-chart strategy produced a strong review queue: high default capture without reviewing the full loan population.

## Selected workflow

The model uses the externally screened predictors above. Gradient boosted trees and random forests are trained on the canonical training partition. Probabilities are calibrated using isotonic regression, and the validation gains curve determines the frozen review cutoff.

## Stage-1 model comparison

On the validation set, the Stage-1 champion was the gradient boosting model:

- `gradient_boosting`: PR-AUC = 0.735678
- `random_forest`: PR-AUC = 0.700025

The gradient boosting model was selected as the champion and used for Stage-2 cutoff tuning and subsequent evaluation.

## Validation cutoff

The reproducible maximum-distance elbow selected `k = 17.00%` of the ranked validation population.

At this operating point:

- reviewed validation loans: not explicitly enumerated in the last export, but the selected fraction corresponds to 17.00%
- cumulative gains / recall: 82.00%
- precision: 44.24%
- lift: 4.8206
- frozen calibrated probability threshold: 0.126925

## Held-out test performance

The frozen 17.00% cutoff was applied unchanged to the held-out test partition.

- test rows: 7,508
- actual defaults: 690
- selected for review: 1,295
- reviewed population: 17.25%
- precision: 44.17%
- recall: 82.90%
- PR-AUC: 0.7267
- balanced accuracy: 0.8615

## Interpretation

The operating point is suitable for a human review queue: it captures approximately 83% of true test defaults while reviewing approximately 17% of the population. Among the loans flagged, roughly 44% are true defaults.

These are screening metrics, not final adjudication metrics. The frozen threshold and feature screen should remain unchanged when comparing future runs unless the underlying requirements are deliberately revised.
