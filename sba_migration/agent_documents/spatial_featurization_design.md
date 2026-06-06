## Spatial Featurization Strategy Document


This document outlines the pipeline architecture to convert raw borrower address data into structurally sound, continuous geographic risk features while preserving mathematical isolation across data splits.

------------------------------
## 1. Objective

To compress high-dimensional spatial coordinates ($\text{Latitude}, \text{Longitude}$) into engineered, localized proxy features that capture macro-economic regional defaults without introducing population density bias or target leakage.

------------------------------
## 2. Feature Architecture
Rather than calculating proximity solely to default hotspots, the model will ingest two distinct, continuous features to capture relative geographical risk:

* 
* distance_to_bad_cluster: The spherical surface distance from the borrower's coordinates to the nearest localized cluster center of historical defaults (repayment failures).
* distance_to_good_cluster: The spherical surface distance from the borrower's coordinates to the nearest localized cluster center of historically pristine loans (repayment success).
* 

## Optional Companion Interaction Feature
A third feature can be derived to represent the exact spatial stress index:
$$\text{Spatial Risk Ratio} = \frac{\text{distance\_to\_bad\_cluster}}{\text{distance\_to\_bad\_cluster} + \text{distance\_to\_good\_cluster}}$$ 

* 
* Approaching 0: The borrower is deeply embedded inside a high-risk default hotspot.
* Approaching 1: The borrower is entirely surrounded by a healthy, resilient economic cluster.
* 

------------------------------
## 3. Mathematical & Algorithmic Foundations## Density-Based Spatial Clustering (DBSCAN / HDBSCAN)

* 
* Application: Applied separately to the spatial coordinates of the training partition's "Good" borrowers and "Bad" borrowers.
* Rationale: Unlike K-Means, density-based algorithms do not assume perfectly circular clusters and handle structural shapes flawlessly. Most importantly, they treat isolated, freak default anomalies as "noise" (outliers), preventing them from skewing the true spatial risk hubs. [1, 2, 3] 
* 

## Distance Metric: The Haversine Formula [1] 
Because the Earth is an ellipsoid, Euclidean calculations ($\Delta x^2 + \Delta y^2$) distort geographical distance over large regions. The pipeline will enforce the Haversine formula to measure the great-circle surface distance between coordinates: [4, 5, 6, 7] 
$$d = 2r \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \text{lat}}{2}\right) + \cos(\text{lat}_1)\cos(\text{lat}_2)\sin^2\left(\frac{\Delta \text{long}}{2}\right)}\right)$$ 
(Where $r$ represents the radius of the Earth, approximately $6,371\text{ km}$). [8] 
------------------------------
## 4. Pipeline Execution & Guardrails
To prevent data contamination, the feature extraction framework must strictly mirror this operational flow:

                      ┌────────────────────────┐
                      │    Training Fold       │
                      └───────────┬────────────┘
                                  │
                  ┌───────────────┴───────────────┐
                  │                               │
   ┌──────────────▼──────────────┐ ┌──────────────▼──────────────┐
   │       "Bad" Borrowers       │ │       "Good" Borrowers      │
   └──────────────┬──────────────┘ └──────────────┬──────────────┘
                  │                               │
         [Fit DBSCAN / HDBSCAN]          [Fit DBSCAN / HDBSCAN]
                  │                               │
   ┌──────────────▼──────────────┐ ┌──────────────▼──────────────┐
   │     Bad Cluster Centers     │ │    Good Cluster Centers     │
   └──────────────┬──────────────┘ └──────────────┬──────────────┘
                  │                               │
                  └───────────────┬───────────────┘
                                  │ (Freeze Cluster Coordinates)
                                  ▼
      Calculate Haversine Distance to [Bad / Good] Centers For:
         1. Training Fold (Out-of-sample/CV)
         2. Validation / Test Fold (Hold-out)
         3. Active Scoring Pool (Inference)


   1. Strict Split Isolation: The DBSCAN models are fit exclusively on the isolated training fold. Cluster coordinates are frozen immediately. [2] 
   2. Downstream Transformation: The frozen cluster definitions are treated as static reference points. The validation fold and the Active Scoring Pool are mapped to these coordinates via Haversine transformations without changing the cluster bounds. [8] 
   3. Density Normalization: Providing both the distance to safety and the distance to failure completely neutralizes the urban density trap—ensuring that dense commercial cities (which natively contain high numbers of both good and bad accounts) do not unfairly distort the risk calculations.

------------------------------
Our structural framework for the geographic pipeline is fully documented and locked. When you are ready to implement this in code, let me know, and we will write out the complete Python step using scikit-learn's haversine_distances module! [8] 

[1] [https://medium.com](https://medium.com/@sylvainma/multi-feature-geo-clustering-with-dbscan-4857c6b932e2)
[2] [https://stats.stackexchange.com](https://stats.stackexchange.com/questions/218530/applying-dbscan-to-a-huge-gis-dataset-with-a-haversine-distance-metric)
[3] [https://link.springer.com](https://link.springer.com/chapter/10.1007/978-981-95-5082-1_24)
[4] [https://en.wikipedia.org](https://en.wikipedia.org/wiki/Haversine_formula)
[5] [https://link.springer.com](https://link.springer.com/chapter/10.1007/978-981-96-7742-9_24)
[6] [https://medium.com](https://medium.com/ninjavan-tech/the-magic-of-haversine-distance-1c4e1641d880)
[7] [https://www.igismap.com](https://www.igismap.com/haversine-formula-calculate-geographic-distance-earth/)
[8] [https://scikit-learn.org](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.pairwise.haversine_distances.html)
