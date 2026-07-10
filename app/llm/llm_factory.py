"""
LLM factory - Gemini only.
"""

from app.llm.gemini import get_gemini_llm


def get_llm(provider: str = None):
    """
    Returns the Gemini LLM instance if provider is "gemini".
    Raises ValueError for unsupported providers.
    """
    provider = provider or "gemini"
    if provider.lower() != "gemini":
        raise ValueError(f"Unsupported LLM provider: '{provider}'. Only 'gemini' is supported.")
    return get_gemini_llm()