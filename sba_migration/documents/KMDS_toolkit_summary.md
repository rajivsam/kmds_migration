# KMDS Toolkit Summary

## Executive Summary

KMDS is not a single monolithic application. It is a toolkit of related packages and components that together support enterprise-grade machine learning development with auditability, transparency, and clean separation of concerns.

This repository demonstrates the KMDS pattern through a collection of packages that each handle a specific stage of the workflow:
- data ingestion and semantic tagging with `dd-parser-cleaner`
- feature preparation with the KMDS featurizer
- model development with `kmds-modeling`
- repository auditing and metadata extraction with `kmds-data-helper`

These packages define consistent interfaces for producing, validating, and retrieving modeling artifacts for tabular ML projects.

## Responsibilities

| Role | Data Scientist | KMDS Packages | Agent |
|---|---|---|---|
| Data sourcing | Decide which raw datasets to use and which sources are trusted | Provide directory structure and metadata conventions | Ingest repository content via helper, map sources to tool input paths |
| Entity selection | Choose which entities to featurize, such as geographic or temporal entities | Offer featurization components that support logical types and domain-specific features | Route the data into the right KMDS package and ensure the right entity types are used |
| Feature engineering | Decide how to encode categorical entities, handle missing values, and select features | Implement reusable featurization transforms and target-aware feature logic | Apply the correct sequence of package operations and preserve separation of concerns |
| Data cleaning | Define domain rules and cleaning strategy | Provide parser/cleaner outputs, metadata tags, and recommended cleaning actions | Coordinate the cleaner stage and produce clean inputs for featurization |
| Modeling workflow | Choose algorithms, validation strategies, and model thresholds | Provide model evaluation, export interfaces, and artifact serialization | Orchestrate `kmds-modeling` and ensure the generated artifacts are usable operationally |
| Audit & documentation | Interpret results, verify assumptions, and review model readiness | Provide knowledge graph and audit metadata generation tools | Convert the repo into an auditable knowledge graph for ad hoc query and inspection |

## KMDS Toolkit Principles

- **Separation of concerns**: each package has a distinct responsibility, from cleaning to featurization to modeling.
- **Consistent interfaces**: packages expose structured configuration, data contracts, and outputs that can be chained.
- **Transparency**: every stage produces artifacts and reports that can be audited in a repository or by tools like `kmds-data-helper`.
- **Extensibility**: the same architecture supports cross-sectional examples now and will support longitudinal, TSEDA, and other enterprise-grade data types later.

## SBA Example: a concrete instantiation

In this repository, the SBA example shows how the toolkit is used in practice:
- The data scientist determined that geographic entities were important and exposed borrower latitude/longitude as featurization targets.
- The featurizer generated cluster-distance features and handled categorical encoding strategy for the `loan_status_r` target.
- The modeling package trained gradient boosting and random forest candidates, calibrated probabilities, and prepared export artifacts for operational use.
- The agent was expected to use the packages linearly:
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

`kmds-data-helper` can convert the resulting repository into a knowledge graph by ingesting the repository artifacts and helper outputs, then translating the findings into a KMDS `project_knowledge_graph.xml`.

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
