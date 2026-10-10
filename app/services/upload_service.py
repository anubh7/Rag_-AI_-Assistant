"""
UploadService — orchestrates: save file -> load -> clean -> validate -> chunk -> embed & store.

Split into two phases so large files never block the API event loop:
  - prepare_uploads(): fast validation + disk save (runs inside the request).
  - process_job():     the heavy pipeline (runs in a background thread owned
                       by the upload job created in routers/upload.py).
process_upload() is kept as a synchronous single-file convenience wrapper.
"""
import time
from typing import List, Tuple

from fastapi import UploadFile

from app.config import settings
from app.utils.file_helper import validate_file, save_upload_file, loader_key_for
from app.loaders.loader_factory import get_documents
from app.preprocessing.clean_text import clean_documents
from app.preprocessing.validator import validate_documents
from app.preprocessing.metadata import enrich_metadata
from app.chunking.splitter_factory import split_documents
from app.services.rag_service import RAGService
from app.services.upload_jobs import (
    UploadJob,
    JobCancelled,
    JOB_RUNNING,
    JOB_COMPLETED,
    JOB_FAILED,
    JOB_CANCELLED,
)
from app.utils.exceptions import AppException
from app.utils.logger import get_logger

logger = get_logger(__name__)


class UploadService:
    def __init__(self, rag_service: RAGService):
        self.rag_service = rag_service

    # ------------------------------------------------------------------
    # Phase 1 — fast: validate type/size and persist the raw file.
    # ------------------------------------------------------------------
    def prepare_uploads(
        self,
        files: List[UploadFile],
        collection_name: str = None,
    ) -> Tuple[List[dict], List[dict]]:
        """
        Validates and saves every file, without touching the expensive
        load/clean/chunk/embed pipeline.

        Returns (accepted, errors): accepted items are
        {"file": name, "path": saved_path, "loader_key": key};
        error items are {"file": name, "error": reason}.
        """
        accepted: List[dict] = []
        errors: List[dict] = []

        for file in files:
            try:
                ext = validate_file(file)
                loader_key = loader_key_for(ext)
                saved_path = save_upload_file(file, sub_dir=loader_key)
                accepted.append({
                    "file": file.filename,
                    "path": saved_path,
                    "loader_key": loader_key,
                })
            except AppException as e:
                errors.append({"file": file.filename, "error": e.message})
            except Exception as e:
                errors.append({"file": file.filename, "error": f"Failed to save: {e}"})

        return accepted, errors

    # ------------------------------------------------------------------
    # Phase 2 — slow: the actual RAG pipeline, run inside a job thread.
    # ------------------------------------------------------------------
    def process_job(
        self,
        job: UploadJob,
        accepted: List[dict],
        chunk_size: int = None,
        chunk_overlap: int = None,
        pre_errors: List[dict] = None,
    ) -> None:
        """
        Runs load -> clean -> validate -> chunk -> embed for every accepted
        file, updating `job` with stage/progress along the way.
        Never raises: failures are recorded on the job so pollers see them.
        """
        collection_name = job.collection_name or settings.DEFAULT_COLLECTION
        results: List[dict] = []
        errors: List[dict] = list(pre_errors or [])
        chunks_indexed_base = 0

        try:
            job.status = JOB_RUNNING
            total = len(accepted)

            for index, item in enumerate(accepted):
                # Cancellation is cooperative: a big PDF is chunked and embedded
                # in batches, so bail out between files instead of running the
                # whole queue to completion.
                job.check_cancelled()

                fname = item["file"]
                job.update(
                    stage="loading",
                    current_file=fname,
                    files_done=index,
                    message=f"Reading {fname}… ({index + 1} of {total} file(s))",
                )

                try:
                    logger.info(f"Loading '{item['path']}' with loader '{item['loader_key']}'.")

                    # Page-level progress: a 3,600-page PDF takes minutes to
                    # parse — update the job live so the UI never looks stuck.
                    pages_base = job.pages_loaded
                    last_page_push = [0.0]

                    def _page_cb(done_in_file: int, total_in_file: int,
                                 _base=pages_base, _fname=fname, _ts=last_page_push):
                        now = time.time()
                        if done_in_file < total_in_file and now - _ts[0] < 0.4:
                            return  # throttle job updates to ~2.5/sec
                        _ts[0] = now
                        job.update(
                            stage="loading",
                            pages_loaded=_base + done_in_file,
                            message=(
                                f"Reading {_fname}: {done_in_file:,}/{total_in_file:,} pages…"
                            ),
                        )
                        # Stop parsing the rest of the file on cancel.
                        job.check_cancelled()

                    documents = get_documents(
                        item["path"], item["loader_key"], progress_cb=_page_cb,
                    )

                    job.update(
                        stage="cleaning",
                        pages_loaded=pages_base + len(documents),
                        message=f"Cleaning {fname}: {len(documents)} section(s) loaded.",
                    )
                    documents = clean_documents(documents)
                    documents = validate_documents(documents)
                    documents = enrich_metadata(documents, collection_name)

                    job.update(stage="chunking", message=f"Splitting {fname} into chunks…")
                    chunks = split_documents(
                        documents,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap,
                    )

                    base = chunks_indexed_base

                    def _progress(done_in_file: int, total_in_file: int, _base=base, _fname=fname):
                        job.update(
                            stage="indexing",
                            chunks_indexed=_base + done_in_file,
                            chunks_total=_base + total_in_file,
                            message=(
                                f"Indexing {_fname}: chunk {_base + done_in_file}"
                                f"/{_base + total_in_file} embedded."
                            ),
                        )
                        # Stop sending further embedding batches on cancel.
                        job.check_cancelled()

                    job.update(
                        chunks_created=job.chunks_created + len(chunks),
                        message=f"Embedding {len(chunks)} chunk(s) from {fname}…",
                    )
                    self.rag_service.ingest_chunks(
                        chunks, collection_name, progress_cb=_progress,
                    )

                    chunks_indexed_base += len(chunks)
                    results.append({
                        "file": fname,
                        "collection": collection_name,
                        "pages_loaded": len(documents),
                        "chunks_created": len(chunks),
                    })

                except JobCancelled:
                    # Unwind out of the per-file loop entirely — the outer
                    # handler turns this into a cancelled job.
                    raise
                except AppException as e:
                    errors.append({"file": fname, "error": e.message})
                except Exception as e:
                    errors.append({"file": fname, "error": f"Failed to process: {e}"})

            job.files_done = total
            job.chunks_indexed = chunks_indexed_base
            job.chunks_total = max(job.chunks_total, chunks_indexed_base)

            response_data = {
                "uploaded": results,
                "errors": errors,
                "total_files_processed": len(results),
                "total_files_failed": len(errors),
                "total_pages_loaded": sum(r["pages_loaded"] for r in results),
                "total_chunks_created": sum(r["chunks_created"] for r in results),
            }
            job.result = response_data

            if results:
                job.status = JOB_COMPLETED
                job.update(
                    stage="done",
                    current_file=None,
                    message=(
                        f"Done: {len(results)} file(s) indexed, "
                        f"{response_data['total_chunks_created']} chunks."
                    ),
                )
                if errors:
                    job.message += f" {len(errors)} file(s) had issues (see errors)."
            else:
                first_error = errors[0]["error"] if errors else "Unknown error."
                job.status = JOB_FAILED
                job.error = f"All file uploads failed. First error: {first_error}"
                job.update(stage="done", current_file=None, message=job.error)
                logger.error(f"Upload job {job.job_id} failed: {job.error}")

        except JobCancelled:
            # Anything embedded before the cancel stays in the collection; the
            # job is simply reported as cancelled, not failed.
            job.status = JOB_CANCELLED
            job.update(
                stage="done",
                current_file=None,
                message=(
                    f"Upload cancelled. {chunks_indexed_base} chunk(s) were "
                    f"already indexed and remain searchable."
                ),
            )
            logger.info(
                f"Upload job {job.job_id} cancelled after "
                f"{chunks_indexed_base} indexed chunk(s)."
            )
        except Exception as e:  # noqa: BLE001 — job thread must never crash silently
            job.status = JOB_FAILED
            job.error = f"Upload job crashed: {e}"
            job.update(stage="done", current_file=None, message=job.error)
            logger.exception(f"Upload job {job.job_id} crashed.")

    # ------------------------------------------------------------------
    # Backward-compatible synchronous single-file path (used by tests).
    # ------------------------------------------------------------------
    def process_upload(
        self,
        file: UploadFile,
        collection_name: str = None,
        chunk_size: int = None,
        chunk_overlap: int = None,
    ) -> dict:
        collection_name = collection_name or settings.DEFAULT_COLLECTION

        ext = validate_file(file)
        loader_key = loader_key_for(ext)
        saved_path = save_upload_file(file, sub_dir=loader_key)

        logger.info(f"Loading '{saved_path}' with loader '{loader_key}'.")
        documents = get_documents(saved_path, loader_key)
        documents = clean_documents(documents)
        documents = validate_documents(documents)
        documents = enrich_metadata(documents, collection_name)

        chunks = split_documents(
            documents,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        self.rag_service.ingest_chunks(chunks, collection_name)

        return {
            "file": file.filename,
            "collection": collection_name,
            "pages_loaded": len(documents),
            "chunks_created": len(chunks),
        }
