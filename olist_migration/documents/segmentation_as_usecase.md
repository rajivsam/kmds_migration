Inventory segmentation is a critical, complex challenge in modern supply chains. It involves categorizing stock-keeping units (SKUs) to determine the right service levels, replenishment cycles, and safety stock targets. Misclassification directly leads to severe operational pain points, such as high capital tied up in slow-moving items and frequent stockouts on critical goods. [1, 2, 3, 4, 5]

---

## The Reality of Inventory Segmentation as an SCM Problem

In modern retail and manufacturing, companies manage thousands or millions of SKUs across multiple distribution centers. Treating all products identically is financially impossible and operationally inefficient. [3, 6, 7, 8, 9]
According to insights published by the [Association for Supply Chain Management](https://www.ascm.org/), managing highly variable, seasonal demand patterns across huge distribution networks requires advanced segmentation to [dynamically rationalize the inventory mix and set proper stocking targets](https://www.ascm.org/ascm-insights/what-can-machine-learning-do-for-your-supply-chain/). Failures in this area result in what professionals call the "long tail" inventory trap, where an unmanaged range of products inflates warehouse costs while failing to satisfy core consumer demand. [8, 10, 11]

---

## Machine Learning vs. Static ABC Analysis

While traditional ABC Analysis scales inventory focus strictly based on a single parameter (typically total revenue or transaction volume via the 80/20 Pareto principle), it struggles in modern enterprise environments. [3, 12, 13]
The table below breaks down the rationale for utilizing Machine Learning (ML) clustering models over static, threshold-based filtering: [14, 15]


| Feature [3, 7, 10, 12, 14, 15, 16, 17, 18, 19] | Static ABC / XYZ Analysis                                                                                     | Machine Learning (e.g., K-Sparsity, K-Means Clustering)                                                      |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Data Dimensions                                | Single or dual-criteria. Usually limited to cost or volume.                                                   | Multi-criteria. Concurrently weights margin, lead times, volatility, and order frequencies.                  |
| Threshold Logic                                | Rigid and fixed. Human analysts guess arbitrary split percentages (e.g., 80/15/5).                            | Data-driven borders. Discovers non-linear, mathematical boundaries natively within dataset structures.       |
| Adaptability                                   | Time-consuming updates. Becomes rapidly obsolete as market trends shift unless manually redone.               | Real-time adjustment. Automatically moves SKUs between segments as demand patterns evolve.                   |
| Handling Volatility                            | Fails on seasonal goods. Classifies a summer product as a "C" item during winter, ruining spring preparation. | Pattern-aware. Tracks historical patterns and shifts categories predictively before demand peaks.            |
| Labor Scale                                    | High manual effort. Requires extensive data manipulation in spreadsheets for large inventories.               | Automated processing. Efficiently maps millions of SKUs simultaneously without manual scoring interventions. |

## Core Architectural Advantage

Static thresholds introduce significant human bias when weighting different factors. For example, deciding whether a low-cost item with an unstable 60-day vendor lead time belongs in Category B or C is often arbitrary. [14]
ML algorithms (like spectral clustering) eliminate this by [measuring pure mathematical distances between multi-dimensional item behaviors](https://academic.oup.com/imaman/advance-article/doi/10.1093/imaman/dpag002/8435240?searchresult=1).  In this example, [spectral clustering](../notebooks/modeling_spectral_clustering.ipynb) was used for this purpose. This groups products with similar demand together.  See [the use case implementation document](olist_temporal_affinity_analytics_for_SP.md) for the implementation details.

---

[6] [https://jmsr-online.com](https://jmsr-online.com/article/optimizing-supply-chain-management-through-machine-learning-applications-in-e-commerce-380/)
[7] [https://www.sciencedirect.com](https://www.sciencedirect.com/science/article/abs/pii/S2214785322061144)
[8] [https://www.youtube.com](https://www.youtube.com/watch?v=zct3uvg0VQs)
[9] [https://www.supplychain247.com](https://www.supplychain247.com/article/autonomous_control_towers_in_retail_consumer_packaged_goods_supply_chains)
[10] [https://www.ascm.org](https://www.ascm.org/ascm-insights/what-can-machine-learning-do-for-your-supply-chain/)
[11] [https://www.youtube.com](https://www.youtube.com/watch?v=jwaLXv1U07k)
[12] [https://www.youtube.com](https://www.youtube.com/watch?v=IzPw02jAtkU&t=17)
[13] [https://dl.acm.org](https://dl.acm.org/doi/10.1145/3674029.3674036)
[14] [https://academic.oup.com](https://academic.oup.com/imaman/advance-article/doi/10.1093/imaman/dpag002/8435240?searchresult=1)
[15] [https://www.netstock.com](https://www.netstock.com/blog/ai-powered-abc-classification/)
[16] [https://www.sciencedirect.com](https://www.sciencedirect.com/science/article/abs/pii/S0957417410009358)
[17] [https://bizom.com](https://bizom.com/blog/top-7-inventory-management-challenges-and-solutions/)
