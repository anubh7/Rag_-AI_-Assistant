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
         "gemini-flash-latest"
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

    # ---------------- Database ----------------
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB = os.getenv("MYSQL_DB", "rag_assistant_db")

    @property
    def DATABASE_URL(self) -> str:
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            return database_url

        # Default to SQLite for local/dev runs when no real MySQL credentials are configured.
        # This avoids startup crashes in environments where MySQL is not installed or the
        # default root account is unavailable.
        mysql_user = (self.MYSQL_USER or "").strip()
        mysql_password = (self.MYSQL_PASSWORD or "").strip()
        if mysql_user == "root" and mysql_password == "" and self.MYSQL_HOST in {"localhost", "127.0.0.1"}:
            sqlite_path = os.path.join(os.getcwd(), "app.db")
            return f"sqlite:///{sqlite_path}"

        import urllib.parse
        encoded_user = urllib.parse.quote_plus(self.MYSQL_USER)
        encoded_password = urllib.parse.quote_plus(self.MYSQL_PASSWORD)
        return f"mysql+pymysql://{encoded_user}:{encoded_password}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset=utf8mb4"

    # ---------------- Security ----------------
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "yoursupersecretkeyhere")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))


settings = Settings()