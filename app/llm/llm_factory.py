"""
LLM factory.

Supports multiple providers, but when no API key is configured it falls back to a
lightweight stub implementation instead of throwing during dependency creation.
"""

from app.config import settings
from app.llm.gemini import get_gemini_llm
from app.llm.fallback import FallbackLLM


def get_llm(provider: str = None):
    """Return the configured LLM implementation, or a safe fallback when credentials are empty.

    A configured GEMINI_API_KEY takes priority over LLM_PROVIDER so dropping a key
    into .env is enough to switch back to Gemini without other changes.
    """
    if provider is None and settings.GEMINI_API_KEY:
        provider = "gemini"
    provider = (provider or settings.LLM_PROVIDER or "gemini").lower()

    if provider == "gemini":
        if not settings.GEMINI_API_KEY:
            return FallbackLLM(provider="gemini")
        return get_gemini_llm()

    if provider == "openai":
        from app.llm.openai import get_openai_llm
        if not settings.OPENAI_API_KEY:
            return FallbackLLM(provider="openai")
        return get_openai_llm()

    if provider == "claude":
        from app.llm.claude import get_claude_llm
        if not settings.ANTHROPIC_API_KEY:
            return FallbackLLM(provider="claude")
        return get_claude_llm()

    if provider == "groq":
        from app.llm.groq import get_groq_llm
        if not settings.GROQ_API_KEY:
            return FallbackLLM(provider="groq")
        return get_groq_llm()

    if provider == "deepseek":
        from app.llm.deepseek import get_deepseek_llm
        if not settings.DEEPSEEK_API_KEY:
            return FallbackLLM(provider="deepseek")
        return get_deepseek_llm()

    if provider == "mistral":
        from app.llm.mistral import get_mistral_llm
        if not settings.MISTRAL_API_KEY:
            return FallbackLLM(provider="mistral")
        return get_mistral_llm()

    if provider == "ollama":
        from app.llm.ollama import get_ollama_llm
        return get_ollama_llm()

    raise ValueError(f"Unsupported LLM provider: '{provider}'.")