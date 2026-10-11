import hdbscan
import numpy as np
from typing import List, Dict

class SemanticClusterer:
    def __init__(self, min_cluster_size: int = 5, min_samples: int = 2):
        """
        Uses HDBSCAN for clustering embeddings.
        It doesn't require knowing the number of clusters a priori,
        which is ideal for discovering unknown recurring themes.
        """
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self.clusterer = hdbscan.HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            min_samples=self.min_samples,
            metric='euclidean' # embeddings are normalized, so euclidean is proportional to cosine
        )
        
    def fit_predict(self, embeddings: np.ndarray) -> List[int]:
        """
        Clusters the given embeddings. Returns a list of cluster IDs.
        Noise points are assigned a cluster ID of -1.
        """
        if len(embeddings) < self.min_cluster_size:
            return [-1] * len(embeddings)
            
        labels = self.clusterer.fit_predict(embeddings)
        return labels.tolist()

if __name__ == "__main__":
    # Generate random normalized embeddings for testing
    np.random.seed(42)
    test_embs = np.random.randn(20, 384)
    test_embs = test_embs / np.linalg.norm(test_embs, axis=1, keepdims=True)
    
    clusterer = SemanticClusterer(min_cluster_size=3)
    labels = clusterer.fit_predict(test_embs)
    print(f"Cluster labels: {labels}")
