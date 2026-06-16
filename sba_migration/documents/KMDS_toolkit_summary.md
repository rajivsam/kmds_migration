# KMDS Toolkit Summary

## Executive Summary

KMDS is a toolkit of related packages and components that support enterprise-grade machine learning development with auditability, transparency, and clear separation of concerns.

KMDS transforms analytical projects from collections of files, notebooks, and documents into a queryable institutional knowledge asset. The resulting knowledge can be accessed through agents, reused by future teams, and preserved even as personnel change over time.

This repository demonstrates the KMDS pattern through a set of packages that each handle a distinct stage of the workflow:

- data ingestion and semantic tagging with `dd-parser-cleaner`
- feature preparation with `kmds-featurizer`
- model development with `kmds-modeling`
- repository auditing and metadata extraction with `kmds-data-helper`

These packages define consistent interfaces for producing, validating, and retrieving modeling artifacts for tabular ML projects.

## The Agent-Human Collaboration

Developing a data science solution requires answering many interconnected questions. Getting any one of them wrong can produce a model that fails to meet requirements. Often, these questions are developed and answered by different stakeholders over varying timelines.

Humans retain ownership and accountability for performance. LLMs are well-suited for retrieving context, generating boilerplate, and reducing behavioral errors when tasks are defined clearly.

KMDS leverages this collaboration to deliver repeatable, auditable, and transparent ML solutions.

### 1. The Semantic Foundation (`dd-parser-cleaner`)

In a typical tabular ML project, the preparatory steps include:

1. Identifying the statistical properties of the data
2. Setting up attributes with correct types
3. Accounting for missing values
4. Applying standard cleaning procedures
5. Tagging domain-specific attributes for downstream pipeline tasks

A lot of this can be automated, but edge cases remain and the human is ultimately the expert. `dd-parser-cleaner` handles most of the boilerplate cleaning work while the human reviews, finalizes corrections, and signs off on the next step.

Please see the notebook [clean_sba_dataset.ipynb](../notebooks/clean_sba_dataset.ipynb) for the SBA example. Please also see [workflow_desc.md](workflow_desc.md) for the details of how the dd-parser-cleaner works.

### 2. The Feature Advisor (`kmds-featurizer`)

Once the data is semantically tagged, KMDS invokes the Feature Advisor. This service uses an LLM to provide strategic featurization recommendations and rationale based on logical type.

These recommendations are drawn from domain knowledge for non-numeric attribute featurization. The data scientist remains accountable for the final choice and uses the suggestions to identify a strong set of candidate transformations.

Please see the notebook [feature_advisor_sba_example.ipynb](../notebooks/feature_advisor_sba_example.ipynb) for the SBA implementation.

### 3. The Design-Time Compiler (`kmds-modeling`)

After feature preparation, the project enters the KMDS Design Governance Framework. `kmds-modeling` acts as a compiler that prevents architectural anti-patterns before they occur and translates design decisions into model-ready guidance.

## KMDS Design Governance Framework

Machine learning projects involve many modeling choices. For teams without deep experience in a specific problem, this volume of options can be overwhelming.

The KMDS Modeling Advisor understands the problem, clarifies priorities, and provides a concise set of guidelines that can be used with any coding assistant to implement a model.

### Supported Modeling Themes

KMDS currently focuses on tabular problems and recognizes several common enterprise ML themes:

1. **Classification**: including workflows for imbalanced classes.
2. **Regression**: standard continuous prediction tasks.
3. **Graph-based Learning**:
   - **Homogeneous Graphs** (single entity types)
   - **Bipartite Graphs** (two entity types)
   - **Heterogeneous Graphs** (multiple entity and relationship types)

If a problem matches one of these themes, the advisor provides tailored guidance. If it does not, the assistant will identify that limitation so the team can plan accordingly.

## Responsibilities


| Role                  | Data Scientist                                                                        | KMDS Packages                                                                          | Agent                                                                                 |
| ----------------------- | --------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Data sourcing         | Decide which raw datasets to use and which sources are trusted                        | Provide directory structure and metadata conventions                                   | Ingest repository content via helper, map sources to tool input paths                 |
| Entity selection      | Choose which entities to featurize, such as geographic or temporal entities           | Offer featurization components that support logical types and domain-specific features | Route the data into the right KMDS package and ensure the right entity types are used |
| Feature engineering   | Decide how to encode categorical entities, handle missing values, and select features | Implement reusable featurization transforms and target-aware feature logic             | Apply the correct sequence of package operations and preserve separation of concerns  |
| Data cleaning         | Define domain rules and cleaning strategy                                             | Provide parser/cleaner outputs, metadata tags, and recommended cleaning actions        | Coordinate cleaner stage and produce clean inputs for featurization                   |
| Modeling workflow     | Choose algorithms, validation strategies, and model thresholds                        | Provide model evaluation, export interfaces, and artifact serialization                | Orchestrate`kmds-modeling` and ensure generated artifacts are usable operationally    |
| Audit & documentation | Interpret results, verify assumptions, and review model readiness                     | Provide knowledge graph and audit metadata generation tools                            | Convert the repo into an auditable knowledge graph for query and inspection           |

## KMDS Toolkit Principles

- **Separation of concerns**: each package has a distinct responsibility, from cleaning to featurization to modeling.
- **Consistent interfaces**: packages expose structured configuration, data contracts, and outputs that can be chained.
- **Transparency**: every stage produces artifacts and reports that can be audited in a repository or by tools like `kmds-data-helper`.
- **Extensibility**: the same architecture supports cross-sectional examples now and will support longitudinal, TSEDA, and other enterprise-grade data types later.

## Operational Integration: The Finished Product

The result of this workflow is a **Design Blueprint**—an expert prompt that the user can hand to any AI coding assistant to generate production-grade code that follows KMDS governance rules.

**Example SBA Governance Blueprint:**

```text
================== [KMDS DESIGN GUIDANCE: SBA EWS] ==================
PROBLEM CHARACTERISTICS:
- Task: Tabular Classification (Loan Default)
- Imbalance: Moderate (SBA Default Ratios)
- Priority: High Interpretability

DESIGN GUIDELINES:
1. Model: Use a Cost-Sensitive Gradient Boosted Tree with isotonic calibration.
2. Validation: Use Stratified K-Fold to maintain the 'Good/Bad' ratio.
3. Feature Logic: Incorporate Distance-to-Bad-Cluster (hdbc) features derived from geographic tags.

SUGGESTED AI ASSISTANT PROMPT:
"I am building an Early Warning System for SBA loans.
Following KMDS Governance for moderate imbalance and high interpretability,
please draft a training script using XGBoost with scale_pos_weight
and include a calibration step using Isotonic Regression..."
====================================================================
```

By combining human expertise with agent-driven technical governance, the SBA example shows that ML production can be both rapid and transparent.

## SBA Example: a concrete instantiation

In this repository, the SBA example demonstrates how the toolkit is used in practice:

- The data scientist determined that geographic entities were important and exposed borrower latitude/longitude as featurization targets.
- The featurizer generated cluster-distance features and handled categorical encoding strategy for the `loan_status_r` target.
- The modeling package trained gradient boosting and random forest candidates, calibrated probabilities, and prepared export artifacts for operational use.
- The agent was expected to use the packages sequentially:
  1. `dd-parser-cleaner` to clean and document the raw data
  2. `kmds-featurizer` to turn metadata-enriched data into modeling-ready features
  3. `kmds-modeling` to evaluate candidates and serialize production-ready artifacts
- The agent also needed to understand boundaries such as which package handles cleaning, which handles feature engineering, and which handles model export.

## Why this matters

KMDS and its supporting packages make the ML production process simple and transparent because they:

- separate auditing from modeling,
- separate data cleaning from feature engineering,
- enforce consistent project structure,
- enable the agent to work with modular components rather than one opaque system.

## Knowledge Graph Conversion

`kmds-data-helper` can convert the repository into a knowledge graph by ingesting repository artifacts and helper outputs, then translating the findings into a KMDS `project_knowledge_graph.xml`.

The really cool side effect of using the tools in the KMDS ecosystem is that the individual tool kit components generate the documentation for the project. You can then use the `kmds-data-helper` to use these artifacts, including anything the data scientist authored, into a KMDS knowledge graph.

This conversion makes the process queryable in an ad hoc way:

- inspectors can ask how the data was cleaned,
- analysts can trace which feature engineering choices were made,
- architects can review which modeling artifacts were produced,
- auditors can validate the workflow without rerunning the pipeline.

The knowledge graph thus becomes a transparent, searchable representation of the ML product lifecycle.

![KMDS knowledge graph screenshot](../images/kmds-sba-migration_kg.png){width=85%}

## Simplicity and transparency of ML production

The ML process is simple because the toolkit defines a clear line of responsibility:

- data cleaning is handled before featurization,
- featurization produces a stable `model_ready_numeric_data.csv`,
- modeling consumes that data and writes export artifacts,
- repository-level auditing converts the whole history into a graph.

It is transparent because each stage writes explicit artifacts and metadata rather than hiding decisions in code. The result is a production-ready workflow that can be reviewed, queried, and extended for cross-sectional, longitudinal, and other advanced KMDS use cases.
