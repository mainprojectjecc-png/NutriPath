from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session


def _duplicate_conflict_detail(error: IntegrityError) -> str:
    message = str(error.orig).lower() if getattr(error, "orig", None) is not None else str(error).lower()
    is_duplicate = (
        "duplicate key" in message
        or "unique constraint" in message
        or "unique index" in message
        or "2601" in message
        or "2627" in message
    )
    if is_duplicate and ("foodchangerequests" in message or "nutritionlogid" in message or "mealitemid" in message):
        return "An active replacement request already exists for this food."
    if is_duplicate and ("coachsuggestions" in message or "requestid" in message):
        return "A suggestion already exists for this request."
    if is_duplicate:
        return "This change conflicts with existing data."
    if "cannot insert the value null" in message and "mealitemid" in message:
        return "The database schema is outdated. Apply the food-change request schema update and retry."
    return "The operation conflicts with existing data."


def commit_or_raise(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        detail = _duplicate_conflict_detail(error)
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
                if "database schema is outdated" in detail.lower()
                else status.HTTP_409_CONFLICT
            ),
            detail=detail,
        ) from error
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The database operation could not be completed.",
        ) from error
