"""
RAGService — owns the embedding + vector-store write path.
Kept separate from UploadService so other flows (e.g. re-indexing) can reuse it.
"""
from typing import List
from langchain_core.documents import Document

from app.vector_db.qdrant_service import QdrantService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RAGService:
    def __init__(self, qdrant_service: QdrantService, embedding_model):
        self.qdrant_service = qdrant_service
        self.embedding_model = embedding_model

    def ingest_chunks(self, chunks: List[Document], collection_name: str):
        if not self.qdrant_service.collection_exists(collection_name):
            self.qdrant_service.create_collection(collection_name)

        self.qdrant_service.add_documents(
            documents=chunks,
            collection_name=collection_name,
            embedding_model=self.embedding_model,
        )
        logger.info(f"Ingested {len(chunks)} chunks into '{collection_name}'.")
