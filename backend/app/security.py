import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db, utc_now
from app.models import LoginSession, User


PASSWORD_ITERATIONS = 310_000
LEGACY_PASSWORD_ITERATIONS = 600_000
SESSION_HOURS = 24
bearer = HTTPBearer(auto_error=False)
_development_secret = secrets.token_bytes(32)


def _secret() -> bytes:
    configured = os.getenv("NUTRIPATH_SECRET_KEY")
    if configured:
        return configured.encode("utf-8")
    if os.getenv("NUTRIPATH_ENVIRONMENT", "development") == "production":
        raise RuntimeError("NUTRIPATH_SECRET_KEY must be configured in production.")
    return _development_secret


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    encoded_salt = base64.urlsafe_b64encode(salt).decode()
    encoded_digest = base64.urlsafe_b64encode(digest).decode()
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${encoded_salt}${encoded_digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        parts = stored_hash.split("$")
        if len(parts) == 4 and parts[0] == "pbkdf2_sha256":
            _, rounds, salt, expected = parts
            actual = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                base64.urlsafe_b64decode(salt),
                int(rounds),
            )
            return hmac.compare_digest(base64.urlsafe_b64encode(actual).decode(), expected)

        if len(parts) == 2:
            salt, expected = parts
            actual = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt.encode("utf-8"),
                LEGACY_PASSWORD_ITERATIONS,
            ).hex()
            return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False
    return False


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(db: Session, user: User) -> tuple[str, datetime]:
    expires_at = utc_now() + timedelta(hours=SESSION_HOURS)
    payload = _b64(
        json.dumps(
            {
                "sub": user.id,
                "exp": int(expires_at.timestamp()),
                "jti": secrets.token_urlsafe(16),
            }
        ).encode()
    )
    signature = _b64(hmac.new(_secret(), payload.encode("ascii"), hashlib.sha256).digest())
    token = f"{payload}.{signature}"
    db.add(LoginSession(user_id=user.id, token_hash=_token_hash(token), expires_at=expires_at))
    db.commit()
    return token, expires_at


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="A valid login is required.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not credentials:
        raise unauthorized
    token = credentials.credentials
    try:
        payload, signature = token.split(".", 1)
        expected = _b64(hmac.new(_secret(), payload.encode("ascii"), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise unauthorized
        decoded = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if int(decoded["exp"]) <= int(utc_now().timestamp()):
            raise unauthorized
    except (ValueError, KeyError, TypeError, UnicodeError, json.JSONDecodeError):
        raise unauthorized from None
    session = db.scalar(
        select(LoginSession).where(
            LoginSession.token_hash == _token_hash(token),
            LoginSession.revoked == False,  # noqa: E712
        )
    )
    if not session or session.expires_at <= utc_now():
        raise unauthorized
    user = db.get(User, session.user_id)
    if not user or not user.is_active:
        raise unauthorized
    return user


def revoke_session(db: Session, token: str) -> None:
    session = db.scalar(select(LoginSession).where(LoginSession.token_hash == _token_hash(token)))
    if session:
        session.revoked = True
        db.commit()
