"""
Upload router (Controller) — receives files, delegates all logic to UploadService.
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from typing import Optional

from app.dependencies import get_upload_service
from app.services.upload_service import UploadService
from app.utils.response import success_response, error_response
from app.utils.exceptions import AppException

router = APIRouter()


@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    collection_name: Optional[str] = Form(default=None),
    chunk_size: Optional[int] = Form(default=None),
    chunk_overlap: Optional[int] = Form(default=None),
    upload_service: UploadService = Depends(get_upload_service),
):
    try:
        result = upload_service.process_upload(
            file=file,
            collection_name=collection_name,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        return success_response("File uploaded and indexed successfully.", data=result)
    except AppException as e:
        return JSONResponse(status_code=e.status_code, content=error_response(e.message).dict())
    except Exception as e:
        return JSONResponse(
            status_code=422,
            content=error_response(f"Failed to process file '{file.filename}': {str(e)}").dict()
        )
