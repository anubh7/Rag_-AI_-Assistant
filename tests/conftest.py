import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.connection import Base, get_db
from app.dependencies import get_current_user
from app.database.models import User
from app.main import app

# Create in-memory SQLite database for unit tests
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize schema in in-memory test database
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
