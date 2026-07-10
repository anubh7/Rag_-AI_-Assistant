"""
UploadService — orchestrates: save file -> load -> clean -> validate -> chunk -> embed & store.
Called by routers/upload.py (Controller layer).
"""
from fastapi import UploadFile

from app.config import settings
from app.utils.file_helper import validate_file, save_upload_file, loader_key_for
from app.loaders.loader_factory import get_documents
from app.preprocessing.clean_text import clean_documents
from app.preprocessing.validator import validate_documents
from app.preprocessing.metadata import enrich_metadata
from app.chunking.splitter_factory import split_documents
from app.services.rag_service import RAGService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class UploadService:
    def __init__(self, rag_service: RAGService):
        self.rag_service = rag_service

    def process_upload(
        self,
        file: UploadFile,
        collection_name: str = None,
        chunk_size: int = None,
        chunk_overlap: int = None,
    ) -> dict:
        collection_name = collection_name or settings.DEFAULT_COLLECTION

        ext = validate_file(file)
        loader_key = loader_key_for(ext)
        saved_path = save_upload_file(file, sub_dir=loader_key)

        logger.info(f"Loading '{saved_path}' with loader '{loader_key}'.")
        documents = get_documents(saved_path, loader_key)
        documents = clean_documents(documents)
        documents = validate_documents(documents)
        documents = enrich_metadata(documents, collection_name)

        chunks = split_documents(
            documents,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        self.rag_service.ingest_chunks(chunks, collection_name)

        return {
            "file": file.filename,
            "collection": collection_name,
            "pages_loaded": len(documents),
            "chunks_created": len(chunks),
        }
