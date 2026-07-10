"""
Mistral chat model via LangChain's ChatMistralAI.
"""
from langchain_mistralai import ChatMistralAI
from app.config import settings


def get_mistral_llm():
    return ChatMistralAI(
        model=settings.MISTRAL_CHAT_MODEL,
        api_key=settings.MISTRAL_API_KEY,
        temperature=0.3,
    )
