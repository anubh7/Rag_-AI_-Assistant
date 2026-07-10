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
        session_id: str = "default",
        collection_name: str = None,
        top_k: int = None,
        use_rag: bool = True,
    ) -> ChatResponse:
        sources: List[SourceChunk] = []

        if use_rag:
            try:
                coll_name = collection_name or settings.DEFAULT_COLLECTION
                if not self.retrieval_service.qdrant_service.collection_exists(coll_name):
                    logger.info(f"Collection '{coll_name}' does not exist. Falling back to general LLM.")
                    use_rag = False
                else:
                    results = self.retrieval_service.retrieve(
                        query=query, collection_name=coll_name, top_k=top_k
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
            answer = ai_message.content
        except Exception as e:
            raise LLMGenerationError(str(e))

        self.history.add_message(session_id, "user", query)
        self.history.add_message(session_id, "assistant", answer)

        return ChatResponse(answer=answer, session_id=session_id, sources=sources)
