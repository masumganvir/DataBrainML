"""
DataWise AI — Models: Clustering Candidate Estimators
"""

from typing import Any, Dict
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.mixture import GaussianMixture


def get_clustering_candidates(n_clusters: int = 3) -> Dict[str, Any]:
    """Returns unsupervised clustering candidates."""
    return {
        "KMeans": KMeans(n_clusters=n_clusters, random_state=42, n_init="auto"),
        "DBSCAN": DBSCAN(eps=0.5, min_samples=5),
        "Agglomerative": AgglomerativeClustering(n_clusters=n_clusters),
        "GaussianMixture": GaussianMixture(n_components=n_clusters, random_state=42),
    }
