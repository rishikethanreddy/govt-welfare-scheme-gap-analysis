from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np

class TextEncoder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initializes the sentence transformer model.
        Using a small, fast model suitable for CPU processing by default.
        """
        print(f"Loading SentenceTransformer: {model_name}...")
        self.model = SentenceTransformer(model_name)
        print("Model loaded.")
        
    def encode(self, texts: List[str]) -> np.ndarray:
        """
        Generates embeddings for a list of texts.
        """
        # normalize_embeddings=True for cosine similarity compatibility
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings

if __name__ == "__main__":
    encoder = TextEncoder()
    texts = ["Can a tenant farmer get PM Kisan?", "Are tenant farmers eligible?"]
    embeddings = encoder.encode(texts)
    
    # Calculate cosine similarity of the two texts
    similarity = np.dot(embeddings[0], embeddings[1])
    print(f"Cosine Similarity: {similarity:.4f}")
