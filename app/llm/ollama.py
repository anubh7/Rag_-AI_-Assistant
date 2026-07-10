"""
Local Ollama chat model via LangChain's ChatOllama.
"""
from langchain_ollama import ChatOllama
from app.config import settings


def get_ollama_llm():
    return ChatOllama(
        model=settings.OLLAMA_CHAT_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0.3,
    )
