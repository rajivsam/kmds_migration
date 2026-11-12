# Modeling Instructions

This is a standard regression task using a real-world cross-sectional dataset.

## Dataset characteristics
- All features are numeric.
- The dataset spans multiple geographies, so heterogeneity is expected.
- The dataset is already clean and featurized; no additional feature engineering or preprocessing is required.

## Candidate models
Evaluate the following models:
- Gradient boosted trees
- Random forest

## Loss function and data splits
- Use mean squared error (MSE) as the optimization/loss metric.
- Create three splits:
  - Training set
  - Validation set
  - Test set

## Model tuning
- Use the validation set to tune model hyperparameters.
- Tune the parameters so that the training and validation errors are as close as possible (ideally matched or highly similar).
- Prefer configurations that balance underfitting and overfitting while minimizing validation error.

## Final evaluation
- After tuning, report the holdout performance of the selected model on the test set.
- Include the final test-set MSE as the reported benchmark.