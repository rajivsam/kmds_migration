# KMDS Real Dataset Illustrations

This repository is set up to illustrate the KMDS toolkit applied to real datasets with the range of issues normally encountered in practical deployments.

## Purpose

- Show how KMDS tools support real-world data ingestion, cleaning, and structuring
- Demonstrate end-to-end handling of dataset issues such as missing values, quarantine output, and evolving schema semantics
- Provide a second instantiation of a real dataset workflow using the Olist retail dataset and KMDS modeling artifacts

## Contents

1. The SBA dataset: This dataset is from the SBA. It provides the financial standing of 7a loans gauranteed by the SBA, nationwide. It is published on a monthly schedule. This represents an imbalanced classification problem. Please see [this document](https://github.com/rajivsam/kmds_migration/blob/main/sba_migration/documents/sba_development_example_full_doc.md) for a complete description of how a solution is developed for this example. This example is in the financial domain, however, the methodology used here can be applied to other classifiers that have the same imbalance characteristics and are applied on some temporal cadence in a batch manner. Examples include:
   1. Churn Prediction
   2. Fraud detection
   3. Adverse reaction to a drug
2. The Olist dataset: This dataset is from Olist (sourced from Kaggle). In the supply chain world, segmentation of sales is an important use case, please see [this document](olist_migration/documents/segmentation_as_usecase.md) for the reason machine learning is applied to develop a solution for this model.
3. The ITSM dataset: This dataset is used to develop a survival analysis solution to capture the performance characteristics of various support groups . Details coming soon.

## Why this repository exists

This repository provides an illustration of how machine learning solutions can be replicated following a standard methodology for a range of enterprise problems. While the modeling approach can be very different, the process from a documentation perspective can be standardized.  This is not to take away focus from the solution techniques for the individual use case. Constructive feedback and comments are welcome.
