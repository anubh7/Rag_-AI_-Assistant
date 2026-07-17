"""
Gemini chat model via LangChain's ChatGoogleGenerativeAI.
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings


def get_gemini_llm():
    print("Using model:", settings.GEMINI_CHAT_MODEL)

    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_CHAT_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.3,
    )
