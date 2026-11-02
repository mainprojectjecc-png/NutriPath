import hashlib
import os
import secrets
import smtplib
from datetime import timedelta
from email.message import EmailMessage

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db, utc_now
from app.models import LoginSession, PasswordReset, User
from app.schemas.schemas import EmailInput, LoginInput, PasswordResetInput, RegistrationInput
from app.security import create_session, current_user, hash_password, revoke_session, verify_password

router = APIRouter(prefix="/api/auth", tags=["authentication"])


def _lookup_user(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.strip().lower()))


def _user_view(user: User) -> dict:
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "onboarding_completed": bool(user.profile and user.profile.goal),
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegistrationInput, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    if _lookup_user(db, email):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    user = User(full_name=payload.full_name.strip(), email=email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    token, expires_at = create_session(db, user)
    return {"access_token": token, "token_type": "bearer", "expires_at": expires_at, "user": _user_view(user)}


@router.post("/login")
def login(payload: LoginInput, db: Session = Depends(get_db)):
    user = _lookup_user(db, payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    token, expires_at = create_session(db, user)
    return {"access_token": token, "token_type": "bearer", "expires_at": expires_at, "user": _user_view(user)}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(authorization: str | None = Header(default=None), user: User = Depends(current_user), db: Session = Depends(get_db)):
    if authorization and authorization.lower().startswith("bearer "):
        revoke_session(db, authorization[7:].strip())
    return None


@router.get("/me")
def me(user: User = Depends(current_user)):
    return _user_view(user)


def _send_reset_email(email: str, token: str) -> None:
    host = os.getenv("NUTRIPATH_SMTP_HOST")
    if not host:
        return
    message = EmailMessage()
    message["Subject"] = "Reset your NutriPath password"
    message["From"] = os.getenv("NUTRIPATH_SMTP_FROM", "noreply@nutripath.local")
    message["To"] = email
    frontend_url = os.getenv("NUTRIPATH_FRONTEND_URL", "http://localhost:5173")
    message.set_content(f"Use this password reset link within 30 minutes:\n{frontend_url}/?reset_token={token}")
    port = int(os.getenv("NUTRIPATH_SMTP_PORT", "587"))
    with smtplib.SMTP(host, port, timeout=10) as server:
        server.starttls()
        username = os.getenv("NUTRIPATH_SMTP_USERNAME")
        password = os.getenv("NUTRIPATH_SMTP_PASSWORD")
        if username and password:
            server.login(username, password)
        server.send_message(message)


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
def forgot_password(payload: EmailInput, db: Session = Depends(get_db)):
    if not os.getenv("NUTRIPATH_SMTP_HOST"):
        raise HTTPException(status_code=503, detail="Password reset email is not configured. Please contact support.")
    user = _lookup_user(db, payload.email)
    token = secrets.token_urlsafe(32)
    if user:
        token_hash = hashlib.sha256(token.encode("ascii")).hexdigest()
        db.add(PasswordReset(user_id=user.id, token_hash=token_hash, expires_at=utc_now() + timedelta(minutes=30)))
        db.commit()
    try:
        _send_reset_email(payload.email, token)
    except (OSError, smtplib.SMTPException):
        raise HTTPException(status_code=503, detail="Password reset email could not be sent. Please try again later.") from None
    return {"message": "If an account exists for this email, password reset instructions will be sent."}


@router.post("/reset-password")
def reset_password(payload: PasswordResetInput, db: Session = Depends(get_db)):
    token_hash = hashlib.sha256(payload.token.encode("utf-8")).hexdigest()
    reset = db.scalar(select(PasswordReset).where(PasswordReset.token_hash == token_hash, PasswordReset.used.is_(False)))
    if not reset or reset.expires_at <= utc_now():
        raise HTTPException(status_code=400, detail="This password reset link is invalid or expired.")
    user = db.get(User, reset.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="This password reset link is invalid or expired.")
    reset.used = True
    user.password_hash = hash_password(payload.new_password)
    db.query(PasswordReset).filter(PasswordReset.user_id == user.id, PasswordReset.id != reset.id).update({"used": True})
    db.query(LoginSession).filter_by(user_id=user.id).update({"revoked": True})
    db.commit()
    return {"message": "Your password has been updated. You can now sign in."}
