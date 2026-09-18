# Olist Marketplace Analytics

## Problem statement

Olist is a major online marketplace operating across Latin America, and the São Paulo market is the dominant regional demand center in the public dataset. The analytical objective is not to build a predictive classification model, but to characterize temporal product affinity in São Paulo during 2017 and to identify recurring demand regimes over the calendar year. This is operationally relevant for inventory planning, merchandising, staffing, and budget allocation because retail demand is shaped by both baseline consumption and seasonal or promotional spikes.

## Dataset and scope

This case study uses the public Olist Brazilian E-Commerce dataset, with the analysis restricted to the São Paulo market in 2017. The project integrates order, order-item, and customer records to construct a weekly product activity view for the selected geography and period. The focus on a single region and a single calendar year reduces confounding from structural shifts in market composition and ensures that the resulting affinity patterns reflect a stable operating window.

The analytical unit is a product-week matrix in which rows correspond to weeks of the year and columns correspond to products, with entries representing weekly product activity or revenue. This framing is appropriate for a temporal affinity problem because it preserves the joint structure between time and product demand rather than collapsing the analysis to a single aggregate product ranking.

## Preprocessing choices

The raw Olist data are cleaned and normalized through the KMDS workflow before modeling. The preprocessing pipeline assembles the relevant order-level features, joins transaction details to product information, and filters the dataset to the São Paulo subset for the 2017 study window. This yields a cleaned transaction table suitable for downstream aggregation and feature generation.

The project then constructs weekly product summaries from the filtered data, with explicit thresholds applied to suppress very low-volume, noisy product-week observations. This step is essential in a marketplace setting with a long tail of infrequent products, where a small number of high-volume items would otherwise dominate the analysis and obscure the main temporal patterns. The resulting prepared outputs include the weekly product revenue matrix and the downstream affinity table used for clustering.

## Feature engineering and representation choices

The central representation is a wide weekly product matrix rather than a conventional one-row-per-customer feature table. Each week is represented as a vector over products, and each product is represented as a time-varying demand profile across the year. This yields a bipartite structure in which week-level and product-level behavior are analyzed jointly.

To preserve interpretability and reduce the influence of globally dominant products, the weekly product matrix is normalized and thresholded before spectral analysis. This keeps the signal focused on relative demand structure rather than raw scale, allowing clusters to reflect temporal affinity regimes rather than simple volume effects. The representation is therefore intentionally compact, domain-aligned, and transparent to stakeholder review.

## Modeling choices and why they were selected

The project uses spectral co-clustering on the normalized week-product affinity matrix. This modeling choice is well suited to the problem because the data are naturally represented as a bipartite graph: weeks are connected to products through shared demand behavior, and the goal is to identify blocks of coherent temporal-product structure. Spectral methods are appropriate here because they operate on the eigenstructure of the similarity graph and are less sensitive than centroid-based methods to the irregular geometry induced by heavy-tailed marketplace demand.

The number of clusters is selected using the spectral gap, which provides a data-driven indication of the natural separation in the underlying graph structure. In practice, this yields a dominant baseline cluster of broadly active products and smaller clusters representing more specialized or seasonal demand regimes. This is a better fit for the business problem than a single aggregate ranking because it preserves the temporal organization of demand.

## Evaluation criteria

The evaluation is based on structural interpretability and operational usefulness rather than on a predictive accuracy metric. The primary criteria are whether the identified clusters are stable, well separated, and aligned with meaningful calendar-based demand patterns. The spectral gap helps assess whether the selected cluster count reflects a real signal in the data rather than an arbitrary partition.

The resulting clusters are then assessed in terms of their business meaning: do they correspond to baseline demand, holiday-driven surges, or niche seasonal products? This is the relevant evaluation standard for an exploratory analytics workflow, where the goal is not to optimize a supervised score but to make demand structure visible and actionable.

## Key outputs

The Olist migration workflow produces a set of artifacts that make the analysis reproducible and auditable. The main data products include the cleaned São Paulo weekly product matrix and the revenue-based product-week output used for clustering:

- data/SP_2017_weekly_product_revenue_by_product_id.csv
- data/SP_2017_freq_prod_weekly_sales_prepared.csv

The modeling outputs retained in the workspace include:

- models/spectral_gap.csv
- models/week_clusters.csv
- models/product_clusters.csv
- models/cluster_counts.csv
- models/week_embeddings.csv
- models/product_embeddings.csv
- models/spectral_clustering_summary.md

These artifacts document the normalized affinity matrix, the cluster assignments, and the spectral evidence used to support the final demand-segmentation interpretation.

## Interpretation for stakeholders

From an operational perspective, the Olist case study demonstrates how KMDS can convert raw marketplace data into interpretable demand regimes. The dominant cluster identifies the steady-state product base that is repeatedly active across many weeks, while smaller clusters highlight periods and products associated with seasonal or promotion-driven variation. This distinction is valuable because it separates the predictable baseline from temporary surges that may require different inventory, staffing, or marketing responses.

For managers, the resulting structure is actionable. It supports inventory planning by identifying which products should be treated as baseline demand versus event-driven demand, and it supports staffing and budgeting decisions by showing when the year is characterized by distinct operational regimes. The use of a transparent, documented workflow allows stakeholders to understand not only what the model finds, but why it finds it.

## Design decisions that were revisited or changed

The most important design choice in this project was to frame the problem as a week-product affinity analysis rather than as a flat product ranking or a conventional time-series forecasting task. This preserves the joint structure between calendar timing and product demand, which is essential for understanding market dynamics in a retail setting.

A second major decision was to threshold and normalize the demand matrix to prevent high-volume evergreen products from dominating the clustering signal. This was not a cosmetic choice: without it, the analysis would primarily recover the most common products rather than the temporal buying regimes that are operationally relevant. The project also restricted analysis to São Paulo in 2017 because that period provides complete data coverage and a coherent business window for interpretation.

## Links to notebooks / scripts / outputs

- Data-preparation notebook: notebooks/raw_datafile_creation.ipynb
- Modeling notebook: notebooks/modeling_spectral_clustering.ipynb
- Modeling advisor notebook: notebooks/modeling_clustering_advisor.ipynb
- Featurization script: featurization_scripts/featurization.py
- Configuration: config.yaml
- Featurizer configuration: featurizer_config.yaml
- Modeling configuration: modeling_config.yaml
- Prepared affinity data: data/SP_2017_freq_prod_weekly_sales_prepared.csv
- Weekly revenue matrix: data/SP_2017_weekly_product_revenue_by_product_id.csv
- Spectral clustering summary: models/spectral_clustering_summary.md
- Cluster outputs: models/week_clusters.csv, models/product_clusters.csv, models/cluster_counts.csv

## Summary

The Olist marketplace case study shows how KMDS supports a scientifically defensible and operationally useful analysis of temporal demand structure. By combining a disciplined data-preparation pipeline, a domain-specific product-week representation, and spectral co-clustering, the workflow makes heterogeneous demand patterns explicit without sacrificing interpretability. The resulting analysis supports reproducible decision-making for inventory, staffing, and promotion planning in a real market environment, while preserving the provenance of the modeling choices that produced the final insight.
