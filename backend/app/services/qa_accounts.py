from dataclasses import dataclass, field
from typing import Literal

from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import User
from app.schemas.schemas import RegistrationInput
from app.security import hash_password
from app.services.transactions import commit_or_raise


@dataclass(frozen=True)
class QAAccount:
    email: str
    full_name: str
    password: str = field(repr=False)
    role: Literal["User", "Coach"]


def provision_qa_accounts(db: Session, accounts: list[QAAccount]) -> list[str]:
    if len(accounts) != 2 or {account.role for account in accounts} != {"User", "Coach"}:
        raise ValueError("Configure exactly one User and one Coach QA account.")

    validated: list[QAAccount] = []
    normalized_emails: set[str] = set()
    for account in accounts:
        details = RegistrationInput(
            full_name=account.full_name,
            email=account.email,
            password=account.password,
        )
        normalized_email = str(details.email).strip().lower()
        if normalized_email in normalized_emails:
            raise ValueError("QA User and Coach accounts must use different email addresses.")
        normalized_emails.add(normalized_email)
        validated.append(
            QAAccount(
                email=normalized_email,
                full_name=details.full_name,
                password=details.password,
                role=account.role,
            )
        )

    outcomes: list[str] = []
    for account in validated:
        existing = db.scalar(
            select(User).where(func.lower(User.email) == account.email)
        )
        if existing is not None:
            if existing.role != account.role:
                outcomes.append("Existing account with a different role left unchanged.")
            elif not existing.is_active:
                outcomes.append(f"Existing {account.role} account is inactive and was left unchanged.")
            else:
                outcomes.append(f"Existing active {account.role} account left unchanged.")
            continue
        db.add(
            User(
                full_name=account.full_name,
                email=account.email,
                password_hash=hash_password(account.password),
                role=account.role,
                is_active=True,
            )
        )
        outcomes.append(f"Created {account.role} QA account.")
    commit_or_raise(db)
    return outcomes
