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
from app.utils.pii_filter import mask_pii


router = APIRouter()


@router.post("/")
def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
):

    try:

        # -------------------------------
        # 1. Receive original user query
        # -------------------------------
        user_query = request.query

        print("USER INPUT:")
        print(user_query)


        # -------------------------------
        # 2. Send original query to LLM
        # -------------------------------
        response = chat_service.chat(
            query=user_query,
            session_id=request.session_id,
            collection_name=request.collection_name,
            top_k=request.top_k,
            use_rag=request.use_rag,
        )


        response_dict = response.dict()


        # -------------------------------
        # 3. Mask AI generated answer
        # -------------------------------
        original_answer = response_dict["answer"]

        print("\nAI ANSWER BEFORE MASKING:")
        print(original_answer)


        masked_answer = mask_pii(original_answer)


        print("\nAI ANSWER AFTER MASKING:")
        print(masked_answer)


        response_dict["answer"] = masked_answer



        # -------------------------------
        # 4. Mask retrieved documents
        # -------------------------------
        for source in response_dict.get("sources", []):

            if source.get("content"):

                source["content"] = mask_pii(
                    source["content"]
                )


        # -------------------------------
        # 5. Return safe response
        # -------------------------------
        return success_response(
            "Chat response generated.",
            data=response_dict
        )


    except AppException as e:

        return JSONResponse(
            status_code=e.status_code,
            content=error_response(e.message).dict()
        )