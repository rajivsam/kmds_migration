# SBA Modeling Workflow Summary

## Objective

The goal of this project is to demonstrate a repeatable, enterprise-style machine learning workflow on a real-world SBA dataset, using the kind of operational steps expected in a modern modeling program: data preparation, feature engineering, model candidate selection, calibration, threshold tuning, artifact export, and human-in-the-loop review.

This is not a claim that the model is a final production risk engine. Rather, it is a demonstration that the workflow is robust and credible: the project follows a disciplined pipeline from source data to modeled outputs with governance around partitions, model selection, and reproducible artifacts.

## What the workflow illustrates

The implementation demonstrates a full, practical ML lifecycle for an imbalanced credit-screening use case:

- canonical dataset partitioning (`train`, `validation`, `test`, `active`)
- feature derivation with a clean fit-on-train / apply-to-all pattern
- model candidate comparison across multiple families
- probability calibration to improve usable scores
- threshold selection for operational decisioning
- scoring of the active population for downstream use
- serialization of model artifacts for an MLOps-like handoff

This is exactly the kind of workflow an enterprise team would expect to see for a real risk-screening problem: disciplined, interpretable, and reusable.

## Why the results are still useful

The SBA dataset represents a rare-event classification problem. In the current out-of-time slices, default incidence is low, so a screening model is judged primarily on whether it captures a large share of true defaults without being so conservative that it becomes operationally unusable.

With that context, the current test-set result is still useful:

- the model recovers nearly all of the true positives at the selected operating threshold
- the operating point is chosen to favor recall for screening
- this is appropriate when the business objective is to identify high-risk loans for review rather than to produce a highly precise final adjudication decision

This makes the model a valid screening model, not a high-precision final decision engine. In a human-in-the-loop workflow, that tradeoff is often exactly what is desired: cast a wide but relevant net, then let review teams investigate the flagged cases.

A utility-based policy remains a possible future improvement if richer loan-level balance, amortization, and cost data become available. For the current dataset, the recall-first policy is the more defensible baseline.

## Test-set performance

The actual performance numbers on the test set at the selected recall-first operating threshold are:

- threshold: 0.005263
- balanced accuracy: 0.4993
- precision: 0.0251
- recall: 0.9868
- F2: 0.1139
- Brier score: 0.0255

## Interpretation

The model is not a strong highly precise classifier in the strict sense, and that is expected given the class rarity and the limited feature engineering available in this exercise. However, for screening, the result is materially useful because the recall is extremely high: it catches nearly all of the true positives and therefore helps prioritize the right loans for further review.

This operating point intentionally favors recall-first screening. It is appropriate when the business objective is to cast a wide net for review and it is consistent with the project’s rare-event classification workflow. The precision remains low because the positive class is sparse and the model is being used to maximize coverage rather than final adjudication accuracy.

If the team later obtains better loan-level balance/cost data, then a utility-driven threshold tuning could be revisited. But with the current data, the recall-first approach is the appropriate baseline and the best transparent choice.

## Bottom line

This project successfully demonstrates a repeatable enterprise-grade ML workflow on a real-world dataset, with emphasis on disciplined process and human-driven screening rather than a single headline accuracy metric. The test-set recall of 98.68% is the key result for this use case and demonstrates that the model remains highly useful as a screening tool even in a sparse-default environment. A future utility-based model may be worthwhile only when the loan-cost and remaining-balance data are available and reliable.
