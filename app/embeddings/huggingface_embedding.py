"""
Local/free embeddings via LangChain's HuggingFaceEmbeddings wrapper.
Useful as a fallback when no Gemini/OpenAI key is configured.
"""
from langchain_community.embeddings import HuggingFaceEmbeddings
from app.config import settings


def get_huggingface_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=settings.HF_EMBEDDING_MODEL)
