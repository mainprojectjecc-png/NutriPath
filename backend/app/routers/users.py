from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserLogin
from app.security import hash_password, verify_password
from app.auth import create_access_token, verify_access_token

from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("/")
def get_users():
    return {
        "message": "User endpoint working",
        "users": []
    }


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.Email == user_data.Email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email is already registered"
        )

    new_user = User(
        FullName=user_data.FullName,
        Email=user_data.Email,
        PasswordHash=hash_password(user_data.Password),
        Role="User",
        IsActive=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@router.post("/login")
def login_user(
    user_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.Email == user_data.username
    ).first()

    if not user or not verify_password(
        user_data.password,
        user.PasswordHash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not user.IsActive:
        raise HTTPException(
            status_code=403,
            detail="Your account is inactive"
        )

    access_token = create_access_token(
        user_id=user.UserID,
        role=user.Role
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me")
def get_current_user(
    current_user: dict = Depends(verify_access_token)
):
    return {
        "message": "Authenticated successfully",
        "user_id": current_user["user_id"],
        "role": current_user["role"]
    }