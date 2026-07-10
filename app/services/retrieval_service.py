"""
RetrievalService — owns the read path: similarity/hybrid search + rerank.
"""
from typing import List, Tuple
from langchain_core.documents import Document

from app.config import settings
from app.vector_db.qdrant_service import QdrantService
from app.retriever.similarity_search import similarity_search
from app.retriever.hybrid_search import hybrid_search
from app.retriever.reranker import rerank
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
    ) -> List[Tuple[Document, float]]:
        collection_name = collection_name or settings.DEFAULT_COLLECTION
        top_k = top_k or settings.TOP_K

        if not self.qdrant_service.collection_exists(collection_name):
            raise CollectionNotFoundError(f"Collection '{collection_name}' does not exist.")

        store = self.qdrant_service.get_store(collection_name)

        if use_hybrid:
            results = hybrid_search(store, query, top_k=top_k)
        else:
            results = similarity_search(store, query, top_k=top_k)

        results = rerank(results, top_k=top_k)
        logger.info(f"Retrieved {len(results)} chunks for query in '{collection_name}'.")
        return results
