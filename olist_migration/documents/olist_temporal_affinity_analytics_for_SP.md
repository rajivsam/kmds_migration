# Olist Temporal Affinity Analytics for SP

## Motivation

Retail teams need to understand how product demand shifts over time so they can plan inventory, staffing, and budgets with more confidence. Please see [this document](segmentation_as_usecase.md) for a discussion why machine learning is suitable for this problem. For Olist in São Paulo, 2017 is the highest-quality historical window, and its weekly product purchase behavior is a strong signal for seasonal affinity patterns.

This project is designed to answer questions such as:

- Which products or product groups are most active in each week of the year?
- Are there consistent seasonal clusters of weeks and products that indicate buying regimes?
- How should merchandising, fulfillment, and staffing plans adapt to peak affinity clusters?

The business value is clear:

- inventory planning: reduce stockouts by aligning ordering to week-product affinity clusters
- staffing planning: schedule warehouse and customer service capacity around likely demand regimes
- budgeting: allocate promotions and logistics spend to the weeks that matter
- strategy: identify long-tail products versus seasonal hits for portfolio decisions

## KMDS-Driven Methodology

### 1. Clean the data

We started with the Olist featurization pipeline and the São Paulo 2017 subset. The raw inputs were:

- `data/olist_orders_dataset_raw.csv`
- `data/olist_order_items_dataset_raw.csv`
- `data/olist_customers_dataset_raw.csv`

The KMDS pipeline produced a clean weekly product activity matrix:

- `data/SP_2017_freq_prod_weekly_sales_prepared.csv`

This dataset is already aligned to order history, product activity, and the weekly calendar, which is the correct unit for temporal affinity analysis.

### 2. Create a product-week view

The analysis matrix is a bipartite view with:

- rows = week of year (`woy`)
- columns = product IDs
- values = product activity counts or revenue by week

This representation allows the model to treat weeks and products as paired entities in a joint affinity space rather than forcing a flat, row-only clustering view.

### 3. Run the model advisor

The local `kmds_modeling` advisor was invoked for `CLUSTERING` and confirmed that this dataset is an unsupervised grouping task.

Advisor output:

- task type: `CLUSTERING`
- pillar: `D`
- guidance: `Use robust clustering that respects operational heterogeneity. Prefer spectral clustering with gap selection or HDBSCAN fallback when appropriate.`

This recommendation matches the domain intuition for a week-product affinity problem.

### 4. Discuss approaches with the team

We considered multiple analytic branches:

- flat k-means on aggregated feature vectors
- hierarchical clustering on weekly sales totals
- spectral co-clustering on the week-product matrix

The team chose spectral co-clustering because it preserves the bipartite week-product topology, reduces the influence of evergreen products, and yields interpretable block structures.

### 5. Select the approach

The final approach was:

- build a normalized affinity matrix from the weekly product activity matrix
- apply TF-IDF-style normalization to downweight globally dominant products
- compute the normalized bipartite spectral embedding
- cluster the combined week and product embedding using KMeans

This approach was implemented in `models/spectral_clustering.py` and executed from the `notebooks/modeling_spectral_clustering.ipynb` notebook.

## Output and Visualization

The project produced the following outputs under `models/`:

- `spectral_gap.csv`
- `week_clusters.csv`
- `product_clusters.csv`
- `week_embeddings.csv`
- `product_embeddings.csv`
- `cluster_counts.csv`
- `spectral_clustering_summary.md`

The notebook also includes visualizations that make the affinity structure accessible:

- spectral values / gap analysis
- week cluster assignment scatter plot over week-of-year
- product cluster distribution bar chart

## Business Impact

This affinity analytics workflow is useful for:

### Inventory planning

- identify product clusters with strong seasonal spikes
- reduce overstock of slow-moving products in low-affinity weeks
- prioritize replenishment for products tied to high-affinity week clusters

### Staffing planning

- detect calendar regimes with elevated product affinity
- align warehouse and customer support staffing to expected demand clusters
- use week cluster labels as an early guide for workforce planning

### Budgeting and promotions

- allocate promotional budget to weeks with concentrated product affinity
- use product cluster labels to target bundle or cross-sell campaigns
- identify low-affinity weeks where discounting may be necessary

### Strategic analytics

- transform raw weekly sales into interpretable demand regimes
- compare affinity clusters for São Paulo against other regions in future work
- build operating plans that respect the joint temporal and product manifold structure

## Conclusion

The Olist temporal affinity analytics project is a KMDS-driven, clean, data-informed approach to understanding how product demand evolves across weeks in São Paulo, 2017. It combines structured featurization, advisor validation, team discussion, and spectral co-clustering to produce outputs that are immediately useful for inventory, staffing, and budgeting decisions.
