from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import User
from app.utils.auth import get_password_hash, verify_password, create_access_token
from app.dependencies import get_current_user
from app.utils.response import success_response

router = APIRouter()


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str = Field(...)
    password: str = Field(...)


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/register")
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user. The first user to register becomes the 'admin'.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if this is the first user
    user_count = db.query(User).count()
    role = "admin" if user_count == 0 else "user"

    hashed_pw = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        hashed_password=hashed_pw,
        role=role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return success_response(
        "User registered successfully",
        data={"username": new_user.username, "role": new_user.role}
    )


@router.post("/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    """
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=user.username)
    return success_response(
        "Login successful",
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "username": user.username,
            "role": user.role
        }
    )


@router.get("/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get profile information of the current logged-in user.
    """
    return success_response(
        "User profile retrieved",
        data={
            "id": current_user.id,
            "username": current_user.username,
            "role": current_user.role,
            "created_at": current_user.created_at.isoformat()
        }
    )
