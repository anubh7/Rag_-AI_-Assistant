"""
ChatService — orchestrates retrieval + prompt building + LLM call, and writes to history.
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


class ChatService:
    def __init__(self, retrieval_service: RetrievalService, llm):
        self.retrieval_service = retrieval_service
        self.llm = llm
        self.history = ChatHistory()

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

        try:
            ai_message = self.llm.invoke(messages)
            raw_content = ai_message.content
            # Gemini may return content as a list of dicts (content parts)
            # instead of a plain string — coerce it to a string for storage.
            if isinstance(raw_content, list):
                answer = "\n".join(
                    part.get("text", str(part)) if isinstance(part, dict) else str(part)
                    for part in raw_content
                )
            else:
                answer = str(raw_content)
        except Exception as e:
            raise LLMGenerationError(str(e))

        # Mask assistant response before saving to history
        answer = mask_pii(answer)

        self.history.add_message(db, session_id, "user", query, user_id)
        self.history.add_message(db, session_id, "assistant", answer, user_id)

        return ChatResponse(answer=answer, session_id=session_id, query=query, sources=sources)

