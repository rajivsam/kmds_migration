# Executive Summary: Olist Regional Demand Segmentation

## The problem

Retailers cannot apply one policy to an assortment containing thousands of SKUs with different demand histories. Aggregate sales rankings show which products sell the most, but not how SKU activity changes across the year or which weeks and products form distinct operating regimes.

This Olist use case frames the canonical problem as **regional temporal SKU segmentation**: identify which products in a coherent retail market form the routine demand baseline and which smaller groups display sufficiently different weekly behavior to justify focused planning.

## What KMDS did

The workflow starts with 112,650 Olist order-item records covering a 2016–2018 extract. It scopes the analysis to São Paulo in 2017 because:

- São Paulo is the largest represented regional market, with 47,449 item records or 42.1% of the cleaned history.
- 2017 provides a complete calendar-year observation window.
- 2018 is partial, so it is unsuitable for an equivalent full-year comparison.

The scope retains 20,044 São Paulo 2017 item records. KMDS then converts these transactions into a 52-week by 9,367-SKU revenue matrix, applies TF-IDF-style weighting and bipartite spectral normalization, and produces a joint spectral embedding of weeks and SKUs. KMeans assigns the joint representation to 16 configured clusters.

This data reduction is a change of analytical grain, not a claim that records outside the selected scope are unusable.

## Result

The resulting structure is highly concentrated:

- **8,661 SKUs (92.5%)** form the dominant product cluster.
- **706 SKUs (7.5%)** occupy smaller, differentiated groups.
- The largest non-dominant groups contain **420, 150, 56, and 36 SKUs**.
- The dominant week regime contains **21 of 52 weeks**, followed by regimes of 11 and 6 weeks.

The immediate finding is that most São Paulo product activity follows a broad shared pattern, while a smaller part of the assortment exhibits temporal behavior distinct enough for specialist review.

## Why it is actionable

The result supports a two-level operating model:

1. Apply standard regional monitoring to the dominant SKU base.
2. Profile the 706 non-dominant SKUs and associate them with their week regimes for focused replenishment, merchandising, promotion, and capacity analysis.

The segmentation is a prioritized decision queue. Before changing safety stock or purchase quantities, the groups should be joined to margin, lead time, stock-on-hand, stockout, and service-level data. The present result does not claim realized inventory savings or forecast improvement.

## Why this matters for KMDS

The statistical method differs from supervised KMDS examples, but the knowledge-management mechanics are the same:

- define the operational decision;
- make the data-scope and reduction logic explicit;
- preserve the analytical representation;
- record the advisor recommendation and model contract;
- retain assignments, embeddings, and diagnostics;
- distinguish evidence from interpretation; and
- map the result to a testable business action.

The reusable KMDS capability is not spectral clustering itself. It is the governed path from a business question to reproducible analytical evidence and an explicit action boundary.

For the full problem statement, methodology, results, and limitations, see [Olist Regional Temporal SKU Segmentation](olist_usecase_summary.md).