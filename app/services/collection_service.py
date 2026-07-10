"""
CollectionService — CRUD-ish operations over Qdrant collections.
"""
from typing import List, Optional

from app.vector_db.qdrant_service import QdrantService
from app.utils.exceptions import CollectionNotFoundError


class CollectionService:
    def __init__(self, qdrant_service: QdrantService):
        self.qdrant_service = qdrant_service

    def list_collections(self) -> List[str]:
        return self.qdrant_service.list_collections()

    def create_collection(self, name: str, vector_size: Optional[int] = None) -> dict:
        self.qdrant_service.create_collection(name, vector_size)
        return {"collection": name, "created": True}

    def delete_collection(self, name: str) -> dict:
        if not self.qdrant_service.collection_exists(name):
            raise CollectionNotFoundError(f"Collection '{name}' does not exist.")
        self.qdrant_service.delete_collection(name)
        return {"collection": name, "deleted": True}
