"""
Embedding factory — returns a LangChain Embeddings object based on config.EMBEDDING_PROVIDER.
"""
from app.config import settings
from app.embeddings.gemini_embedding import get_gemini_embeddings
from app.embeddings.huggingface_embedding import get_huggingface_embeddings


def get_embedding_model():
    provider = settings.EMBEDDING_PROVIDER.lower()

    if provider == "gemini":
        return get_gemini_embeddings()
    elif provider == "huggingface":
        return get_huggingface_embeddings()
    else:
        raise ValueError(f"Unsupported embedding provider: {provider}")
