"""
Vector store factory — wraps Qdrant with LangChain's QdrantVectorStore for a
consistent add_documents / similarity_search interface used by the rest of the app.
"""
from langchain_qdrant import QdrantVectorStore
from qdrant_client.models import Distance, VectorParams

from app.config import settings
from app.vector_db.qdrant_client import get_qdrant_client
from app.embeddings.embedding_factory import get_embedding_model


def ensure_collection(collection_name: str, vector_size: int = None):
    client = get_qdrant_client()
    vector_size = vector_size or settings.EMBEDDING_DIM

    existing = [c.name for c in client.get_collections().collections]
    if collection_name not in existing:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
    return client


def get_vector_store(collection_name: str = None, embedding_model=None) -> QdrantVectorStore:
    collection_name = collection_name or settings.DEFAULT_COLLECTION
    embedding_model = embedding_model or get_embedding_model()

    ensure_collection(collection_name)
    client = get_qdrant_client()

    return QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embedding_model,
    )
