"""
Groq-hosted chat model via LangChain's ChatGroq.
"""
from langchain_groq import ChatGroq
from app.config import settings


def get_groq_llm():
    return ChatGroq(
        model=settings.GROQ_CHAT_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=0.3,
    )
