"""
Embedding factory — returns a LangChain Embeddings object based on config.EMBEDDING_PROVIDER.
"""
from functools import lru_cache

from app.config import settings
from app.embeddings.gemini_embedding import get_gemini_embeddings
from app.embeddings.huggingface_embedding import get_huggingface_embeddings


class FallbackEmbedding:
    """Tiny stand-in embedding model for local/test environments without provider credentials."""

    def embed_query(self, text):
        return [0.0] * int(settings.EMBEDDING_DIM)

    def embed_documents(self, texts):
        return [[0.0] * int(settings.EMBEDDING_DIM) for _ in texts]


@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Cached: building the model object measured ~1.4-1.9s per call (HTTP client +
    provider setup), and it was being rebuilt on every retrieve/upload request.
    """
    provider = settings.EMBEDDING_PROVIDER.lower()

    if provider == "gemini":
        if not settings.GEMINI_API_KEY:
            return FallbackEmbedding()
        return get_gemini_embeddings()
    elif provider == "huggingface":
        return get_huggingface_embeddings()
    elif provider == "ollama":
        from langchain_ollama import OllamaEmbeddings

        return OllamaEmbeddings(
            model=settings.OLLAMA_EMBEDDING_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            # Keep the embedding model resident between upload batches/uploads.
            keep_alive=settings.OLLAMA_KEEP_ALIVE_VALUE,
        )
    else:
        raise ValueError(f"Unsupported embedding provider: {provider}")
