"""
ChatService — orchestrates retrieval + prompt building + LLM call, and writes to history.

chat() returns a single JSON response; chat_stream() yields the same
preparation as token-by-token events so large-context RAG answers start
appearing immediately instead of blocking until generation finishes.
"""
from typing import List
from langchain_core.documents import Document

from app.config import settings
from app.services.retrieval_service import RetrievalService
from app.prompts.rag_prompt import build_rag_prompt
from app.prompts.general_prompt import build_general_prompt
from app.models.chat_response import ChatResponse, SourceChunk
from app.database.history import ChatHistory
from app.utils.exceptions import LLMGenerationError, RetrievalError, CollectionNotFoundError
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _format_context(docs_with_scores) -> str:
    parts = []
    for i, (doc, score) in enumerate(docs_with_scores, start=1):
        parts.append(f"[{i}] {doc.page_content}")
    return "\n\n".join(parts)


def _coerce_text(raw_content) -> str:
    """LLM content may be a plain string or a list of content parts (Gemini)."""
    if isinstance(raw_content, list):
        return "\n".join(
            part.get("text", str(part)) if isinstance(part, dict) else str(part)
            for part in raw_content
        )
    return str(raw_content)


class ChatService:
    def __init__(self, retrieval_service: RetrievalService, llm):
        self.retrieval_service = retrieval_service
        self.llm = llm
        self.history = ChatHistory()

    def _prepare(self, query: str, use_rag: bool, collection_name, top_k, filters):
        """
        Shared retrieval + prompt selection for both chat() and chat_stream().

        Falls back to a general (non-RAG) prompt when the collection doesn't
        exist, retrieval errors, or the best score is below SCORE_THRESHOLD.

        Returns: (use_rag, messages, sources)
        """
        sources: List[SourceChunk] = []

        if use_rag:
            try:
                coll_name = collection_name or settings.DEFAULT_COLLECTION
                if not self.retrieval_service.qdrant_service.collection_exists(coll_name):
                    logger.info(f"Collection '{coll_name}' does not exist. Falling back to general LLM.")
                    use_rag = False
                else:
                    results = self.retrieval_service.retrieve(
                        query=query,
                        collection_name=coll_name,
                        top_k=top_k,
                        filters=filters,
                    )
                    if not results or max(score for _, score in results) < settings.SCORE_THRESHOLD:
                        logger.info("No relevant document chunks found matching the query. Falling back to general LLM.")
                        use_rag = False
            except Exception as e:
                logger.warning(f"Error during retrieval, falling back to general LLM: {e}")
                use_rag = False

        if use_rag:
            context = _format_context(results)
            messages = build_rag_prompt(context=context, question=query)

            for doc, score in results:
                sources.append(
                    SourceChunk(
                        content=doc.page_content[:300],
                        source=doc.metadata.get("source"),
                        score=float(score),
                        metadata=doc.metadata,
                    )
                )
        else:
            messages = build_general_prompt(question=query)

        return use_rag, messages, sources

    def chat(
        self,
        query: str,
        db,
        user_id: int,
        session_id: str = "default",
        collection_name: str = None,
        top_k: int = None,
        use_rag: bool = True,
        filters=None,
    ) -> ChatResponse:
        """
        Orchestrate RAG retrieval + LLM response generation.

        Args:
            filters: Optional SearchFilters pydantic model. When provided, Qdrant
                     pre-filters the vector space by metadata BEFORE semantic search.
                     Supports must / must_not / should with match / match_any clauses.
        """
        from app.utils.pii_filter import mask_pii
        query = mask_pii(query)

        use_rag, messages, sources = self._prepare(
            query, use_rag, collection_name, top_k, filters,
        )

        try:
            ai_message = self.llm.invoke(messages)
            answer = _coerce_text(ai_message.content)
        except Exception as e:
            raise LLMGenerationError(str(e))

        # Mask assistant response before saving to history
        answer = mask_pii(answer)

        self.history.add_message(db, session_id, "user", query, user_id)
        self.history.add_message(db, session_id, "assistant", answer, user_id)

        return ChatResponse(answer=answer, session_id=session_id, query=query, sources=sources)

    def chat_stream(
        self,
        query: str,
        db,
        user_id: int,
        session_id: str = "default",
        collection_name: str = None,
        top_k: int = None,
        use_rag: bool = True,
        filters=None,
    ):
        """
        Same pipeline as chat(), but yields plain-dict events for the SSE endpoint:

          {"type": "start",   "session_id": ..., "rag": bool}
          {"type": "sources", "sources": [...]}   (after retrieval, before generation)
          {"type": "token",   "text": "..."}      (zero or more, as generated)
          {"type": "done",    "answer": masked, "session_id": ..., "partial": bool}
          {"type": "error",   "message": "..."}

        History is written once with the final PII-masked answer.
        """
        from app.utils.pii_filter import mask_pii
        query = mask_pii(query)

        use_rag, messages, sources = self._prepare(
            query, use_rag, collection_name, top_k, filters,
        )

        yield {"type": "start", "session_id": session_id, "rag": use_rag}
        yield {"type": "sources", "sources": [s.dict() for s in sources]}

        parts: List[str] = []
        stream_fn = getattr(self.llm, "stream", None)
        try:
            if callable(stream_fn):
                for chunk in stream_fn(messages):
                    text = _coerce_text(getattr(chunk, "content", chunk))
                    if text:
                        parts.append(text)
                        yield {"type": "token", "text": text}
            else:  # providers without streaming support (e.g. FallbackLLM)
                text = _coerce_text(self.llm.invoke(messages).content)
                if text:
                    parts.append(text)
                    yield {"type": "token", "text": text}
        except Exception as e:
            logger.warning(f"Streaming generation failed: {e}")
            if parts:
                answer = mask_pii("".join(parts))
                self.history.add_message(db, session_id, "user", query, user_id)
                self.history.add_message(db, session_id, "assistant", answer, user_id)
                yield {"type": "done", "session_id": session_id, "answer": answer, "partial": True}
            else:
                yield {"type": "error", "message": str(e)}
            return

        answer = mask_pii("".join(parts))
        self.history.add_message(db, session_id, "user", query, user_id)
        self.history.add_message(db, session_id, "assistant", answer, user_id)

        yield {"type": "done", "session_id": session_id, "answer": answer, "partial": False}

