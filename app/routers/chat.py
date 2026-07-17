"""
Chat router (Controller) — receives chat requests, delegates to ChatService.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.models.chat_request import ChatRequest
from app.services.chat_service import ChatService
from app.dependencies import get_chat_service, get_current_user
from app.database.connection import get_db
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