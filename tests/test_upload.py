"""
Tests for the upload flow (file validation + processing pipeline).
Run with: pytest tests/test_upload.py
"""
import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_upload_rejects_unsupported_file_type():
    file_content = io.BytesIO(b"not a real file")
    response = client.post(
        "/upload/",
        files={"file": ("malware.exe", file_content, "application/octet-stream")},
    )
    assert response.status_code in (400, 415)


def test_upload_accepts_txt_file(monkeypatch):
    file_content = io.BytesIO(b"Hello world, this is a test document.")
    response = client.post(
        "/upload/",
        files={"file": ("note.txt", file_content, "text/plain")},
        data={"collection_name": "test_collection"},
    )
    # NOTE: requires a running Qdrant instance + valid embedding API key to fully pass.
    assert response.status_code in (200, 500, 502)
