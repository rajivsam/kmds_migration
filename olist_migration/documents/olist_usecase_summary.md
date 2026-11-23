# Regional Temporal SKU Segmentation with Unsupervised Learning

## Executive proposition

The Olist São Paulo case study demonstrates how a retail transaction history can be converted into an operationally useful segmentation of product demand over time. The goal is not to predict an individual target variable. It is to identify which SKUs share stable weekly demand behavior and which exhibit distinct temporal patterns that merit separate planning attention.

The canonical problem is **regional temporal SKU segmentation**: given a history of retail transactions, determine a coherent market and observation window, represent SKU activity across time, and group weeks and products by shared demand structure. The resulting segmentation can guide assortment review, merchandising, replenishment monitoring, and further inventory-policy analysis.

This use case is suitable for showcasing KMDS because the work requires more than selecting an algorithm. It records the decision context, data-scope rationale, representation choices, model contract, generated evidence, and the limits of the operational claims.

## Business decision

A regional retail team managing a large and heterogeneous assortment needs to decide whether every SKU should be treated alike. Static catalog categories and aggregate sales rankings do not show when a product sells, whether its demand is routine or intermittent, or which products distinguish one period of the year from another.

The operational decision supported by this analysis is:

> Which São Paulo SKUs form the routine demand baseline, and which smaller groups have sufficiently distinctive weekly behavior to justify separate review?

The output is a decision-support segmentation, not an automated replenishment policy. Inventory investment, service levels, lead times, margins, stock-on-hand, and stockout costs would be needed before the segments could directly determine order quantities or safety stock.

## Why this is a canonical retail analytics problem

Large retailers and marketplaces routinely face:

- a broad, long-tail assortment;
- demand concentrated in a smaller active market or fulfillment region;
- incomplete time coverage in historical extracts;
- many low-frequency SKUs;
- operational differences hidden by aggregate category labels; and
- a need to separate routine demand from specialized or event-sensitive behavior.

Unsupervised learning is appropriate because there is no pre-existing label that defines the desired operational regimes. The task is to discover structure in the transaction history and then evaluate whether that structure is useful for a concrete retail decision.

This use case is narrower and more defensible than a full ABC-XYZ or inventory-optimization claim. ABC-XYZ analysis usually requires revenue or volume plus demand variability and often incorporates inventory economics. The current Olist representation contains weekly item-price activity, but not inventory cost, margin, supplier lead time, or service-level data. It therefore supports **temporal demand segmentation**, which can become an input to later ABC-XYZ and inventory-policy work.

## Data scope and reduction

The source workflow begins with three public Olist datasets:

- 99,441 orders;
- 112,650 order-item records after joining the item-level transaction data; and
- 32,951 catalog products.

The cleaned item-level working table contains 112,650 records. All 2017 and 2018 records should not be pooled into one undifferentiated annual model:

- 2017 is a complete calendar-year observation window in the extract.
- 2018 is partial; the source orders extend only to October 2018.
- Calendar-complete behavior cannot be compared fairly when one year lacks a full set of weeks.

São Paulo is also the largest represented market:

| Geography | Item records | Share of cleaned item records |
| --- | ---: | ---: |
| São Paulo | 47,449 | 42.1% |
| Rio de Janeiro | 14,579 | 12.9% |
| Minas Gerais | 13,129 | 11.7% |

The canonical analytical scope combines the complete year with the largest regional market:

> **São Paulo transactions placed during 2017**

This retains 20,044 order-item records, approximately 17.8% of the cleaned item-level history. The reduction is not a finding that other records are invalid. It is a design decision that removes time and geographic mixtures that would make the operating regimes harder to interpret.

The scoped item-level data is pivoted into a weekly SKU revenue representation:

- 52 rows, representing ISO weeks 1 through 52;
- 9,367 SKU columns; and
- each cell representing the sum of item prices for that SKU in that week.

This is a major change in analytical grain. More than one hundred thousand transaction events become a compact representation of how each SKU behaved across the year. The representation is sparse because many SKUs sell in only a few weeks, but no SKU-level revenue floor is applied in the canonical featurization pipeline.

## Representation and modeling

The model uses a bipartite week-SKU structure. Weeks are connected to products through observed weekly revenue activity, allowing the analysis to preserve the relationship between calendar periods and product demand.

The processing steps are:

1. Sum item prices by SKU and ISO week for São Paulo in 2017.
2. Build a 52-by-9,367 weekly revenue matrix.
3. Apply a TF-IDF-style transformation so products that are broadly active do not dominate the representation solely because they are common.
4. Normalize the bipartite affinity matrix.
5. Compute a joint spectral embedding for weeks and SKUs.
6. Cluster the combined embedding with KMeans using 16 configured clusters, a four-dimensional embedding, and random state 42.

The repository also generates spectral values and gaps, product and week embeddings, cluster assignments, and a clustering-advisor recommendation. The advisor confirms clustering as the appropriate unsupervised task family. The configured model is a fixed 16-cluster run; the presence of gap diagnostics should not be interpreted as proof that 16 was automatically selected by the spectral-gap plot.

## Results

The model produced a highly concentrated segmentation rather than evenly sized groups:

- 8,661 of 9,367 SKUs, or **92.5%**, were assigned to the dominant product cluster.
- 706 SKUs, or **7.5%**, were assigned outside the dominant cluster.
- The four largest non-dominant product groups contained 420, 150, 56, and 36 SKUs.
- The largest week regime contained 21 of 52 weeks.
- A second week regime contained 11 weeks.
- A third week regime contained 6 weeks.

The measured result is **structural concentration**: most SKU activity follows a broad shared pattern, while a much smaller portion of the assortment is distinguishable through temporal demand behavior.

The cluster labels alone do not establish that the groups are “evergreen,” “seasonal,” or “promotional.” Those interpretations require cluster profiling against sales frequency, revenue, product category, calendar events, and stability checks. The defensible immediate result is the separation of a large baseline-like group from several smaller, behaviorally distinct candidate groups.

## Operational meaning

The segmentation supports a staged retail response:

### 1. Baseline assortment management

Use the dominant 8,661-SKU group as the population for a standard regional monitoring and replenishment process. Its concentration means that a common baseline policy may be reasonable to test, but individual inventory economics must still be assessed.

### 2. Specialist assortment review

Prioritize the 706 SKUs outside the dominant group for profiling. Questions to answer include:

- Which weeks drive each group?
- Are the products concentrated in particular categories?
- Are the patterns recurring, sparse, or event-driven?
- How much revenue and order volume do the groups represent?
- Do the groups remain stable under alternative feature weights or cluster counts?

### 3. Calendar-linked planning

Use the week assignments to identify periods that differ from the broad operating regime. These periods can trigger deeper forecasts, promotion reviews, merchandising checks, and capacity planning.

### 4. Policy validation

Before changing inventory targets, join the segmentation to margin, lead time, service level, on-hand inventory, and stockout information. Then test whether differentiated policies improve business outcomes relative to the current uniform rule.

The output is therefore actionable in a disciplined way: it directs management attention and creates candidate policy groups. It is not, by itself, evidence of a realized cost saving or inventory improvement.

## How KMDS frames the use case

The mechanics are reusable across KMDS use cases:

1. **State the decision.** Identify what regional retail team is trying to change.
2. **Define the evidence boundary.** Select the complete time window and relevant market.
3. **Document data reduction.** Explain which records enter the analysis and why.
4. **Create an aligned representation.** Preserve the week-SKU relationship needed for the decision.
5. **Use an advisor and explicit model contract.** Retain the recommended task family and configured method.
6. **Preserve analytical evidence.** Keep the matrix, embeddings, assignments, counts, and configuration.
7. **Translate results into action.** Separate measured findings from operational hypotheses.
8. **Record limitations.** Prevent exploratory structure from being presented as proven business impact.

The problem characteristics differ from a supervised KMDS example because there is no target label and no predictive score. Evaluation depends on:

- separation and stability of the discovered structure;
- whether the groups have interpretable temporal and product profiles;
- whether the groups remain useful when joined to business metrics; and
- whether they improve a real planning decision in a controlled test.

The reusable KMDS contribution is therefore not spectral clustering itself. It is the governed, reproducible path from a business question to data evidence and an explicit operational response.

## Recommended website wording

> **Regional Retail Demand Segmentation**  
> This KMDS case study converts 112,650 Olist order-item records into a coherent São Paulo 2017 demand study. A scope decision favors the largest represented market and a complete calendar year, reducing the analysis to 20,044 relevant item records. These transactions become a 52-week by 9,367-SKU revenue matrix, which is analyzed with spectral clustering. The result is highly concentrated: 92.5% of SKUs occupy one broad temporal group, while 7.5% form smaller groups suitable for focused assortment, merchandising, and inventory-policy investigation. The workflow records the data rationale, representation, model evidence, and business boundary so the discovered segments remain explainable and reproducible.

## Evidence and limitations

The primary evidence is retained in:

- [`modeling_config.yaml`](../modeling_config.yaml)
- [`featurizer_config.yaml`](../featurizer_config.yaml)
- [`featurization_scripts/featurization.py`](../featurization_scripts/featurization.py)
- [`SP_2017_freq_prod_weekly_sales_prepared.csv`](../data/SP_2017_freq_prod_weekly_sales_prepared.csv)
- [`product_clusters.csv`](../models/product_clusters.csv)
- [`week_clusters.csv`](../models/week_clusters.csv)
- [`cluster_counts.csv`](../models/cluster_counts.csv)
- [`clustering_advisor_recommendation.json`](../models/advisor/clustering_advisor_recommendation.json)

Limitations to keep visible:

- The matrix represents weekly item-price activity, not demand forecasts or stock requirements.
- Co-purchase and basket affinity are not modeled.
- The 2017 São Paulo result does not establish behavior in another region or year.
- Cluster labels are not semantic business segments until they are profiled.
- The current artifacts do not demonstrate cluster stability, realized inventory savings, or forecast uplift.
- Inventory, margin, lead-time, and service-level data are required for policy optimization.