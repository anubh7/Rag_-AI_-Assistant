"""
Chat router (Controller) — receives chat requests, delegates to ChatService.
POST /chat/       — single JSON response (legacy clients).
POST /chat/stream — server-sent events: retrieval info + tokens as they generate.
"""
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.models.chat_request import ChatRequest
from app.services.chat_service import ChatService
from app.dependencies import get_chat_service, get_current_user
from app.database.connection import get_db, SessionLocal
from app.database.models import User, ChatSession

from app.utils.response import success_response, error_response
from app.utils.exceptions import AppException
from app.utils.pii_filter import mask_pii


router = APIRouter()


@router.post("/")
def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        user_query = request.query

        print("USER INPUT:")
        print(user_query)

        # Ensure session belongs to current user if it already exists
        session_id = request.session_id
        if session_id and session_id != "default":
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session and session.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="Not authorized to access this chat session")

        # Send query to ChatService
        response = chat_service.chat(
            query=user_query,
            db=db,
            user_id=current_user.id,
            session_id=session_id,
            collection_name=request.collection_name,
            top_k=request.top_k,
            use_rag=request.use_rag,
            filters=request.filters,
        )

        response_dict = response.dict()
        original_answer = response_dict["answer"]

        print("\nAI ANSWER BEFORE MASKING:")
        print(original_answer)

        masked_answer = mask_pii(original_answer)

        print("\nAI ANSWER AFTER MASKING:")
        print(masked_answer)

        response_dict["answer"] = masked_answer

        # Mask retrieved documents if any
        for source in response_dict.get("sources", []):
            if source.get("content"):
                source["content"] = mask_pii(source["content"])

        return success_response(
            "Chat response generated.",
            data=response_dict
        )

    except AppException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=error_response(e.message).dict()
        )


@router.post("/stream")
def chat_stream(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Streaming chat over Server-Sent Events.

    Events (one JSON object per `data:` line):
        {"type":"start",...}                — immediately, before retrieval
        {"type":"sources","sources":[...]}  — after retrieval, before generation
        {"type":"token","text":"..."}       — repeatedly, as tokens generate
        {"type":"done","answer":...}        — final PII-masked answer (also saved to history)
        {"type":"error","message":...}      — generation/retrieval failure

    The browser sees the first tokens in ~seconds instead of waiting for the
    whole answer — critical for 3000+ page collections where context is large.
    """
    # Ownership check on an existing session (runs before the stream starts).
    session_id = request.session_id
    if session_id and session_id != "default":
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session and session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this chat session")

    def event_stream():
        # Own session for the generator: the request-scoped `db` dependency is
        # closed by FastAPI once the response starts streaming.
        history_db = SessionLocal()
        try:
            for event in chat_service.chat_stream(
                query=request.query,
                db=history_db,
                user_id=current_user.id,
                session_id=session_id,
                collection_name=request.collection_name,
                top_k=request.top_k,
                use_rag=request.use_rag,
                filters=request.filters,
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"
        finally:
            history_db.close()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable proxy buffering if deployed behind nginx
        },
    )


@router.get("/sessions")
def list_sessions(
    chat_service: ChatService = Depends(get_chat_service),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all chat sessions for the logged in user.
    """
    sessions = chat_service.history.get_user_sessions(db, current_user.id)
    return success_response("User chat sessions retrieved", data=sessions)


@router.get("/sessions/{session_id}")
def load_session(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get messages for a specific chat session if it belongs to the user.
    """
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this session")

    messages = chat_service.history.get_history(db, session_id)
    return success_response("Session messages retrieved", data=messages)


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a chat session and its messages.
    """
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this session")

    chat_service.history.clear_history(db, session_id)
    return success_response("Chat session deleted successfully")