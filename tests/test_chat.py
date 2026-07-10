"""
Tests for the chat endpoint.
Run with: pytest tests/test_chat.py
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_chat_missing_collection_falls_back_to_general_llm():
    response = client.post(
        "/chat/",
        json={"query": "What is the capital of France?", "collection_name": "nonexistent_collection"},
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert len(res_data["data"]["sources"]) == 0


def test_chat_requires_query_field():
    response = client.post("/chat/", json={})
    assert response.status_code == 422
