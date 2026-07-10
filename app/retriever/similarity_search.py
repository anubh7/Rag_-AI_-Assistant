"""
Plain vector similarity search over a LangChain Qdrant vector store.
"""
from typing import List, Tuple
from langchain_core.documents import Document


def similarity_search(store, query: str, top_k: int) -> List[Tuple[Document, float]]:
    """Returns list of (Document, score) tuples, most relevant first."""
    return store.similarity_search_with_score(query, k=top_k)
