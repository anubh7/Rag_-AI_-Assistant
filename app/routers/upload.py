"""
Upload router (Controller) — receives files, delegates all logic to UploadService.
Supports single or multiple file uploads in one request.
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional

from app.dependencies import get_upload_service, get_current_user
from app.database.models import User
from app.services.upload_service import UploadService
from app.utils.response import success_response, error_response
from app.utils.exceptions import AppException

router = APIRouter()


@router.post("/")
async def upload_files(
    files: List[UploadFile] = File(...),
    collection_name: Optional[str] = Form(default=None),
    chunk_size: Optional[int] = Form(default=None),
    chunk_overlap: Optional[int] = Form(default=None),
    upload_service: UploadService = Depends(get_upload_service),
    current_user: User = Depends(get_current_user),
):
    """
    Upload one or more files and index them into the Qdrant collection.
    Each file is processed independently: validate → load → clean → chunk → embed → store.
    Returns a summary per file plus overall totals.
    """
    results = []
    errors = []

    for file in files:
        try:
            result = upload_service.process_upload(
                file=file,
                collection_name=collection_name,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            results.append(result)
        except AppException as e:
            errors.append({"file": file.filename, "error": e.message})
        except Exception as e:
            errors.append({"file": file.filename, "error": f"Failed to process: {str(e)}"})

    total_chunks = sum(r.get("chunks_created", 0) for r in results)
    total_pages  = sum(r.get("pages_loaded",  0) for r in results)

    response_data = {
        "uploaded": results,
        "errors": errors,
        "total_files_processed": len(results),
        "total_files_failed": len(errors),
        "total_pages_loaded": total_pages,
        "total_chunks_created": total_chunks,
    }

    if results:
        return success_response(
            f"{len(results)} file(s) uploaded and indexed successfully"
            + (f"; {len(errors)} failed" if errors else "") + ".",
            data=response_data,
        )
    else:
        return JSONResponse(
            status_code=422,
            content=error_response("All file uploads failed.").dict()
        )

