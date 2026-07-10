"""
Tests for the LLM factory — ensures provider routing works without needing live API calls.
Run with: pytest tests/test_llm.py
"""
import pytest
from app.llm.llm_factory import get_llm


def test_unsupported_provider_raises():
    with pytest.raises(ValueError):
        get_llm(provider="not_a_real_provider")


def test_default_provider_resolves_without_error():
    # Will raise only if the API key is missing at instantiation time for some providers;
    # LangChain chat model constructors are generally lazy about auth until .invoke() is called.
    llm = get_llm(provider="gemini")
    assert llm is not None
