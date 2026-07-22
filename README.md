# Case Studies Overview

KMDS is not just a technical framework — it is a repeatable consulting methodology.  
To illustrate its application, we highlight three case studies based on public datasets.  
Each one demonstrates how KMDS structures data, preserves domain knowledge, and enables workflows that transfer directly to real business problems.

---

## SBA Loan Dataset
- **Context**: Imbalanced classification problem with far fewer defaults than successful loans.  
- **KMDS Solution**: Defined loan records as the unit of analysis, captured monthly updates, engineered features to handle imbalance.  
- **Outcome**: Repeatable workflow for imbalanced classification.  
- **Transferability**: Applicable to churn prediction, fraud detection, and adverse drug reactions.  
- **Deep Dive**: [SBA workflow](sba_migration/documents/sba_development_example_full_doc.md)

---

## Olist Retail Dataset
- **Context**: E‑commerce transactions with heterogeneous data (orders, reviews, product categories).  
- **KMDS Solution**: Structured customer orders as the unit of analysis, captured order timelines, integrated product and review features.  
- **Outcome**: Segmented retail sales into actionable clusters, built forecasting workflows.  
- **Transferability**: Inventory forecasting, customer segmentation, demand planning.  
- **Deep Dive**: [Olist workflow](olist_migration/documents/olist_development_example_full_doc.md)

---

## ITSM Downtime Dataset
- **Context**: Service management logs with downtime events and resolution times.  
- **KMDS Solution**: Defined downtime events as the unit of analysis, captured resolution timelines, engineered escalation features.  
- **Outcome**: Survival analysis for downtime prediction, workflows for resolution time forecasting.  
- **Transferability**: IT operations, reliability engineering, risk management.  
- **Deep Dive**: [ITSM Survival Pipeline](itsm_analysis/notebooks/create_itsm_survival_pipeline.ipynb) and [ITSM Kaplan-Meier Model](itsm_analysis/notebooks/create_KM_models.ipynb)

---

## Why This Matters
These case studies show KMDS as both a **technical framework** and a **consulting methodology**.  
Executives can see the business relevance, while engineers can explore the detailed migration steps in the sections below.


# KMDS Real Dataset Illustrations

This repository demonstrates how the KMDS toolkit applies a consistent solution methodology across multiple real-world projects.

The models in this repository are created by assistants based on modeling prompts. There are modeling assistants for each phase of the project, and they guide the workflow from data understanding through featurization and clustering. Data cleaning and featurization are also performed by assistants, with a human expert in the loop to validate and steer the work.

KMDS does not simply build one-off models. It captures dataset semantics, creates a knowledge-backed cleaning and feature-engineering workflow, and then applies the same structured process to each new dataset. That makes it possible to reuse the same methodology across domains such as finance, retail, and IT service management while still solving the unique business problem for each project.

![KMDS component view](images/kmds_component_view.png)

## Purpose

- Show how KMDS tools support real-world data ingestion, cleaning, and structuring
- Demonstrate end-to-end handling of dataset issues such as missing values, quarantine output, and evolving schema semantics
- Provide a second instantiation of a real dataset workflow using the Olist retail dataset and KMDS modeling artifacts
- Provide a third instantiation of a workflow showing survival analysis.

## Contents

1. The SBA dataset: Monthly nationwide 7a loan data used for an imbalanced classification problem. See the [SBA workflow document](sba_migration/documents/sba_development_example_full_doc.md). This same methodology can also be applied to similar batch classifiers, including:

   1. Churn prediction
   2. Fraud detection
   3. Adverse reaction to a drug
2. The Olist dataset: Olist data (from Kaggle) for retail sales segmentation. See [Segmentation as a Use Case](olist_migration/documents/segmentation_as_usecase.md) for business context and the [Olist workflow document](olist_migration/documents/olist_development_example_full_doc.md) for implementation details.
3. The ITSM dataset: IT service ticket data for survival analysis of resolution performance. See [Create ITSM Survival Pipeline](itsm_analysis/notebooks/create_itsm_survival_pipeline.ipynb) and [Create ITSM Survival Kaplan-Meier Model](itsm_analysis/notebooks/create_KM_models.ipynb).

## Why this repository exists

This repository provides an illustration of how machine learning solutions can be replicated following a standard methodology for a range of enterprise problems. While the modeling approach can vary by use case, the process from a documentation, knowledge, and workflow perspective remains standardized. This is not to take away focus from the solution techniques for the individual use case. Constructive feedback and comments are welcome.

## Further Reading

- For a deeper discussion of reproducibility, methodology, and business impact, see the [KMDS Insights Article](docs/kmds_insights_article.md).
- To explore the published documentation site, visit the [KMDS GitHub Pages root](https://rajivsam.github.io/kmds_migration/).
