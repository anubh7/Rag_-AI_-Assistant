"""
Vector store factory — wraps Qdrant with LangChain's QdrantVectorStore for a
consistent add_documents / similarity_search interface used by the rest of the app.
"""
from functools import lru_cache

from langchain_qdrant import QdrantVectorStore
from qdrant_client.models import Distance, VectorParams

from app.config import settings
from app.vector_db.qdrant_client import get_qdrant_client
from app.embeddings.embedding_factory import get_embedding_model

# Collections confirmed to exist in the current process. Without this, every
# get_vector_store() call issued a get_collections() round-trip just to check
# that a collection created minutes earlier was still there.
_ensured = set()


def ensure_collection(collection_name: str, vector_size: int = None):
    client = get_qdrant_client()

    if collection_name in _ensured:
        return client

    vector_size = vector_size or settings.EMBEDDING_DIM
    existing = [c.name for c in client.get_collections().collections]
    if collection_name not in existing:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
    _ensured.add(collection_name)
    return client


def _build_vector_store(collection_name: str, embedding_model=None) -> QdrantVectorStore:
    collection_name = collection_name or settings.DEFAULT_COLLECTION
    embedding_model = embedding_model or get_embedding_model()

    ensure_collection(collection_name)
    client = get_qdrant_client()

    return QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embedding_model,
    )


@lru_cache(maxsize=8)
def get_vector_store(collection_name: str = None) -> QdrantVectorStore:
    """
    Cached per collection: the QdrantVectorStore wrapper is stateless (it just
    holds a client + collection name + embeddings), so rebuilding it per request
    only re-triggered collection checks and client construction.

    NOTE: the embedding model is deliberately NOT a cache key. lru_cache hashes
    its arguments, and LangChain embeddings (OllamaEmbeddings and friends) are
    pydantic models that are unhashable — passing one raised
    "TypeError: unhashable type: 'OllamaEmbeddings'", which the chat pipeline
    swallowed as a retrieval failure and silently downgraded every answer to
    non-RAG. The embedding model is already a process-wide singleton
    (get_embedding_model is itself lru_cached), so it is resolved inside.
    """
    return _build_vector_store(collection_name)


def get_vector_store_with_embeddings(collection_name: str, embedding_model):
    """Uncached variant for callers that supply their own embeddings object."""
    return _build_vector_store(collection_name, embedding_model)


def forget_vector_store(collection_name: str):
    """
    Invalidate cached stores for a collection (call after deleting it, so a
    later re-create doesn't reuse a handle bound to the old collection).
    """
    _ensured.discard(collection_name)
    # Stores are keyed by collection_name; dropping the whole cache is cheap
    # (maxsize=8) and avoids depending on lru_cache internals.
    get_vector_store.cache_clear()
