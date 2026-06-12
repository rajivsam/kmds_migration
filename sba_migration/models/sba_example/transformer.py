import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.cluster import DBSCAN, SpectralClustering
from sklearn.metrics import pairwise_distances

from ..core.base import BaseFeatureTransformer


def haversine_distance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return 6371.0 * c


class SBAClusterDistanceTransformer(BaseFeatureTransformer, BaseEstimator, TransformerMixin):
    """Derive hdgc and hdbc based on geographic clusters for SBA loans."""

    def __init__(self, lat_col="borrower_latitude", lon_col="borrower_longitude", n_clusters_max=6):
        self.lat_col = lat_col
        self.lon_col = lon_col
        self.n_clusters_max = n_clusters_max
        self.good_cluster_centers_ = None
        self.bad_cluster_centers_ = None
        self.feature_names_ = ["hdgc", "hdbc"]

    def fit(self, X: pd.DataFrame, y: pd.Series = None):
        if y is None:
            raise ValueError("SBAClusterDistanceTransformer requires a target series during fit.")

        coords = X[[self.lat_col, self.lon_col]].copy()
        good_points = coords.loc[y == 0].dropna()
        bad_points = coords.loc[y == 1].dropna()

        if len(good_points) < 2 or len(bad_points) < 2:
            raise ValueError("Not enough labeled geographic points in training set for clustering.")

        self.good_cluster_centers_ = self._fit_clusters(good_points)
        self.bad_cluster_centers_ = self._fit_clusters(bad_points)
        return self

    def _fit_clusters(self, points: pd.DataFrame):
        coords_deg = points[[self.lat_col, self.lon_col]].to_numpy()
        coords_rad = np.radians(coords_deg)
        if len(coords_deg) < 2:
            return np.asarray([coords_deg.mean(axis=0)])

        if len(coords_deg) > 500:
            dbscan = DBSCAN(eps=50 / 6371.0, min_samples=5, metric="haversine")
            labels = dbscan.fit_predict(coords_rad)
            if np.all(labels == -1):
                labels = np.zeros(len(coords_rad), dtype=int)
            best_labels = labels
        else:
            similarity = np.exp(-pairwise_distances(coords_rad, metric="haversine"))
            similarity[np.isnan(similarity)] = 0.0

            best_gap = -np.inf
            best_labels = None

            eigen_cache = np.linalg.eigvals(np.eye(len(coords_rad)) - similarity)

            for k in range(2, min(self.n_clusters_max, len(coords_deg) - 1) + 1):
                try:
                    model = SpectralClustering(
                        n_clusters=k,
                        affinity="precomputed",
                        assign_labels="discretize",
                        random_state=42,
                    )
                    labels = model.fit_predict(similarity)
                except Exception:
                    continue

                gap = np.real(eigen_cache[k] - eigen_cache[k - 1]) if len(eigen_cache) > k else 0.0
                if gap > best_gap:
                    best_gap = gap
                    best_labels = labels

            if best_labels is None:
                dbscan = DBSCAN(eps=50 / 6371.0, min_samples=5, metric="haversine")
                labels = dbscan.fit_predict(coords_rad)
                if np.all(labels == -1):
                    labels = np.zeros(len(coords_rad), dtype=int)
                best_labels = labels

        centers = []
        for cluster_id in np.unique(best_labels):
            cluster_coords = coords_deg[best_labels == cluster_id]
            centers.append(cluster_coords.mean(axis=0))

        return np.asarray(centers)

    def _nearest_cluster_distance(self, points, centers):
        if centers is None or len(centers) == 0:
            return np.full(len(points), np.nan)

        lat1 = points[:, 0][:, None]
        lon1 = points[:, 1][:, None]
        lat2 = centers[:, 0][None, :]
        lon2 = centers[:, 1][None, :]
        dists = haversine_distance(lat1, lon1, lat2, lon2)
        return np.min(dists, axis=1)

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        result = X.copy()
        coords = result[[self.lat_col, self.lon_col]].to_numpy()
        result["hdgc"] = self._nearest_cluster_distance(coords, self.good_cluster_centers_)
        result["hdbc"] = self._nearest_cluster_distance(coords, self.bad_cluster_centers_)
        return result

    def fit_transform(self, X: pd.DataFrame, y: pd.Series = None) -> pd.DataFrame:
        return self.fit(X, y).transform(X)
