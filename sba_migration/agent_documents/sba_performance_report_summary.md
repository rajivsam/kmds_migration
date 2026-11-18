# SBA Modeling Workflow Performance Summary

## Prologue

Several modeling approaches were evaluated during this project, including broader feature engineering, recall-maximizing threshold sweeps, and more complex multi-stage and utility-oriented designs. The main limitation was the sparse nature of the available predictors and the low prevalence of distressed loans: traditional in-model feature selection was not stable enough to support a defensible operating policy.

To address that limitation, the project used the [imbalanced feature screener](https://github.com/rajivsam/imbalanced_feature_screener/tree/master) to identify the five strongest predictors for this dataset. Those externally screened features were fixed for the model, and a calibrated Stage-1 model was used to rank validation loans by predicted default risk. The project then used cumulative gains and lift curves with an elbow method to tune the Stage-2 review cutoff. This feature-screening and gains-chart strategy produced the strongest, operationally actionable result: strong default capture without requiring a review of the full loan population.

## Selected workflow

The model uses the five externally screened predictors:

- `initialinterestrate`
- `bankcity`
- `approvaldate`
- `terminmonths`
- `bankname`

Gradient boosted trees and random forests are trained on the canonical training partition. Probabilities are calibrated using isotonic regression, and the validation gains curve determines the frozen review cutoff.

## Validation cutoff

The reproducible maximum-distance elbow selected `k = 17%` of the ranked validation population.

At this operating point:

- reviewed validation loans: 1,277
- defaults captured: 554 of 689
- cumulative gains / recall: 80.41%
- precision: 43.38%
- lift: 4.73
- frozen calibrated probability threshold: 0.131353

## Held-out test performance

The frozen 17% cutoff was applied unchanged to the test partition.

- test rows: 7,508
- actual defaults: 690
- selected for review: 1,294
- reviewed population: 17.23%
- precision: 43.35%
- recall: 81.30%
- PR-AUC: 0.6963
- balanced accuracy: 0.8528
- F2: 0.6919
- Brier score: 0.0585
- frozen-percentile lift: 4.78

## Interpretation

The operating point is suitable for a human review queue: it captures approximately 81% of true test defaults while reviewing approximately 17% of the population. Among the loans flagged, approximately 43% are true defaults.

These are screening metrics, not final adjudication metrics. The frozen threshold and feature screen should remain unchanged when comparing future runs unless the underlying requirements are deliberately revised.
