# KMDS-Powered ML Solutions: Insights Article

## Executive Summary

KMDS is designed to make machine learning projects reproducible in batch/offline settings. By aligning with business planning cycles and enforcing structured workflows, KMDS ensures that ML outputs are reliable, explainable, and repeatable. This transforms ML from one-off experiments into a dependable capability for mid-market enterprises.

## Problem Context

For many companies, machine learning problems are solved on a cadence tied to business planning cycles. In these cases, models are stable enough to remain effective for months, which defines the **batch/offline ML setting**—the subset of problems KMDS is designed to address. Unlike online or continuous models, this cadence reflects the most common business reality.

It’s important to distinguish **model development** from **model retraining**. A demand forecasting model may retain its structure but require retraining on new operational data. KMDS focuses on development, ensuring that design choices—data cleaning, feature engineering, modeling, and deployment—are captured and reproducible across cycles.

Without this reproducibility, critical context behind modeling decisions is lost, leading to inconsistent outcomes and reduced confidence in ML outputs. KMDS fixes this gap, enabling firms to trust that each cycle builds on a reliable foundation rather than reinventing the process.

## Examples in This Repository

This repository demonstrates KMDS workflows on two of the most prevalent dataset types in business development: **cross-sectional** and **panel** datasets. Within these, we cover three common machine learning problems:

- **Classification on cross-sectional data** — a supervised ML task often used for customer segmentation or risk scoring.
- **Clustering on cross-sectional data** — an unsupervised ML task applied to grouping customers, products, or suppliers.
- **Survival analysis on panel data** — a time-to-event modeling approach relevant for churn prediction, equipment failure, or contract renewals.

While these problems represent only a subset of enterprise ML challenges, the goal here is to show that **the same solution template applies across settings**. The mechanics of developing and delivering the solution—data cleaning, feature engineering, modeling, and deployment—remain consistent, reinforcing reproducibility and confidence in outcomes.

## Technical Approach

KMDS solves reproducibility challenges in batch ML by enforcing a structured, Git-based workflow. The framework assumes that projects are versioned in Git, refreshed on a quarterly cadence, and directed by human experts with agent assistance for mechanics.

### Repeatability Mechanisms

KMDS achieves reproducibility by enforcing structure and consistency across all phases of a machine learning project. The framework is built on several key assumptions and tools:

- **Git-managed projects**: All projects are versioned in Git, ensuring that every modeling decision is tracked and recoverable.
- **Fixed directory structure**: Each repository follows a standard layout: `documents`, `notebooks`, `data`, `data_dictionary`, `models`, and `featurization_scripts`.
  - The **dd-parser-cleaner** package bootstraps this structure automatically.
  - The **location-helper** utility guides users on what artifacts belong where.
- **Standardized project phases**: Projects follow the familiar sequence of data cleaning, featurization, and modeling—consistent with industry standards like CRISP-DM.
- **Phase packages with discovery APIs**: Each phase has a package that organizes inputs/outputs consistently.
  - The `get_package_info()` API exposes the interface of each package.
  - Config files capture relevant keys, while a path coordinator abstraction ensures agents can read/write without hard-coding paths.
  - Properties abstract keys/values, simplifying semantics and making code more maintainable.
- **Agent-assisted orchestration**: Data scientists interact with packages using coding agents (e.g., GitHub Copilot) to discover package properties, write design documents for phase tasks, and implement pipelines (e.g., survival-dataset pipeline, classifier-model pipeline).
- **Knowledge graph integration**: Repository consistency enables the **kmds-data-helper** tool to map projects into a natural-language searchable knowledge graph. Existing graphs can be searched via the **KMDS-UI**, a Dash application.

KMDS assumes mid-level or higher data science skills. Human experts provide the design instructions for featurization and modeling pipelines, while agents assist with execution. This hybrid approach ensures reproducibility without oversimplifying the expertise required.

## Business Impact

By embedding reproducibility into every stage of machine learning projects, KMDS delivers
