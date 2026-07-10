"""
OpenAI chat model via LangChain's ChatOpenAI.
"""
from langchain_openai import ChatOpenAI
from app.config import settings


def get_openai_llm():
    return ChatOpenAI(
        model=settings.OPENAI_CHAT_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0.3,
    )
