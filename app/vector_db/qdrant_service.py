"""
QdrantService — thin service wrapper around Qdrant admin operations and
vector-store access, used by CollectionService / RAGService / RetrievalService.
"""
from typing import List, Optional
from langchain_core.documents import Document

from app.config import settings
from app.vector_db.qdrant_client import get_qdrant_client
from app.vector_db.vector_factory import get_vector_store, ensure_collection
from app.embeddings.embedding_factory import get_embedding_model
from app.utils.logger import get_logger

logger = get_logger(__name__)


class QdrantService:
    def __init__(self):
        self.client = get_qdrant_client()

    def list_collections(self) -> List[str]:
        return [c.name for c in self.client.get_collections().collections]

    def collection_exists(self, name: str) -> bool:
        return name in self.list_collections()

    def create_collection(self, name: str, vector_size: Optional[int] = None):
        ensure_collection(name, vector_size)
        logger.info(f"Ensured collection '{name}' exists.")

    def delete_collection(self, name: str):
        self.client.delete_collection(collection_name=name)
        logger.info(f"Deleted collection '{name}'.")

    def add_documents(self, documents: List[Document], collection_name: str, embedding_model=None):
        embedding_model = embedding_model or get_embedding_model()
        store = get_vector_store(collection_name, embedding_model)
        store.add_documents(documents)
        logger.info(f"Added {len(documents)} chunks to '{collection_name}'.")

    def get_store(self, collection_name: str, embedding_model=None):
        embedding_model = embedding_model or get_embedding_model()
        return get_vector_store(collection_name, embedding_model)
