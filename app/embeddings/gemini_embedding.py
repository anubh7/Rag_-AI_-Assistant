"""
Gemini embeddings via LangChain's GoogleGenerativeAIEmbeddings wrapper.
"""
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.config import settings


def get_gemini_embeddings() -> GoogleGenerativeAIEmbeddings:
    return GoogleGenerativeAIEmbeddings(
        model=settings.GEMINI_EMBEDDING_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
    )
