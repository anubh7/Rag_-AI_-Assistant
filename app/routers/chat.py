"""
Chat router (Controller) — receives chat requests, delegates to ChatService.
"""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.models.chat_request import ChatRequest
from app.services.chat_service import ChatService
from app.dependencies import get_chat_service
from app.utils.response import success_response, error_response
from app.utils.exceptions import AppException

router = APIRouter()


@router.post("/")
def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        response = chat_service.chat(
            query=request.query,
            session_id=request.session_id,
            collection_name=request.collection_name,
            top_k=request.top_k,
            use_rag=request.use_rag,
        )
        return success_response("Chat response generated.", data=response.dict())
    except AppException as e:
        return JSONResponse(status_code=e.status_code, content=error_response(e.message).dict())
