"""
DeepSeek chat model — OpenAI-compatible API, reused via LangChain's ChatOpenAI
pointed at DeepSeek's base URL.
"""
from langchain_openai import ChatOpenAI
from app.config import settings


def get_deepseek_llm():
    return ChatOpenAI(
        model=settings.DEEPSEEK_CHAT_MODEL,
        api_key=settings.DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com/v1",
        temperature=0.3,
    )
