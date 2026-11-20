# SBA Knowledge Graph Generation Requirements

## Objective

Create a KMDS knowledge graph that documents the SBA loan modeling problem, the
modeling alternatives considered, the feature-selection rationale, the
implemented workflow phases, and the final held-out performance evidence.

The graph should illustrate a useful KMDS knowledge graph rather than merely
list final metrics. It should span all supported KMDS observation types and
connect decisions to the notebooks and documents that implement them.

## Data source and prediction problem

The SBA loan dataset is sourced from:

- [SBA data on Data.gov](https://data.gov/metrics/organization/sba/)

The current exercise predicts the **probability that an SBA loan will be
charged off**. Loans with elevated predicted risk are referred to human review.
The model supports review prioritization; it does not perform automatic final
adjudication.

### Alternative outcome formulations

Other formulations are possible depending on the business objective. For
example, insurance and credit-risk applications may estimate both:

1. the probability of an adverse event; and
2. the loss intensity or amount conditional on that event occurring.

An equivalent two-part SBA formulation could estimate both the probability of
charge-off and the amount charged off if a charge-off occurs. This exercise
intentionally models only the probability of charge-off and refers high-risk
loans to human review.

## Modeling guidance and alternatives considered

The principal modeling approach and implementation requirements are documented
in:

- [SBA modeling requirements](../documents/sba_modeling_requirements.md)

Several approaches were evaluated before the final baseline was selected:

1. **Cascading classifiers** — optimize first for recall and then for precision.
2. **Utility-based scoring** — combine the predicted probability of default with
   the amount at risk and compare the utility of a review prediction with a
   no-review prediction. Select the higher-utility action with a safety factor.
3. **Calibrated probability ranking with a human-review cutoff** — train and
   calibrate candidate classifiers, rank validation loans by predicted risk,
   select an operating point from cumulative gains and lift, freeze the
   threshold, and evaluate it once on the held-out test set.

The knowledge graph should preserve these alternatives and explain why the
calibrated ranking and review-queue formulation is the current project
baseline.

## Feature selection requirement

Feature selection is essential for this dataset. Including all available
features introduces feature noise and can produce a weak classification model,
as documented in:

- [SBA performance report summary](sba_performance_report_summary.md)

Feature importance must be assessed from multiple complementary perspectives
to obtain a reliable and balanced view. The project uses:

- [imbalanced_feature_screener](https://github.com/rajivsam/imbalanced_feature_screener)

The screener is intended for feature evaluation in imbalanced datasets. Relying
on the importance values of a single fitted classifier can overstate unstable
predictors or be distorted by the low prevalence of charged-off loans.

The final model uses five features:

1. `bankname`
2. `bankcity`
3. `initialinterestrate`
4. `bankstreet`
5. `terminmonths`

Using five features is a judgment call, not a universal optimum. Future
experiments may evaluate different feature counts and subsets, but they must
record the requested `top_k`, selected feature identities, screener version and
configuration, and the downstream validation and test results.

## Foundational references

The graph and the feature-selection rationale should cite and explain the
following references:

1. Domingos, P. (2012).
   [*A Few Useful Things to Know about Machine Learning*](https://doi.org/10.1145/2347736.2347755).
   Communications of the ACM, 55(10), 78-87.
   This work emphasizes that representation, feature engineering,
   generalization, and overfitting are central to machine-learning success.
2. Guyon, I., & Elisseeff, A. (2003).
   [*An Introduction to Variable and Feature Selection*](https://www.jmlr.org/papers/v3/guyon03a.html).
   Journal of Machine Learning Research, 3, 1157-1182.
   This paper motivates feature selection and shows the value of considering
   complementary evaluation perspectives.
3. Kuhn, M., & Johnson, K. (2013).
   [*Applied Predictive Modeling*](https://doi.org/10.1007/978-1-4614-6849-3).
   Springer.
   This book provides practical guidance for preprocessing, feature selection,
   resampling, model comparison, and evaluation.
4. He, H., & Garcia, E. A. (2009).
   [*Learning from Imbalanced Data*](https://doi.org/10.1109/TKDE.2008.239).
   IEEE Transactions on Knowledge and Data Engineering, 21(9), 1263-1284.
   This reference covers the learning and evaluation challenges created by
   imbalanced classes.

## Workflow phases to represent

Review [SBA KMDS workflow overview](../documents/sba_modelling_overview.md) and
represent each phase in the graph. Observations should point to the
corresponding implementation notebook or artifact.

| Phase | Responsibility | Implementation or evidence |
| --- | --- | --- |
| 1. Acquisition and initial preparation | Preserve the SBA source, acquisition context, and canonical raw copy. | [`data/sba_loans_raw.csv`](../data/sba_loans_raw.csv) and the [SBA workflow overview](../documents/sba_modelling_overview.md) |
| 2. Parsing, cleaning, metadata, and annotation | Profile the data, interpret cleaning recommendations, define field semantics, and prepare the terminal-outcome universe. | [`clean_sba_dataset.ipynb`](../notebooks/clean_sba_dataset.ipynb) |
| 3. Geographic feature investigation | Explore latitude/longitude and good/distressed cluster distance features. | [`clustering_feature_derivation.ipynb`](../notebooks/clustering_feature_derivation.ipynb) |
| 4. Feature advice and selection under imbalance | Compare candidate features with multiple perspectives and establish a controlled feature contract. | [`feature_advisor_sba_example.ipynb`](../notebooks/feature_advisor_sba_example.ipynb) and [imbalanced_feature_screener](https://github.com/rajivsam/imbalanced_feature_screener) |
| 5. Featurization | Apply train-only imputation and encoding, preserve `dataset_partition`, and export consistent numeric model inputs. | [`sba_featurization.ipynb`](../notebooks/sba_featurization.ipynb) |
| 6. Candidate training and calibration | Fit Gradient Boosting and Random Forest candidates on `train` and calibrate probabilities with isotonic regression. | [`sba_modeling.ipynb`](../notebooks/sba_modeling.ipynb) |
| 7. Model selection and validation thresholding | Select the champion on validation PR-AUC, construct cumulative gains and lift, and select a validation-only elbow cutoff. | [`sba_modeling.ipynb`](../notebooks/sba_modeling.ipynb) |
| 8. Held-out evaluation and handoff | Freeze the model and cutoff, evaluate the test partition once, and publish reproducible metrics and model artifacts. | [`sba_modeling.ipynb`](../notebooks/sba_modeling.ipynb) and [`sba_performance_report_summary.md`](sba_performance_report_summary.md) |

## Knowledge graph coverage

The graph must use the KMDS 0.5 notebook API and cover **every supported
observation type**, including the exploratory, data-representation,
modeling-choice, model-selection, and experimental families.

At minimum, the graph should contain observations for:

- data relevance and source provenance;
- terminal-outcome scope and class imbalance;
- geographic and final five-feature engineering;
- train-only transformations and canonical partitions;
- Gradient Boosting and Random Forest modeling choices;
- assumptions about decision-time availability and human review;
- model-selection criteria and validation setup;
- candidate-model evidence and the selected champion;
- the feature-selection hypothesis and alternative modeling experiments;
- direct experimental observations and conjectures;
- the validation elbow and frozen operating threshold;
- held-out test results and follow-up implications.

The notebook should also:

1. display the supported observation-type registry;
2. construct observations through `KnowledgeGraph.add_observation`;
3. avoid direct Owlready2 ontology construction;
4. assert that every supported observation type appears;
5. display the chronological observation table;
6. save the graph as RDF/XML;
7. reload it with `KnowledgeGraph.load`; and
8. verify that the loaded table matches the in-memory table.

## Current evidence to capture

The baseline selected Gradient Boosting from the two evaluated candidates. The
graph should include the following project evidence:

- validation PR-AUC:
  - Gradient Boosting: `0.7560`
  - Random Forest: `0.7237`
- validation elbow:
  - nominal ranked cohort: `20.00%`
  - frozen calibrated probability threshold: `0.069643`
  - realized review rate after score ties: `20.55%`
- held-out test:
  - rows: `7,510`
  - charge-offs: `690`
  - selected for review: `1,468`
  - review rate: `19.55%`
  - precision: `38.76%`
  - recall / cumulative gains: `82.46%`
  - F1: `52.73%`
  - PR-AUC: `0.7421`
  - balanced accuracy: `0.8464`
  - lift: `4.22`

The interpretation is that the model is suitable for constructing a human
review queue: it captures approximately 82.5% of test charge-offs while
reviewing approximately 19.5% of the population. These are screening metrics,
not final adjudication metrics.

## Deliverable

Create the executable knowledge-graph notebook at:

- [`notebooks/knowledge_graph_creation.ipynb`](../notebooks/knowledge_graph_creation.ipynb)

Use KMDS 0.5's notebook interface and the references and phase map above. The
notebook should save its completed RDF/XML graph in the workspace output
directory so the observations can be reviewed, reused, and visualized
independently of the notebook.
