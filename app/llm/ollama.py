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
        # Keep the model resident so the first token doesn't wait for a
        # 30-60s model reload after any idle period.
        keep_alive=settings.OLLAMA_KEEP_ALIVE_VALUE,
        # Room for system prompt + retrieved chunks + the answer.
        num_ctx=settings.LLM_NUM_CTX,
        # Cap answer length so generation finishes in bounded time.
        num_predict=settings.LLM_MAX_TOKENS,
    )
