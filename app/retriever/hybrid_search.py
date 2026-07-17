"""
Hybrid search — combines dense vector similarity with simple keyword (BM25-style)
overlap scoring for cases where exact term matches matter (e.g. names, codes).
Supports an optional qdrant_filter to pre-filter the vector space before retrieval.
"""
from typing import List, Tuple
from langchain_core.documents import Document
from app.retriever.similarity_search import similarity_search


def _keyword_overlap_score(query: str, text: str) -> float:
    q_tokens = set(query.lower().split())
    t_tokens = set(text.lower().split())
    if not q_tokens:
        return 0.0
    return len(q_tokens & t_tokens) / len(q_tokens)


def hybrid_search(
    store,
    query: str,
    top_k: int,
    alpha: float = 0.75,
    qdrant_filter=None,
) -> List[Tuple[Document, float]]:
    """
    alpha weights vector score vs keyword score (alpha=1 → pure vector).

    Args:
        store:          LangChain QdrantVectorStore instance.
        query:          User's search query string.
        top_k:          Final number of results to return.
        alpha:          Blend weight: 1.0 = pure vector, 0.0 = pure keyword.
        qdrant_filter:  Optional qdrant_client.models.Filter forwarded to
                        the underlying similarity search to pre-filter results.
    """
    vector_results = similarity_search(store, query, top_k=top_k * 2, qdrant_filter=qdrant_filter)

    rescored = []
    for doc, vec_score in vector_results:
        kw_score = _keyword_overlap_score(query, doc.page_content)
        final_score = alpha * vec_score + (1 - alpha) * kw_score
        rescored.append((doc, final_score))

    rescored.sort(key=lambda x: x[1], reverse=True)
    return rescored[:top_k]
