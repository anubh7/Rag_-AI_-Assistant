"""
Splitter factory — chooses recursive vs semantic chunking strategy.
"""
from typing import List, Optional
from langchain_core.documents import Document

from app.config import settings
from app.chunking.recursive_splitter import split_recursive
from app.chunking.semantic_splitter import split_semantic


def split_documents(
    documents: List[Document],
    strategy: Optional[str] = None,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    embedding_model=None,
) -> List[Document]:
    strategy = strategy or settings.CHUNKING_STRATEGY
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    if strategy == "semantic" and embedding_model is not None:
        return split_semantic(documents, embedding_model)

    return split_recursive(documents, chunk_size, chunk_overlap)
