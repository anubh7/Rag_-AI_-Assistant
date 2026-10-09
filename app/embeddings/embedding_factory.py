"""
Embedding factory — returns a LangChain Embeddings object based on config.EMBEDDING_PROVIDER.
"""
from app.config import settings
from app.embeddings.gemini_embedding import get_gemini_embeddings
from app.embeddings.huggingface_embedding import get_huggingface_embeddings


class FallbackEmbedding:
    """Tiny stand-in embedding model for local/test environments without provider credentials."""

    def embed_query(self, text):
        return [0.0] * int(settings.EMBEDDING_DIM)

    def embed_documents(self, texts):
        return [[0.0] * int(settings.EMBEDDING_DIM) for _ in texts]


def get_embedding_model():
    provider = settings.EMBEDDING_PROVIDER.lower()

    if provider == "gemini":
        if not settings.GEMINI_API_KEY:
            return FallbackEmbedding()
        return get_gemini_embeddings()
    elif provider == "huggingface":
        return get_huggingface_embeddings()
    else:
        raise ValueError(f"Unsupported embedding provider: {provider}")
