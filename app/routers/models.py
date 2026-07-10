"""
Models router (Controller) — exposes which LLM/embedding providers are configured/available.
"""
from fastapi import APIRouter
from app.config import settings
from app.utils.response import success_response

router = APIRouter()

_AVAILABLE_LLMS = ["gemini", "openai", "claude", "groq", "ollama", "deepseek", "mistral"]
_AVAILABLE_EMBEDDINGS = ["gemini", "huggingface"]


@router.get("/")
def list_models():
    return success_response(
        "Available models fetched.",
        data={
            "current_llm_provider": settings.LLM_PROVIDER,
            "current_embedding_provider": settings.EMBEDDING_PROVIDER,
            "available_llm_providers": _AVAILABLE_LLMS,
            "available_embedding_providers": _AVAILABLE_EMBEDDINGS,
        },
    )
