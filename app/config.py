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

    # Local embeddings via Ollama (no API key required)
    OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

    EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", 3072))

    # ---------------- Gemini LLM ----------------
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_CHAT_MODEL = os.getenv(
        "GEMINI_CHAT_MODEL",
         "gemini-flash-latest"
    )

    # ---------------- Ollama (local, no API key) ----------------
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.1:8b")
    # "-1" keeps loaded models resident in RAM so re-uploads / new chats never
    # pay the 30-60s cold-start model load again (set to e.g. "10m" to free RAM).
    OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "-1")

    @property
    def OLLAMA_KEEP_ALIVE_VALUE(self):
        """
        Ollama's API accepts either an integer number of seconds or a Go
        duration string with a unit ("10m", "1h"). Env vars always arrive as
        strings, so a bare "-1" is rejected with
        'time: missing unit in duration "-1"' (HTTP 400) — which surfaces to
        the user as a chat error. Coerce numeric-looking values to int here and
        pass unit strings through untouched.
        """
        raw = str(self.OLLAMA_KEEP_ALIVE).strip()
        try:
            return int(raw)
        except ValueError:
            return raw

    # ---------------- LLM generation ----------------
    # Cap answer length (num_predict) so generations finish in bounded time.
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", 600))
    # Context window: retrieval context (top_k * ~chunk_size chars) + answer room.
    LLM_NUM_CTX = int(os.getenv("LLM_NUM_CTX", 8192))

    # ---------------- Chunking ----------------
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 150))
    CHUNKING_STRATEGY = os.getenv("CHUNKING_STRATEGY", "recursive")

    # ---------------- Retrieval ----------------
    TOP_K = int(os.getenv("TOP_K", 5))
    SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD", 0.5))

    # ---------------- Uploads ----------------
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "app/uploads")
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 50))
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