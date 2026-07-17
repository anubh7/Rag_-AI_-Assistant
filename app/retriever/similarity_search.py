"""
Plain vector similarity search over a LangChain Qdrant vector store.
Supports an optional pre-filter (qdrant_client.models.Filter) that narrows
the candidate vectors before scoring, so only matching payload docs are returned.
"""
from typing import List, Optional, Tuple
from langchain_core.documents import Document


def similarity_search(
    store,
    query: str,
    top_k: int,
    qdrant_filter=None,
) -> List[Tuple[Document, float]]:
    """
    Returns list of (Document, score) tuples, most relevant first.

    Args:
        store:          LangChain QdrantVectorStore instance.
        query:          User's search query string.
        top_k:          Maximum number of results to return.
        qdrant_filter:  Optional qdrant_client.models.Filter. When supplied,
                        Qdrant pre-filters the vector space to only chunks
                        whose payload satisfies the filter before scoring.
    """
    return store.similarity_search_with_score(
        query,
        k=top_k,
        filter=qdrant_filter,
    )

