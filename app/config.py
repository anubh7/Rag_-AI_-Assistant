"""
Central configuration for the RAG AI Assistant.
Loads environment variables and exposes typed settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # ---------------- App ----------------
    APP_NAME = "RAG AI Assistant"
    APP_VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"

    # ---------------- Server ----------------
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))

    # ---------------- Qdrant ----------------
    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
    QDRANT_URL = os.getenv("QDRANT_URL", "")
    DEFAULT_COLLECTION = os.getenv("DEFAULT_COLLECTION", "rag_documents")

    # ---------------- Embeddings ----------------
    EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "gemini")

    # Updated default embedding model
    GEMINI_EMBEDDING_MODEL = os.getenv(
        "GEMINI_EMBEDDING_MODEL",
        "models/gemini-embedding-001"
    )

    HF_EMBEDDING_MODEL = os.getenv(
        "HF_EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", 3072))

    # ---------------- Gemini LLM ----------------
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_CHAT_MODEL = os.getenv(
        "GEMINI_CHAT_MODEL",
        "gemini-2.5-flash"
    )

    # ---------------- Chunking ----------------
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 150))
    CHUNKING_STRATEGY = os.getenv("CHUNKING_STRATEGY", "recursive")

    # ---------------- Retrieval ----------------
    TOP_K = int(os.getenv("TOP_K", 5))
    SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD", 0.5))

    # ---------------- Uploads ----------------
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "app/uploads")
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 25))
    ALLOWED_EXTENSIONS = {
        ".pdf",
        ".csv",
        ".xlsx",
        ".xls",
        ".docx",
        ".txt",
    }


settings = Settings()