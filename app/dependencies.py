"""
Shared FastAPI dependencies (DI layer).
Provides singleton-ish access to services so routers stay thin (Controller layer).
"""

from functools import lru_cache
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import User
from app.utils.auth import decode_token
from app.services.upload_service import UploadService
from app.services.rag_service import RAGService
from app.services.chat_service import ChatService
from app.services.retrieval_service import RetrievalService
from app.services.collection_service import CollectionService
from app.vector_db.qdrant_service import QdrantService
from app.embeddings.embedding_factory import get_embedding_model
from app.llm.llm_factory import get_llm

# Setup JWT security bearer scheme
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency that decodes the bearer JWT token and retrieves the current authenticated user.
    """
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def check_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency that requires the current user to have the 'admin' role.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted. Admin privileges required.",
        )
    return current_user


@lru_cache()
def get_qdrant_service() -> QdrantService:
    return QdrantService()


@lru_cache()
def get_collection_service() -> CollectionService:
    return CollectionService(qdrant_service=get_qdrant_service())


@lru_cache()
def get_retrieval_service() -> RetrievalService:
    return RetrievalService(qdrant_service=get_qdrant_service())


@lru_cache()
def get_rag_service() -> RAGService:
    return RAGService(
        qdrant_service=get_qdrant_service(),
        embedding_model=get_embedding_model(),
    )


@lru_cache()
def get_upload_service() -> UploadService:
    return UploadService(rag_service=get_rag_service())


@lru_cache()
def get_chat_service() -> ChatService:
    return ChatService(
        retrieval_service=get_retrieval_service(),
        llm=get_llm(),
    )

