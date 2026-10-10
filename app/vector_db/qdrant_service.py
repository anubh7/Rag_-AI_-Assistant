"""
QdrantService — thin service wrapper around Qdrant admin operations and
vector-store access, used by CollectionService / RAGService / RetrievalService.
"""
import threading
import time
from typing import List, Optional
from langchain_core.documents import Document

from app.config import settings
from app.vector_db.qdrant_client import get_qdrant_client
from app.vector_db.vector_factory import (
    get_vector_store,
    get_vector_store_with_embeddings,
    ensure_collection,
    forget_vector_store,
)
from app.embeddings.embedding_factory import get_embedding_model
from app.utils.logger import get_logger

logger = get_logger(__name__)

# How long a cached "collection exists" answer stays valid. Listing collections
# is a separate Qdrant round-trip; on the chat path it ran on every query and
# cost ~1-2s of dead time per request.
COLLECTION_CACHE_TTL = 60


class QdrantService:
    def __init__(self):
        self.client = get_qdrant_client()
        self._collection_cache = {}
        self._cache_lock = threading.Lock()

    def list_collections(self) -> List[str]:
        return [c.name for c in self.client.get_collections().collections]

    def collection_exists(self, name: str) -> bool:
        """
        Cached membership test.

        The list call is only re-issued when the cached entry for `name` is
        missing or older than COLLECTION_CACHE_TTL. Collections are created or
        removed through this same service, which invalidates the cache, so a
        stale answer cannot outlive a real change.
        """
        now = time.monotonic()
        with self._cache_lock:
            if name in self._collection_cache and (now - self._collection_cache[name]) < COLLECTION_CACHE_TTL:
                return True

        exists = name in self.list_collections()

        with self._cache_lock:
            if exists:
                self._collection_cache[name] = now
            else:
                self._collection_cache.pop(name, None)
        return exists

    def _invalidate(self, name: Optional[str] = None) -> None:
        with self._cache_lock:
            if name is None:
                self._collection_cache.clear()
            else:
                self._collection_cache.pop(name, None)

    def create_collection(self, name: str, vector_size: Optional[int] = None):
        ensure_collection(name, vector_size)
        self._invalidate(name)
        logger.info(f"Ensured collection '{name}' exists.")

    def delete_collection(self, name: str):
        self.client.delete_collection(collection_name=name)
        # Drop cached stores so a later re-create isn't served a stale handle.
        forget_vector_store(name)
        self._invalidate(name)
        logger.info(f"Deleted collection '{name}'.")

    def add_documents(
        self,
        documents: List[Document],
        collection_name: str,
        embedding_model=None,
        progress_cb=None,
        batch_size: int = 64,
    ):
        """
        Adds documents in batches so callers can report indexing progress
        (embedding thousands of chunks takes minutes on a local model).
        progress_cb(done_count, total_count) is invoked after each batch.
        """
        embedding_model = embedding_model or get_embedding_model()
        # Uncached path: the caller supplies its own embeddings object, which
        # can't be used as an lru_cache key (see vector_factory.get_vector_store).
        store = get_vector_store_with_embeddings(collection_name, embedding_model)

        total = len(documents)
        done = 0
        for start in range(0, total, batch_size):
            batch = documents[start:start + batch_size]
            store.add_documents(batch)
            done += len(batch)
            if progress_cb:
                progress_cb(done, total)

        logger.info(f"Added {total} chunks to '{collection_name}'.")

    def get_store(self, collection_name: str, embedding_model=None):
        if embedding_model is not None:
            # Caller-supplied embeddings: uncached (can't be an lru_cache key).
            return get_vector_store_with_embeddings(collection_name, embedding_model)
        # Default singleton embeddings: cached per collection.
        return get_vector_store(collection_name)
