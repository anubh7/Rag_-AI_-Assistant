"""
Tests for Qdrant collection management.
Run with: pytest tests/test_qdrant.py
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_collections_returns_success_envelope():
    response = client.get("/collection/")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert isinstance(body["data"], list)


def test_create_and_delete_collection():
    name = "pytest_temp_collection"
    create_res = client.post("/collection/", json={"collection_name": name})
    assert create_res.status_code == 200

    delete_res = client.delete(f"/collection/{name}")
    assert delete_res.status_code == 200
