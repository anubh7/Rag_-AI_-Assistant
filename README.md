# RAG AI Assistant

A modular Retrieval-Augmented Generation platform built with **FastAPI**, **LangChain**,
**Qdrant**, and pluggable LLM/embedding providers (Gemini, OpenAI, Claude, Groq, Ollama,
DeepSeek, Mistral).

## Architecture

Follows a **Controller → Service → Filter** pattern:

- `app/routers/` — Controllers. Thin HTTP layer, no business logic.
- `app/services/` — Services. Orchestrate the actual workflows (upload pipeline, RAG ingestion, retrieval, chat).
- `app/loaders/`, `app/preprocessing/`, `app/chunking/`, `app/retriever/` — Filters. Transform data step by step (load → clean → validate → chunk → retrieve → rerank).
- `app/embeddings/`, `app/llm/` — Provider factories, swap via `.env` (`EMBEDDING_PROVIDER`, `LLM_PROVIDER`).
- `app/vector_db/` — Qdrant integration via `langchain-qdrant`.
- `app/prompts/` — LangChain `ChatPromptTemplate`s for RAG and general chat.
- `app/database/history.py` — chat history (in-memory by default, swappable for a real DB).
- `frontend/` — plain HTML/CSS/JS UI, plus equivalent React components under `frontend/components/`.

## Setup

```bash
python -m venv venv
source venv/bin/activate       # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env           # fill in your API keys
```

Start Qdrant (if not using Qdrant Cloud):

```bash
docker run -p 6333:6333 qdrant/qdrant
```

Run the API:

```bash
python run.py
# or
uvicorn app.main:app --reload
```

Open `frontend/index.html` in a browser (or serve it) to use the chat UI.

## Query Modes & Fallback Support

The platform supports two modes of answering user questions:

- **Document Q&A Mode (RAG)**: Enabled when **Use uploaded documents** is toggled ON. The assistant searches your uploaded documents (stored in Qdrant) and constructs a context-grounded response.
- **General Q&A Mode**: Enabled when **Use uploaded documents** is toggled OFF. The assistant bypasses the vector search and answers questions using general knowledge directly from the LLM (Gemini).

### Automatic Fallback Behavior
To prevent frustrating "I don't have enough information" errors when Document Q&A is ON, the system has an built-in automatic fallback:
- If a query is sent in Document Mode but the document collection is empty, nonexistent, or does not contain content relevant to your question (highest similarity score is below `SCORE_THRESHOLD`), the backend will dynamically fall back to General Q&A mode and query the LLM directly.

## Key Endpoints

| Method | Path                    | Description                          |
|--------|-------------------------|--------------------------------------|
| GET    | `/health/`              | Liveness check                       |
| POST   | `/upload/`               | Upload + index a document            |
| POST   | `/chat/`                 | Ask a question (RAG or general chat) |
| GET    | `/collection/`           | List Qdrant collections              |
| POST   | `/collection/`           | Create a collection                  |
| DELETE | `/collection/{name}`     | Delete a collection                  |
| GET    | `/models/`               | List available LLM/embedding providers |

## Switching providers

Set in `.env`:

```
LLM_PROVIDER=gemini        # gemini | openai | claude | groq | ollama | deepseek | mistral
EMBEDDING_PROVIDER=gemini  # gemini | huggingface
```

## Tests

```bash
pytest tests/
```

Note: `test_upload.py`, `test_chat.py`, and `test_qdrant.py` need a running Qdrant instance
and valid API keys to fully pass end-to-end; they're written to fail gracefully otherwise.
