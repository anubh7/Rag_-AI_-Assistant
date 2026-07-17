"""
RetrievalService — owns the read path: similarity/hybrid search + rerank.
Now supports optional metadata-based payload filtering via Qdrant's Filter API.
"""
from typing import List, Optional, Tuple
from langchain_core.documents import Document

from app.config import settings
from app.vector_db.qdrant_service import QdrantService
from app.retriever.similarity_search import similarity_search
from app.retriever.hybrid_search import hybrid_search
from app.retriever.reranker import rerank
from app.retriever.filter_builder import build_qdrant_filter
from app.utils.exceptions import CollectionNotFoundError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RetrievalService:
    def __init__(self, qdrant_service: QdrantService):
        self.qdrant_service = qdrant_service

    def retrieve(
        self,
        query: str,
        collection_name: str = None,
        top_k: int = None,
        use_hybrid: bool = False,
        filters=None,
    ) -> List[Tuple[Document, float]]:
        """
        Retrieve relevant document chunks for the given query.

        Args:
            query:           User's natural language query.
            collection_name: Qdrant collection to search in.
            top_k:           Maximum number of chunks to return after reranking.
            use_hybrid:      When True, blend vector + keyword scoring.
            filters:         Optional SearchFilters pydantic model. Converted to a
                             qdrant_client.models.Filter and applied BEFORE semantic
                             search — only chunks whose metadata satisfies the filter
                             are candidates. Supports must / must_not / should clauses
                             with match (exact) and match_any (list) conditions.
        """
        collection_name = collection_name or settings.DEFAULT_COLLECTION
        top_k = top_k or settings.TOP_K

        if not self.qdrant_service.collection_exists(collection_name):
            raise CollectionNotFoundError(f"Collection '{collection_name}' does not exist.")

        store = self.qdrant_service.get_store(collection_name)

        # Build native Qdrant filter from the optional SearchFilters model
        qdrant_filter = build_qdrant_filter(filters)

        if use_hybrid:
            results = hybrid_search(store, query, top_k=top_k, qdrant_filter=qdrant_filter)
        else:
            results = similarity_search(store, query, top_k=top_k, qdrant_filter=qdrant_filter)

        results = rerank(results, top_k=top_k)
        logger.info(
            f"Retrieved {len(results)} chunks for query in '{collection_name}' "
            f"(filter={'active' if qdrant_filter else 'none'})."
        )
        return results

