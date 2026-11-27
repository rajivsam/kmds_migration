import math
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
import yaml
from cluster_profiler import ClusterGeometryProfiler
from sklearn.cluster import KMeans

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
    A = df.astype(float).values
    row_sums = A.sum(axis=1, keepdims=True)
    tf = np.divide(A, row_sums, out=np.zeros_like(A), where=row_sums != 0)
    df_counts = np.count_nonzero(A, axis=0)
    n_weeks = A.shape[0]
    idf = np.log((1.0 + n_weeks) / (1.0 + df_counts)) + 1.0
    return tf * idf


def _build_normalized_affinity(A: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    D1 = np.maximum(A.sum(axis=1), 1.0)
    D2 = np.maximum(A.sum(axis=0), 1.0)
    D1_inv_sqrt = np.diag(1.0 / np.sqrt(D1))
    D2_inv_sqrt = np.diag(1.0 / np.sqrt(D2))
    B = D1_inv_sqrt @ A @ D2_inv_sqrt
    return B, D1_inv_sqrt, D2_inv_sqrt, D1, D2


def _build_spectral_gap_df(singular_values: np.ndarray) -> pd.DataFrame:
    gaps = np.diff(singular_values)
    return pd.DataFrame(
        {
            "component": np.arange(1, len(singular_values) + 1),
            "singular_value": singular_values,
            "gap": np.append(gaps, np.nan),
        }
    )


def _select_cluster_count_from_spectral_gap(singular_values: np.ndarray, min_clusters: int = 2) -> int:
    if singular_values.size < 2:
        return max(1, min_clusters)

    gaps = np.diff(singular_values)
    if np.all(gaps <= 0):
        return max(2, min_clusters)

    best_index = int(np.argmax(gaps))
    n_clusters = best_index + 1
    n_clusters = max(min_clusters, min(int(n_clusters), singular_values.size - 1))
    return n_clusters


def _build_joint_embedding(
    U: np.ndarray,
    Vt: np.ndarray,
    D1_inv_sqrt: np.ndarray,
    D2_inv_sqrt: np.ndarray,
    embedding_dim: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    max_dim = min(U.shape[1], Vt.shape[0]) - 1
    if embedding_dim > max_dim:
        embedding_dim = max_dim
    if embedding_dim < 1:
        raise ValueError("embedding_dim must be at least 1")

    Ul = D1_inv_sqrt @ U[:, 1 : (embedding_dim + 1)]
    Vl = D2_inv_sqrt @ Vt.T[:, 1 : (embedding_dim + 1)]
    Z = np.vstack([Ul, Vl])
    return Z, Ul, Vl


def _fit_kmeans(Z: np.ndarray, n_clusters: int, random_state: int) -> Tuple[np.ndarray, KMeans]:
    model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init="auto")
    labels = model.fit_predict(Z)
    return labels, model


def _to_dataframe(embedding: np.ndarray, names: list[str], prefix: str) -> pd.DataFrame:
    columns = [f"emb_{i+1}" for i in range(embedding.shape[1])]
    df = pd.DataFrame(embedding, columns=columns)
    df.index = names
    df.insert(0, prefix, names)
    return df


def _prepare_model_matrix(df: pd.DataFrame, random_state: int) -> pd.DataFrame:
    """Screen the raw product matrix for sparse, zero-spread, and redundant features before clustering."""
    dropped_names = {"woy", "cluster"}
    candidate_df = df.drop(columns=[col for col in df.columns if col in dropped_names], errors="ignore")
    candidate_df = candidate_df.loc[:, ~candidate_df.columns.str.startswith("Unnamed: ", na=False)]
    if candidate_df.empty:
        raise ValueError("No candidate product features remain after geometry screening.")

    profiler = ClusterGeometryProfiler(random_state=random_state).fit_audit(
        candidate_df,
        invariance="none",
        feature_names=candidate_df.columns.tolist(),
    )
    retained = profiler.retained_feature_names
    retained = [col for col in retained if col in candidate_df.columns]
    if not retained:
        raise ValueError("ClusterGeometryProfiler did not retain any features for clustering.")

    geometry_filtered = candidate_df[retained].copy()
    if "woy" in df.columns:
        geometry_filtered.insert(0, "woy", df["woy"].astype(str).values)
    return geometry_filtered


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

    df = _read_dataset(Path(resolver.model_ready_dataset_path))
    if "cluster" in df.columns:
        df = df.drop(columns=["cluster"])
    if "Unnamed: 0" in df.columns:
        df = df.drop(columns=["Unnamed: 0"])

    if "woy" not in df.columns:
        raise ValueError("Expected 'woy' column in the model-ready dataset after geometry screening.")

    df = _prepare_model_matrix(df, int(random_state))
    feature_df = df.drop(columns=["woy"])  # Each column corresponds to retained product activity.
    product_labels = feature_df.columns.tolist()
    week_labels = df["woy"].astype(str).tolist()
    A = _build_tfidf_matrix(feature_df) if use_tfidf else feature_df.fillna(0).astype(float).values

    B, D1_inv_sqrt, D2_inv_sqrt, D1, D2 = _build_normalized_affinity(A)
    U, singular_values, Vt = np.linalg.svd(B, full_matrices=False)
    gap_df = _build_spectral_gap_df(singular_values)

    config = _load_config(str(config_path))
    use_spectral_gap = bool(config.get("algorithm", {}).get("use_spectral_gap_analysis", True))

    if n_clusters is None:
        if use_spectral_gap:
            n_clusters = _select_cluster_count_from_spectral_gap(singular_values)
        else:
            n_clusters = config.get("algorithm", {}).get("n_clusters")
            if n_clusters is None:
                n_clusters = 2
            n_clusters = int(n_clusters)
    if embedding_dim is None:
        embedding_dim = int(config.get("algorithm", {}).get("embedding_dim", 4))

    Z, Ul, Vl = _build_joint_embedding(U, Vt, D1_inv_sqrt, D2_inv_sqrt, int(embedding_dim))
    labels, model = _fit_kmeans(Z, int(n_clusters), int(random_state))

    week_labels_out = labels[: len(week_labels)]
    product_labels_out = labels[len(week_labels) :]
    week_clusters = pd.DataFrame({"woy": week_labels, "cluster": week_labels_out})
    product_clusters = pd.DataFrame({"product_id": product_labels, "cluster": product_labels_out})
    week_embedding = _to_dataframe(Ul, week_labels, "woy")
    product_embedding = _to_dataframe(Vl, product_labels, "product_id")

    if output_dir is None:
        output_dir = Path(resolver.modeling_output_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    gap_path = output_dir / "spectral_gap.csv"
    week_clusters_path = output_dir / "week_clusters.csv"
    product_clusters_path = output_dir / "product_clusters.csv"
    week_embedding_path = output_dir / "week_embeddings.csv"
    product_embedding_path = output_dir / "product_embeddings.csv"
    joint_embedding_path = output_dir / "joint_embedding.parquet"
    summary_path = output_dir / "spectral_clustering_summary.md"

    gap_df.to_csv(gap_path, index=False)
    week_clusters.to_csv(week_clusters_path, index=False)
    product_clusters.to_csv(product_clusters_path, index=False)
    week_embedding.to_csv(week_embedding_path, index=False)
    product_embedding.to_csv(product_embedding_path, index=False)
    pd.DataFrame(Z).to_parquet(joint_embedding_path, index=False)

    cluster_counts = pd.DataFrame(
        {
            "week_cluster": week_clusters["cluster"].value_counts(sort=False),
            "product_cluster": product_clusters["cluster"].value_counts(sort=False),
        }
    ).fillna(0).astype(int)
    cluster_counts.to_csv(output_dir / "cluster_counts.csv")

    summary_text = [
        "# Spectral Co-Clustering Artifacts",
        "",
        "This output was generated from the Olist SP 2017 weekly product matrix using a normalized bipartite spectral co-clustering algorithm.",
        "",
        f"- Input dataset: {resolver.model_ready_dataset_path}",
        f"- Cluster count selected from the spectral gap heuristic: {n_clusters}",
        f"- Saved week clusters: {week_clusters_path}",
        f"- Saved product clusters: {product_clusters_path}",
        f"- Saved spectral gap analysis: {gap_path}",
        f"- Saved week embeddings: {week_embedding_path}",
        f"- Saved product embeddings: {product_embedding_path}",
        f"- Saved cluster counts: {output_dir / 'cluster_counts.csv'}",
    ]
    summary_path.write_text("\n".join(summary_text), encoding="utf-8")

    return {
        "spectral_gap": str(gap_path),
        "week_clusters": str(week_clusters_path),
        "product_clusters": str(product_clusters_path),
        "week_embeddings": str(week_embedding_path),
        "product_embeddings": str(product_embedding_path),
        "cluster_counts": str(output_dir / "cluster_counts.csv"),
        "joint_embedding": str(joint_embedding_path),
        "summary": str(summary_path),
    }
