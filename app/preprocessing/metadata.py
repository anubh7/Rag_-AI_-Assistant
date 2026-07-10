"""
Metadata enrichment for Documents prior to embedding/storage.
"""
from langchain_core.documents import Document
from typing import List
from app.utils.helper import new_id, utc_now_iso


def enrich_metadata(documents: List[Document], collection_name: str) -> List[Document]:
    for doc in documents:
        doc.metadata.setdefault("chunk_id", new_id())
        doc.metadata.setdefault("collection", collection_name)
        doc.metadata.setdefault("ingested_at", utc_now_iso())
    return documents
