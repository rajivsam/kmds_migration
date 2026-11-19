# KMDS Framework Overview for the SBA Modeling Project

## Purpose

This document explains how the KMDS framework is used to deliver and maintain the SBA data science project in a disciplined, repeatable, and auditable way.

KMDS is not a replacement for data science judgment. It provides a modular delivery framework for the activities that recur in analytics and machine learning projects, while leaving problem framing, feature design, modeling choices, validation, and operational interpretation to a competent data science team. The combination of reusable utilities and explicit domain expertise makes the recurring parts of an ML project much closer to a cookie-cutter workflow without making the resulting model generic or automatic.

The framework's central value is that each phase has:

- a clear responsibility;
- a defined input and output contract;
- reusable utilities for routine implementation work;
- explicit human review points for decisions requiring expertise;
- reproducible notebooks and artifacts;
- a clean handoff to the next phase.

## The KMDS delivery model

Most analytics and data science projects follow the same broad lifecycle:

1. acquire and prepare the raw source data;
2. profile, clean, and annotate the dataset;
3. translate domain fields into model-ready features;
4. select a stable, leakage-safe feature contract;
5. train and calibrate candidate models;
6. tune the operating cutoff on validation data;
7. evaluate once on held-out test data;
8. publish models, metrics, thresholds, and documentation;
9. maintain and rerun the workflow as data or requirements change.

KMDS supplies focused utilities for these common phases. This modularity reduces duplicated project plumbing and helps teams spend more effort on the decisions that require domain and modeling expertise.

The intended flow is:

```text
Raw source
   |
   v
kmds-dataset-util
   |  download / ingestion / initial preparation
   v
dd-parser-cleaner
   |  cleaning / profiling / metadata / annotations
   v
featurization
   |  transformations / feature contract / train-fit preprocessing
   v
imbalanced_feature_screener
   |  feature evidence / compact ranking under class imbalance
   v
kmds-modeling
   |  training / calibration / thresholding / evaluation
   v
Reproducible model bundle, gains/lift table, metrics, and documentation
```

## Phase 1: Data acquisition and initial preparation

The project uses [kmds-dataset-util](https://github.com/rajivsam/kmds-dataset-util) to download the source dataset and prepare it as a durable raw-data input.

This phase should be concerned only with reproducible acquisition and basic preparation. It should preserve enough information to answer:

- what source was used;
- where it came from;
- when it was acquired;
- what file or source version was captured;
- where the canonical raw copy is stored.

Separating acquisition from later cleaning prevents undocumented data corrections or transformations from becoming hidden in the download process.

## Phase 2: Parsing, cleaning, metadata, and annotation

The project uses [dd-parser-cleaner](https://github.com/rajivsam/dd-parser-cleaner) to profile and clean the raw dataset. This phase produces the cleaned records, data dictionary context, metadata, and annotations needed for safe downstream work.

Its outputs allow the team to understand:

- raw and cleaned field names and types;
- missing-value patterns;
- distributions and anomalous values;
- recommended cleaning actions;
- field semantics and potential modeling risks;
- which fields may be post-outcome or otherwise unsuitable for prediction.

This phase is essential because featurization cannot be made reliable by code alone. Cleaning recommendations and metadata must be reviewed by people who understand the source and the target business process.

The canonical cleaned SBA outputs in this project live under `data/dd_cleaner/` and preserve the train, validation, and test assignments used throughout the workflow.

## Phase 3: Featurization

The project uses the [featurization](https://github.com/rajivsam/featurization) utility to create a clear boundary between raw cleaned records and numeric model inputs.

The feature-advisor workflow and its recommendations are illustrated in:

- [feature_advisor_sba_example.ipynb](../notebooks/feature_advisor_sba_example.ipynb)

The canonical five-feature implementation used by modeling is:

- [sba_featurization.ipynb](../notebooks/sba_featurization.ipynb)

The featurization phase is responsible for:

- enforcing an explicit candidate and final feature contract;
- excluding post-outcome and leakage-prone fields;
- learning numeric imputation only on the training split;
- fitting categorical encoders only on the training split;
- transforming validation and test with frozen training artifacts;
- exporting consistent numeric train, validation, and test files;
- preserving `loan_status_r` and `dataset_partition`;
- serializing the featurization state needed for repeatable scoring.

For the current SBA baseline, the selected feature contract is:

1. `bankname`
2. `bankcity`
3. `initialinterestrate`
4. `bankstreet`
5. `terminmonths`

Numeric fields receive train-only median imputation. Categorical fields receive train-only M-estimate encoding. The combined output is `data/featurization/model_ready_numeric_data.csv`.

This is an intentionally narrow and reproducible interface: downstream modeling consumes the numeric output without redefining transformations or creating a second random split.

## Phase 4: Feature selection under class imbalance

Feature selection deserves a separate, explicit phase in an imbalanced classification project. More available fields do not necessarily produce a better model. Correlated, sparse, high-cardinality, or weakly measured fields can obscure stable signal and reduce ranking quality.

The project therefore uses [imbalanced_feature_screener](https://github.com/rajivsam/imbalanced_feature_screener) as the reference mechanism for ranking candidate features under class imbalance. It helps make feature choice:

- evidence-based;
- repeatable;
- comparable between runs;
- less dependent on the importance output of a single fitted classifier;
- sensitive to the practical needs of an imbalanced screening problem.

Feature count and membership should be treated as controlled modeling parameters. The current run fixes the `top_k` value at five, but future work may study alternative values or ranked subsets. Every experiment must record:

- the screener version or reference;
- screener configuration;
- requested `top_k`;
- ordered selected feature list;
- validation and test results;
- the final feature contract used by featurization and modeling.

Validation and test outcomes must not be used to silently reshape the feature set. Changes require a deliberate experiment that preserves the canonical split contract and reruns the complete downstream workflow.

In this project, narrowing the broader engineered feature set to the five screened features materially improved ranking quality and made the validation-derived review cutoff operationally useful. That result demonstrates why feature selection should be a maintained project artifact rather than an incidental model-training step.

## Phase 5: Modeling

The project uses [kmds-modeling](https://github.com/rajivsam/kmds-modeling) as the modeling utility layer. KMDS provides a repeatable structure around candidate models, calibration, threshold selection, scoring, and artifact serialization. The notebook remains the primary experiment and explanation surface, while the package and a later CLI wrapper provide automation-friendly reuse of the same logic.

The current modeling implementation is:

- [sba_modeling.ipynb](../notebooks/sba_modeling.ipynb)

The model-development requirements are defined in:

- [sba_modeling_requirements.md](sba_modeling_requirements.md)

The modeling workflow uses these boundaries:

1. **Training:** fit candidate Gradient Boosting and Random Forest pipelines only on `train`.
2. **Calibration:** apply isotonic calibration from training-derived probabilities.
3. **Validation diagnostics:** measure the champion by PR-AUC and retain a recall-maximizing threshold as a first-stage diagnostic.
4. **Stage 2 cutoff tuning:** rank all validation rows by calibrated default probability.
5. **Gains and lift:** calculate cumulative gains and lift at ordered review cutoffs.
6. **Elbow selection:** select the validation point with the greatest positive distance above the random-selection baseline.
7. **Freeze:** lock both the selected review percentile and calibrated probability cutoff.
8. **Test evaluation:** apply the frozen model and cutoff to test exactly once.

For individual-row scoring, the frozen condition is `score >= selected_threshold`. For batch scoring, the selected top-`k%` cohort is available as an alternative operating interpretation. Score ties at a probability boundary are reported because they can make the realized review population larger than the nominal batch percentile.

## Current project outcome

The five-feature baseline produced a clear improvement over the prior broader feature set:

| Metric | Prior broader set | Five-feature baseline |
|---|---:|---:|
| Validation PR-AUC | 0.1673 | 0.7560 |
| Test PR-AUC | 0.1523 | 0.7421 |
| Test F1 | 0.1683 | 0.5273 |
| Test review rate | 100.0% | 19.55% |
| Test lift | 1.00 | 4.22 |

The current champion is Gradient Boosting. The validation gains/lift elbow selects approximately the top 20% of the population and freezes a calibrated cutoff of `0.069643`. On test, this captures 82.46% of defaults while selecting 19.55% of loans for review, with precision of 38.76% and PR-AUC of 0.7421.

These results make two points:

- model architecture matters, but the feature contract can matter at least as much;
- a useful operating threshold requires a model with meaningful ranking separation, not only a model that can be fit successfully.

Performance details are maintained in [sba_performance_report_summary.md](../agent_documents/sba_performance_report_summary.md).

## Results, artifacts, and reproducibility

The modeling notebook records both the reasoning path and the executable implementation. It publishes results in code outputs and persistent artifacts rather than relying on screenshots or informal descriptions.

The primary outputs are:

- `data/featurization/model_ready_numeric_data.csv`
- `data/featurization/sba_featurization_bundle.joblib`
- `data/modeling/sba_model_bundle.joblib`
- `data/modeling/validation_gains_lift.csv`
- validation and test metric dictionaries stored in the model bundle
- the feature list, partition column, target column, model name, thresholds, and selected review percentile

Together, these artifacts support three distinct needs:

1. **Explanation:** the notebooks show what was done and why.
2. **Reproducibility:** the saved transformations and model state preserve the trained workflow.
3. **Automation:** the same contracts can later be wrapped by CLI or scheduled batch utilities.

## Where expertise remains essential

KMDS standardizes the structure and reusable mechanics of a project; it does not automate expert judgment. A competent data science team must still decide:

- whether the prediction target is correctly defined;
- whether the available data supports a defensible use case;
- which fields are available at decision time;
- which variables leak outcome information;
- how cleaning recommendations should be interpreted;
- which screener experiment or `top_k` contract is appropriate;
- whether model and calibration quality are sufficient;
- whether the selected review capacity is operationally acceptable;
- how model errors and review capacity affect the business;
- when a drifted or weak model should be retrained or retired.

The framework makes these decisions visible and reviewable. It does not hide them inside opaque utilities.

## Why this produces cleaner and more maintainable projects

KMDS improves project delivery by separating common mechanics from project-specific decisions.

### Modular responsibility

Acquisition, cleaning, featurization, feature screening, modeling, and reporting have distinct owners and output contracts. A change in one phase should not require informal rewrites across the entire project.

### Repeatable implementation

Canonical splits, train-only fit rules, saved transformations, and frozen thresholds eliminate avoidable variation between experiments and production reruns.

### Clear validation boundaries

Training, validation, and test are used for different purposes. The test set is not a tuning loop, and the model cannot be reconfigured after seeing its final performance without declaring a new experiment.

### Auditable feature decisions

The retained feature list and screener ranking are explicit requirements. A future reviewer can determine why a field entered the pipeline and which experiment introduced or removed it.

### Notebook-to-utility handoff

Notebooks remain appropriate for development, analysis, and reporting. Once the logic is stable, `kmds-modeling` and other utilities provide a natural route to automation without changing the notebook-defined contract.

### Maintainable change process

A future change can be handled phase by phase:

- new source data changes the acquisition and cleaning stages;
- changed field semantics update metadata and validation;
- a new feature-selection experiment changes the explicit feature contract;
- a new model candidate changes the training phase;
- a different operating capacity changes validation cutoff selection;
- deployment changes use the same saved transformations, model, and threshold.

This makes the project easier to rerun, review, transfer to another team, and extend without turning the workflow into a collection of one-off scripts.

## Conclusion

KMDS turns the common skeleton of a data science project into a maintained system of reusable utilities, explicit contracts, and reproducible artifacts. In the SBA project, `kmds-dataset-util`, `dd-parser-cleaner`, `featurization`, `imbalanced_feature_screener`, and `kmds-modeling` divide the work into understandable phases while the project notebooks and requirements documents capture the expert decisions that cannot be delegated to the framework.

The result is not “automatic data science.” It is disciplined data science: routine work is standardized, domain and modeling expertise is applied where it matters, and every important decision has a clear implementation, rationale, validation path, and maintenance boundary.