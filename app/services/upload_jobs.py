"""
In-process upload job registry.

Large files (e.g. a 3,600-page PDF) take minutes to load and index. Running
that pipeline inside the request handler blocks the asyncio event loop and
freezes the entire API. Instead, the upload router creates an UploadJob here,
runs the pipeline in a daemon thread, and clients poll GET /upload/jobs/{id}
for live stage/progress updates.
"""
import threading
import time
import uuid
from typing import Dict, List, Optional, Any

JOB_QUEUED = "queued"
JOB_RUNNING = "running"
JOB_COMPLETED = "completed"
JOB_FAILED = "failed"
JOB_CANCELLED = "cancelled"


class JobCancelled(Exception):
    """Raised inside a job worker to unwind once a cancel is requested."""

# Keep only the most recent finished jobs in memory.
MAX_FINISHED_JOBS = 50


class UploadJob:
    """Mutable job state shared between the worker thread and the API."""

    def __init__(self, job_id: str, user_id: Any, collection_name: str):
        self.job_id = job_id
        self.user_id = user_id
        self.collection_name = collection_name

        self.status = JOB_QUEUED
        self.stage = "queued"          # queued | loading | cleaning | chunking | indexing | finalizing | done
        self.message = "Waiting to start."

        self.created_at = time.time()
        self.updated_at = time.time()

        # Progress counters
        self.total_files = 0
        self.files_done = 0
        self.current_file: Optional[str] = None
        self.pages_loaded = 0
        self.chunks_created = 0
        self.chunks_indexed = 0
        self.chunks_total = 0           # 0 until chunking for the current file finished

        self.result: Optional[dict] = None   # final summary (same shape as the old sync response)
        self.error: Optional[str] = None

        # Cancellation: set by POST /upload/jobs/{id}/cancel. The worker polls
        # it between pages and between embedding batches, so a cancel lands
        # within one batch instead of running the whole file to completion.
        self.cancel_requested = False
        self.cancelled_at: Optional[float] = None


    def update(self, stage: Optional[str] = None, message: Optional[str] = None, **counters: Any) -> None:
        if stage is not None:
            self.stage = stage
        if message is not None:
            self.message = message
        for key, value in counters.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = time.time()

    def snapshot(self) -> dict:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "stage": self.stage,
            "message": self.message,
            "collection": self.collection_name,
            "total_files": self.total_files,
            "files_done": self.files_done,
            "current_file": self.current_file,
            "pages_loaded": self.pages_loaded,
            "chunks_created": self.chunks_created,
            "chunks_indexed": self.chunks_indexed,
            "chunks_total": self.chunks_total,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "cancel_requested": self.cancel_requested,
            "cancelled": self.status == JOB_CANCELLED,
        }

    def request_cancel(self) -> bool:
        """
        Flags the job for cancellation. Returns False when the job has already
        finished, so the caller can report that there is nothing left to stop.
        """
        if self.status in (JOB_COMPLETED, JOB_FAILED, JOB_CANCELLED):
            return False
        self.cancel_requested = True
        self.cancelled_at = time.time()
        self.updated_at = self.cancelled_at
        return True

    def check_cancelled(self) -> None:
        """Raises JobCancelled if a cancel was requested. Call inside loops."""
        if self.cancel_requested:
            raise JobCancelled("Upload cancelled by user.")

    @property
    def is_active(self) -> bool:
        return self.status in (JOB_QUEUED, JOB_RUNNING)


_jobs: Dict[str, UploadJob] = {}
_lock = threading.Lock()


def _prune_finished_locked() -> None:
    finished = [
        job for job in _jobs.values()
        if job.status in (JOB_COMPLETED, JOB_FAILED, JOB_CANCELLED)
    ]
    finished.sort(key=lambda job: job.created_at)
    while len(finished) >= MAX_FINISHED_JOBS:
        old = finished.pop(0)
        _jobs.pop(old.job_id, None)


def create_job(user_id: Any, collection_name: str, total_files: int) -> UploadJob:
    with _lock:
        _prune_finished_locked()
        job = UploadJob(str(uuid.uuid4()), user_id, collection_name)
        job.total_files = total_files
        _jobs[job.job_id] = job
        return job


def get_job(job_id: str, user_id: Any = None) -> Optional[UploadJob]:
    """Returns the job, or None if it does not exist / belongs to another user."""
    with _lock:
        job = _jobs.get(job_id)
    if job is None:
        return None
    if user_id is not None and job.user_id != user_id:
        return None
    return job


def request_cancel(job_id: str, user_id: Any = None) -> Optional[bool]:
    """
    Ask a job to stop. Returns:
      True  — the cancel flag was set, the worker will unwind shortly.
      False — the job already finished, there was nothing to cancel.
      None  — no such job (or it belongs to another user).
    """
    job = get_job(job_id, user_id)
    if job is None:
        return None
    return job.request_cancel()
