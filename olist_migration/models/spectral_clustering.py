from pathlib import Path
from typing import Dict, Optional, Tuple
import json
import warnings

import numpy as np
import pandas as pd
import yaml
from cluster_profiler import ClusterGeometryProfiler
from sklearn.cluster import KMeans
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    pairwise_distances,
    silhouette_score,
)

from kmds_modeling.core.notebook_utils import build_notebook_resolver


def _load_config(config_path: str) -> Dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _read_dataset(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    if path.suffix == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Unsupported dataset extension: {path.suffix}")


def _build_tfidf_matrix(df: pd.DataFrame) -> np.ndarray:
    values = df.astype(float).to_numpy()
    row_sums = values.sum(axis=1, keepdims=True)
    term_frequency = np.divide(
        values, row_sums, out=np.zeros_like(values), where=row_sums != 0
    )
    document_frequency = np.count_nonzero(values, axis=0)
    inverse_document_frequency = (
        np.log((1.0 + values.shape[0]) / (1.0 + document_frequency)) + 1.0
    )
    return term_frequency * inverse_document_frequency


def _prepare_model_matrix(
    df: pd.DataFrame, random_state: int, feature_report_path: Optional[Path] = None
) -> pd.DataFrame:
    """Apply the profiler's label-free feature screening before graph construction."""
    candidate_df = df.drop(columns=["woy", "cluster"], errors="ignore")
    candidate_df = candidate_df.loc[
        :, ~candidate_df.columns.str.startswith("Unnamed: ", na=False)
    ]
    if candidate_df.empty:
        raise ValueError("No candidate product features remain after geometry screening.")

    retained = []
    if feature_report_path is not None and feature_report_path.exists():
        with feature_report_path.open("r", encoding="utf-8") as report_file:
            report = json.load(report_file)
        retained = list(
            report["executive_summary"]["exports"]["filtered_dataset"][
                "retained_feature_names"
            ]
        )
    if not retained:
        profiler = ClusterGeometryProfiler(random_state=random_state).fit_audit(
            candidate_df,
            invariance="none",
            feature_names=candidate_df.columns.tolist(),
        )
        retained = profiler.retained_feature_names
    retained = [name for name in retained if name in candidate_df]
    if not retained:
        raise ValueError("ClusterGeometryProfiler did not retain any clustering features.")

    result = candidate_df[retained].copy()
    result.insert(0, "woy", df["woy"].astype(str).values)
    return result


def _build_local_scaled_graph(
    features: np.ndarray, n_neighbors: int, sigma_neighbors: int
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build a mutual k-NN graph with Zelnik-Manor/Perona local RBF scaling."""
    distances = pairwise_distances(features, metric="cosine")
    np.fill_diagonal(distances, 0.0)
    n_observations = distances.shape[0]
    if n_neighbors >= n_observations:
        n_neighbors = n_observations - 1
    sigma_neighbors = min(max(1, sigma_neighbors), n_neighbors)

    neighbor_order = np.argsort(distances, axis=1)
    neighbors = neighbor_order[:, 1 : n_neighbors + 1]
    mutual = np.zeros_like(distances, dtype=bool)
    mutual[np.arange(n_observations)[:, None], neighbors] = True
    mutual &= mutual.T

    sorted_distances = np.sort(distances, axis=1)
    local_scale = sorted_distances[:, sigma_neighbors].copy()
    positive_distances = distances[distances > 0]
    if positive_distances.size == 0:
        raise ValueError("Cosine distances are all zero; no spectral graph can be built.")
    fallback_scale = float(np.median(positive_distances))
    local_scale[local_scale <= 0] = fallback_scale

    affinity = np.exp(
        -(distances**2)
        / (np.outer(local_scale, local_scale) + np.finfo(float).eps)
    )
    affinity *= mutual
    np.fill_diagonal(affinity, 0.0)

    # A mutual graph may isolate a sample. Add only its strongest reciprocal edge.
    isolated = np.flatnonzero(affinity.sum(axis=1) == 0)
    for row in isolated:
        column = int(neighbors[row, 0])
        weight = np.exp(
            -(distances[row, column] ** 2)
            / (2.0 * max(local_scale[row], local_scale[column]) ** 2 + 1e-12)
        )
        affinity[row, column] = weight
        affinity[column, row] = weight

    degrees = affinity.sum(axis=1)
    inverse_sqrt_degree = np.divide(
        1.0, np.sqrt(degrees), out=np.zeros_like(degrees), where=degrees > 0
    )
    laplacian = np.eye(n_observations) - (
        inverse_sqrt_degree[:, None] * affinity * inverse_sqrt_degree[None, :]
    )
    return affinity, distances, laplacian


def _spectral_decomposition(
    features: np.ndarray, n_neighbors: int, sigma_neighbors: int
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    affinity, distances, laplacian = _build_local_scaled_graph(
        features, n_neighbors, sigma_neighbors
    )
    eigenvalues, eigenvectors = np.linalg.eigh(laplacian)
    return affinity, distances, eigenvalues, eigenvectors


def _row_normalize_embedding(eigenvectors: np.ndarray, n_clusters: int) -> np.ndarray:
    embedding = eigenvectors[:, 1:n_clusters].copy()
    norms = np.linalg.norm(embedding, axis=1, keepdims=True)
    return np.divide(embedding, norms, out=np.zeros_like(embedding), where=norms > 0)


def _fit_clusters(
    eigenvectors: np.ndarray, n_clusters: int, random_state: int
) -> Tuple[np.ndarray, np.ndarray]:
    embedding = _row_normalize_embedding(eigenvectors, n_clusters)
    model = KMeans(n_clusters=n_clusters, n_init=50, random_state=random_state)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        labels = model.fit_predict(embedding)
    return labels, embedding


def _select_cluster_count(eigenvalues: np.ndarray, max_clusters: int) -> int:
    """Select the first secondary gap at least 75% of the primary gap."""
    primary_gap = eigenvalues[2] - eigenvalues[1]
    candidate_counts = np.arange(3, max_clusters + 1)
    gaps = eigenvalues[candidate_counts] - eigenvalues[candidate_counts - 1]
    qualifying = candidate_counts[gaps >= 0.75 * primary_gap]
    if qualifying.size == 0:
        return 2
    return int(qualifying[0])


def _cluster_validation(
    feature_frame: pd.DataFrame,
    eigenvectors: np.ndarray,
    n_neighbors: int,
    sigma_neighbors: int,
    random_state: int,
    repetitions: int = 50,
) -> pd.DataFrame:
    """Evaluate geometry and 80% week-subset stability around plausible K."""
    rows = []
    rng = np.random.default_rng(random_state)
    sample_size = int(round(0.8 * len(feature_frame)))
    for n_clusters in range(2, 7):
        labels, embedding = _fit_clusters(eigenvectors, n_clusters, random_state)
        ari_scores = []
        for _ in range(repetitions):
            indices = np.sort(rng.choice(len(feature_frame), sample_size, replace=False))
            sample_features = _build_tfidf_matrix(feature_frame.iloc[indices])
            _, _, _, sample_eigenvectors = _spectral_decomposition(
                sample_features, n_neighbors, sigma_neighbors
            )
            sample_labels, _ = _fit_clusters(
                sample_eigenvectors, n_clusters, random_state
            )
            ari_scores.append(adjusted_rand_score(labels[indices], sample_labels))
        rows.append(
            {
                "n_clusters": n_clusters,
                "silhouette": silhouette_score(embedding, labels),
                "davies_bouldin": davies_bouldin_score(embedding, labels),
                "calinski_harabasz": calinski_harabasz_score(embedding, labels),
                "subsample_ari_mean": float(np.mean(ari_scores)),
                "subsample_ari_sd": float(np.std(ari_scores)),
                "subsample_ari_min": float(np.min(ari_scores)),
            }
        )
    return pd.DataFrame(rows)


def run_spectral_clustering(
    config_path: str,
    output_dir: Optional[str] = None,
    n_clusters: Optional[int] = None,
    embedding_dim: Optional[int] = None,
    random_state: int = 42,
    use_tfidf: bool = True,
) -> Dict[str, str]:
    config_path = Path(config_path).resolve()
    workspace_root = config_path.parent
    resolver = build_notebook_resolver(str(workspace_root), config_name=config_path.name)
    config = _load_config(str(config_path))
    algorithm = config.get("algorithm", {})

    df = _read_dataset(Path(resolver.model_ready_dataset_path))
    if "woy" not in df.columns:
        raise ValueError("Expected 'woy' in the model-ready dataset.")
    feature_report = algorithm.get(
        "feature_screening_report", "data/SP_2017_cluster_feature_report.json"
    )
    screened_df = _prepare_model_matrix(
        df, int(random_state), workspace_root / feature_report
    )
    week_labels = screened_df["woy"].astype(str).tolist()
    retained_feature_frame = screened_df.drop(columns=["woy"])
    if not use_tfidf:
        model_features = retained_feature_frame.astype(float).to_numpy()
    else:
        model_features = _build_tfidf_matrix(retained_feature_frame)

    n_neighbors = int(algorithm.get("mutual_knn_neighbors", 10))
    sigma_neighbors = int(algorithm.get("local_sigma_neighbor", 7))
    if not 1 <= sigma_neighbors <= n_neighbors:
        raise ValueError("local_sigma_neighbor must be between 1 and mutual_knn_neighbors.")
    max_clusters = min(int(algorithm.get("max_clusters", 10)), len(week_labels) - 1)
    affinity, distances, eigenvalues, eigenvectors = _spectral_decomposition(
        model_features, n_neighbors, sigma_neighbors
    )
    selected_n_clusters = (
        _select_cluster_count(eigenvalues, max_clusters)
        if n_clusters is None
        else int(n_clusters)
    )
    week_labels_out, week_embedding_values = _fit_clusters(
        eigenvectors, selected_n_clusters, int(random_state)
    )
    week_clusters = pd.DataFrame({"woy": week_labels, "cluster": week_labels_out})
    week_embedding = pd.DataFrame(
        week_embedding_values,
        columns=[f"emb_{i + 1}" for i in range(week_embedding_values.shape[1])],
    )
    week_embedding.insert(0, "woy", week_labels)
    validation = _cluster_validation(
        retained_feature_frame,
        eigenvectors,
        n_neighbors,
        sigma_neighbors,
        int(random_state),
    )
    raw_features = df.drop(columns=["woy"], errors="ignore")
    domain_profile = pd.DataFrame(
        {
            "woy": week_labels,
            "total_revenue": raw_features.sum(axis=1).to_numpy(),
            "active_products": (raw_features > 0).sum(axis=1).to_numpy(),
            "cluster": week_labels_out,
        }
    ).groupby("cluster", as_index=False).agg(
        weeks=("woy", "size"),
        mean_total_revenue=("total_revenue", "mean"),
        median_total_revenue=("total_revenue", "median"),
        mean_active_products=("active_products", "mean"),
        first_week=("woy", lambda values: min(map(int, values))),
        last_week=("woy", lambda values: max(map(int, values))),
    )

    output_path = (
        Path(output_dir) if output_dir is not None else Path(resolver.modeling_output_path)
    )
    output_path.mkdir(parents=True, exist_ok=True)

    spectral_gap = pd.DataFrame(
        {
            "component": np.arange(len(eigenvalues)),
            "eigenvalue": eigenvalues,
            "eigengap": np.append(np.diff(eigenvalues), np.nan),
        }
    )
    spectral_gap["cluster_count_after_gap"] = spectral_gap["component"] + 1
    stability_rows = []
    for sigma_rank in range(max(1, sigma_neighbors - 1), sigma_neighbors + 2):
        _, _, perturbed_eigenvalues, perturbed_eigenvectors = _spectral_decomposition(
            model_features, n_neighbors, sigma_rank
        )
        perturbed_labels, _ = _fit_clusters(
            perturbed_eigenvectors, selected_n_clusters, int(random_state)
        )
        selected_gap = (
            perturbed_eigenvalues[selected_n_clusters]
            - perturbed_eigenvalues[selected_n_clusters - 1]
        )
        stability_rows.append(
            {
                "sigma_neighbor": sigma_rank,
                "selected_k": selected_n_clusters,
                "selected_eigengap": selected_gap,
                "adjusted_rand_vs_central_sigma": adjusted_rand_score(
                    week_labels_out, perturbed_labels
                ),
            }
        )
    stability = pd.DataFrame(stability_rows)
    gap_path = output_path / "spectral_gap.csv"
    week_clusters_path = output_path / "week_clusters.csv"
    week_embedding_path = output_path / "week_embeddings.csv"
    affinity_path = output_path / "week_affinity.csv"
    stability_path = output_path / "spectral_gap_stability.csv"
    validation_path = output_path / "cluster_validation.csv"
    domain_profile_path = output_path / "week_cluster_domain_profile.csv"
    summary_path = output_path / "spectral_clustering_summary.md"

    spectral_gap.to_csv(gap_path, index=False)
    week_clusters.to_csv(week_clusters_path, index=False)
    week_embedding.to_csv(week_embedding_path, index=False)
    pd.DataFrame(affinity, index=week_labels, columns=week_labels).to_csv(affinity_path)
    stability.to_csv(stability_path, index=False)
    validation.to_csv(validation_path, index=False)
    domain_profile.to_csv(domain_profile_path, index=False)
    median_local_sigma = float(
        np.median(np.sort(distances, axis=1)[:, sigma_neighbors])
    )
    summary_path.write_text(
        "\n".join(
            [
                "# Spectral Clustering Artifacts",
                "",
                f"- Input dataset: {resolver.model_ready_dataset_path}",
                f"- Screened features: {retained_feature_frame.shape[1]}",
                f"- Graph: mutual {n_neighbors}-NN with local RBF sigma from neighbor {sigma_neighbors}",
                f"- Median local sigma: {median_local_sigma:.4f}",
                f"- Laplacian: symmetric normalized",
                f"- Primary eigengap candidate: 2",
                f"- Selected first substantial secondary eigengap: {selected_n_clusters}",
                f"- Mean adjacent-sigma ARI stability: {stability['adjusted_rand_vs_central_sigma'].mean():.4f}",
                f"- Mean 50-run subsample ARI for selected K: {validation.loc[validation['n_clusters'].eq(selected_n_clusters), 'subsample_ari_mean'].iloc[0]:.4f}",
                f"- Saved spectral gap analysis: {gap_path}",
                f"- Saved local-sigma stability: {stability_path}",
                f"- Saved geometric and subsample validation: {validation_path}",
                f"- Saved domain profile: {domain_profile_path}",
                f"- Saved week affinity: {affinity_path}",
                f"- Saved week clusters: {week_clusters_path}",
                f"- Saved week embeddings: {week_embedding_path}",
            ]
        ),
        encoding="utf-8",
    )

    return {
        "spectral_gap": str(gap_path),
        "spectral_gap_stability": str(stability_path),
        "cluster_validation": str(validation_path),
        "week_cluster_domain_profile": str(domain_profile_path),
        "week_affinity": str(affinity_path),
        "week_clusters": str(week_clusters_path),
        "week_embeddings": str(week_embedding_path),
        "summary": str(summary_path),
    }
