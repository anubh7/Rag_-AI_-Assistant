"""
Shared FastAPI dependencies (DI layer).
Provides singleton-ish access to services so routers stay thin (Controller layer).
"""

from functools import lru_cache

from app.services.upload_service import UploadService
from app.services.rag_service import RAGService
from app.services.chat_service import ChatService
from app.services.retrieval_service import RetrievalService
from app.services.collection_service import CollectionService
from app.vector_db.qdrant_service import QdrantService
from app.embeddings.embedding_factory import get_embedding_model
from app.llm.llm_factory import get_llm


@lru_cache()
def get_qdrant_service() -> QdrantService:
    return QdrantService()


@lru_cache()
def get_collection_service() -> CollectionService:
    return CollectionService(qdrant_service=get_qdrant_service())


@lru_cache()
def get_retrieval_service() -> RetrievalService:
    return RetrievalService(qdrant_service=get_qdrant_service())


@lru_cache()
def get_rag_service() -> RAGService:
    return RAGService(
        qdrant_service=get_qdrant_service(),
        embedding_model=get_embedding_model(),
    )


@lru_cache()
def get_upload_service() -> UploadService:
    return UploadService(rag_service=get_rag_service())


@lru_cache()
def get_chat_service() -> ChatService:
    return ChatService(
        retrieval_service=get_retrieval_service(),
        llm=get_llm(),
    )
