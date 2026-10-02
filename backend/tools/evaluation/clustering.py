"""
DataWise AI — Evaluation: Clustering Validation
"""

from typing import Any, Dict
import numpy as np
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)


def evaluate_clustering(X: Any, labels: Any) -> Dict[str, Any]:
    """Calculates internal clustering validity indices."""
    unique_clusters = len(np.unique(labels))
    if unique_clusters < 2:
        return {"silhouette_score": None, "note": "Less than 2 clusters found"}

    sil = float(silhouette_score(X, labels))
    ch = float(calinski_harabasz_score(X, labels))
    db = float(davies_bouldin_score(X, labels))

    return {
        "n_clusters": unique_clusters,
        "silhouette_score": round(sil, 4),
        "calinski_harabasz_score": round(ch, 2),
        "davies_bouldin_score": round(db, 4),
    }
