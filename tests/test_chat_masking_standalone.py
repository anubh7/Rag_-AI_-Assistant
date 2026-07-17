import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.connection import Base, get_db
from app.dependencies import get_current_user
from app.database.models import User, Message, ChatSession

# StaticPool forces all connections to share the same in-memory SQLite DB
SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables once
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_current_user():
    db = TestingSessionLocal()
    user = db.query(User).filter(User.username == "test_user").first()
    if not user:
        user = User(
            id=1,
            username="test_user",
            hashed_password="mocked_password_hash",
            role="user"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    db.close()
    return user


# Register FastAPI dependency overrides
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


class TestChatMasking(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Clear messages and sessions between tests, but keep the user
        db = TestingSessionLocal()
        db.query(Message).delete()
        db.query(ChatSession).delete()
        db.commit()
        db.close()

    def test_pii_masking_in_chat(self):
        payload = {
            "query": "My email is test@example.com and my phone number is +1-202-555-0173. Please repeat this exact email and phone back to me.",
            "collection_name": "nonexistent_collection",
            "use_rag": False
        }

        response = self.client.post("/chat/", json=payload)
        self.assertEqual(response.status_code, 200)

        res_data = response.json()
        self.assertEqual(res_data["status"], "success")

        data = res_data["data"]

        # Verify query returned by the API is masked
        self.assertNotIn("test@example.com", data["query"])
        self.assertNotIn("+1-202-555-0173", data["query"])
        self.assertIn("*****", data["query"])

        # Verify answer returned by the API is masked
        self.assertNotIn("test@example.com", data["answer"])
        self.assertNotIn("+1-202-555-0173", data["answer"])

        # Verify what was written to the database history
        db = TestingSessionLocal()
        messages = db.query(Message).all()
        self.assertTrue(len(messages) >= 2, f"Expected at least 2 messages, got {len(messages)}")

        user_msg = next(m for m in messages if m.role == "user")
        assistant_msg = next(m for m in messages if m.role == "assistant")

        # Both database records must not contain raw PII
        self.assertNotIn("test@example.com", user_msg.content)
        self.assertNotIn("+1-202-555-0173", user_msg.content)

        self.assertNotIn("test@example.com", assistant_msg.content)
        self.assertNotIn("+1-202-555-0173", assistant_msg.content)

        print("\nTest Chat Masking PASSED!")
        print("   Stored user message   :", user_msg.content)
        print("   Stored assistant reply:", assistant_msg.content)
        db.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)

