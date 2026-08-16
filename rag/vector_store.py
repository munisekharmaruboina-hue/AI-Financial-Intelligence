import numpy as np
from rag.embedding import embed_texts


class SimpleVectorStore:
    def __init__(self, texts: list[str], vectors: list[list[float]]):
        self.texts = texts
        self.vectors = np.array(vectors)

    def similarity_search(self, query_vector: list[float], k: int = 5) -> list[str]:
        query_vec = np.array(query_vector)
        norms = np.linalg.norm(self.vectors, axis=1) * np.linalg.norm(query_vec)
        norms[norms == 0] = 1e-10  # avoid divide-by-zero
        scores = (self.vectors @ query_vec) / norms
        top_k_idx = np.argsort(scores)[::-1][:k]
        return [self.texts[i] for i in top_k_idx]


def build_ephemeral_store(documents: list[str]):
    if not documents:
        return None

    vectors = embed_texts(documents)
    return SimpleVectorStore(documents, vectors)