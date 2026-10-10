"""
Raw Qdrant client instance (used for admin ops like create/delete/list collections).
"""
import os

from qdrant_client import QdrantClient
from app.config import settings

# Singletons: the client must be resolved once and reused for the process lifetime.
#
# QdrantClient(path=...) takes an exclusive on-disk lock, so multiple local
# instances on the same path raise "already accessed by another instance".
# Separately, probing a Qdrant *server* that isn't running burns ~4.4s in
# connection retries before falling back — and that probe used to re-run on
# every single call, twice per chat request (ensure_collection + get_vector_store),
# which alone accounted for ~10s of latency before the first token streamed.
_client: QdrantClient = None
_local_client: QdrantClient = None


def reset_qdrant_client():
    """Drop cached clients (used by tests that switch QDRANT_URL)."""
    global _client, _local_client
    _client = None
    _local_client = None


def get_qdrant_client() -> QdrantClient:
    global _client, _local_client

    if _client is not None:
        return _client

    if settings.QDRANT_URL:
        _client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY or None,
            # Skip the version handshake round-trip on every request.
            check_compatibility=False,
        )
        return _client

    # Try a local Qdrant server first; connections are lazy, so probe with a
    # real call. This probe happens at most once per process now.
    try:
        candidate = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        candidate.get_collections()
        _client = candidate
        return _client
    except Exception:
        # Fall back to persistent local Qdrant for development.
        if _local_client is None:
            local_path = os.path.join(os.getcwd(), "app", "vector_db", "local_qdrant")
            os.makedirs(local_path, exist_ok=True)
            _local_client = QdrantClient(path=local_path)
        _client = _local_client
        return _client
