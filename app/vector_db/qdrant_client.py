"""
Raw Qdrant client instance (used for admin ops like create/delete/list collections).
"""
from qdrant_client import QdrantClient
from app.config import settings


def get_qdrant_client() -> QdrantClient:
    if settings.QDRANT_URL:
        return QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY or None)
    return QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
