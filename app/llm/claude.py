"""
Anthropic Claude chat model via LangChain's ChatAnthropic.
"""
from langchain_anthropic import ChatAnthropic
from app.config import settings


def get_claude_llm():
    return ChatAnthropic(
        model=settings.CLAUDE_CHAT_MODEL,
        api_key=settings.ANTHROPIC_API_KEY,
        temperature=0.3,
    )
