"""
Upload router (Controller) — two-phase uploads:
  1) POST /upload/            — validate + save files fast, spawn a background job.
  2) GET  /upload/jobs/{id}   — poll job stage/progress while the heavy
                                load/clean/chunk/embed pipeline runs in a thread.
This keeps the API responsive while large documents (thousands of pages)
are being indexed instead of freezing the whole server inside the request.
"""
import threading
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.dependencies import get_upload_service, get_current_user
from app.database.models import User
from app.services.upload_service import UploadService
from app.services import upload_jobs
from app.utils.response import success_response, error_response
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


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
    Phase 1: validate + save every file, then hand the expensive
    load/clean/chunk/embed pipeline to a background job thread.
    Returns immediately with a job_id the client polls for progress.
    If every file fails quick validation, returns 422 with per-file reasons.
    """
    accepted, pre_errors = upload_service.prepare_uploads(files, collection_name)

    if not accepted:
        first_error = pre_errors[0]["error"] if pre_errors else "Unknown error."
        response_data = {
            "uploaded": [],
            "errors": pre_errors,
            "total_files_processed": 0,
            "total_files_failed": len(pre_errors),
            "total_pages_loaded": 0,
            "total_chunks_created": 0,
        }
        return JSONResponse(
            status_code=422,
            content=error_response(
                f"All file uploads failed. First error: {first_error}",
                data=response_data,
            ).dict(),
        )

    job = upload_jobs.create_job(
        user_id=current_user.id,
        collection_name=collection_name,
        total_files=len(accepted),
    )

    worker = threading.Thread(
        target=upload_service.process_job,
        kwargs={
            "job": job,
            "accepted": accepted,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "pre_errors": pre_errors,
        },
        daemon=True,
        name=f"upload-job-{job.job_id[:8]}",
    )
    worker.start()

    return success_response(
        f"{len(accepted)} file(s) accepted; processing in the background"
        + (f"; {len(pre_errors)} rejected during validation" if pre_errors else "")
        + ".",
        data={
            "job_id": job.job_id,
            "status_url": f"/upload/jobs/{job.job_id}",
            "accepted": [{"file": a["file"]} for a in accepted],
            "errors": pre_errors,
            "total_files_accepted": len(accepted),
            "total_files_failed": len(pre_errors),
        },
    )


@router.get("/jobs/{job_id}")
async def get_upload_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    """Pollable status/progress for a background upload job (owner only)."""
    job = upload_jobs.get_job(job_id, user_id=current_user.id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload job not found.",
        )

    snapshot = job.snapshot()
    if snapshot["status"] == upload_jobs.JOB_FAILED:
        # Same shape either way: clients read data.status + data.result/errors.
        return error_response(snapshot["error"] or "Upload job failed.", data=snapshot)
    return success_response(snapshot["message"], data=snapshot)


@router.post("/jobs/{job_id}/cancel")
async def cancel_upload_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Ask a running upload job to stop.

    Cancellation is cooperative: the worker checks the flag between parsed
    pages and between embedding batches, so it stops within one batch rather
    than freezing the API. Chunks already indexed stay in the collection and
    remain searchable — only the remaining work is abandoned.
    """
    outcome = upload_jobs.request_cancel(job_id, user_id=current_user.id)

    if outcome is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload job not found.",
        )

    if not outcome:
        job = upload_jobs.get_job(job_id, user_id=current_user.id)
        return success_response(
            "Job already finished; nothing to cancel.",
            data=job.snapshot() if job else None,
        )

    logger.info(
        f"Cancel requested for upload job {job_id} by user {current_user.id}."
    )
    return success_response(
        "Cancellation requested. Stopping after the current batch…",
        data={"job_id": job_id, "status": upload_jobs.JOB_CANCELLED},
    )

