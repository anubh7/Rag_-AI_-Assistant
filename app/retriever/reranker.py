"""
Lightweight reranking step applied after initial retrieval.
Placeholder for a cross-encoder reranker; currently re-sorts by score
and truncates to top_k, with a hook to plug in a real reranker model later.
"""
from typing import List, Tuple
from langchain_core.documents import Document


def rerank(results: List[Tuple[Document, float]], top_k: int) -> List[Tuple[Document, float]]:
    results = sorted(results, key=lambda x: x[1], reverse=True)
    return results[:top_k]
