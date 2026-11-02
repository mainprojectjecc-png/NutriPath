from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import true
from sqlalchemy.orm import Session

from app.auth import verify_access_token
from app.database import get_db
from app.models.coach_suggestion import CoachSuggestion
from app.models.food_change_request import FoodChangeRequest
from app.models.food_item import FoodItem
from app.models.user import User
from app.schemas.coach import CoachRequestResponse, CoachSuggestionCreate
from app.services.food_change_requests import (
    request_details_query,
    serialize_request_row,
)
from app.services.transactions import commit_or_raise

router = APIRouter(prefix="/api/v1/coach", tags=["Coach"])


def _require_coach(db: Session, current_user: dict) -> int:
    user = (
        db.query(User.UserID, User.Role, User.IsActive)
        .filter(User.UserID == current_user["user_id"])
        .first()
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user no longer exists",
        )
    if user.Role != "Coach" or not user.IsActive:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Coach access is required",
        )
    return user.UserID


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _get_request_response(db: Session, request_id: int) -> CoachRequestResponse:
    row = (
        request_details_query(db)
        .filter(FoodChangeRequest.RequestID == request_id)
        .first()
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food change request not found",
        )
    return CoachRequestResponse.model_validate(
        serialize_request_row(row).model_dump()
    )


@router.get(
    "/requests",
    response_model=list[CoachRequestResponse],
    summary="List pending food change requests",
)
def get_pending_requests(
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_access_token),
) -> list[CoachRequestResponse]:
    _require_coach(db, current_user)
    rows = (
        request_details_query(db)
        .filter(FoodChangeRequest.Status == "Pending")
        .order_by(
            FoodChangeRequest.CreatedAt.asc(),
            FoodChangeRequest.RequestID.asc(),
        )
        .all()
    )
    return [
        CoachRequestResponse.model_validate(
            serialize_request_row(row).model_dump()
        )
        for row in rows
    ]


@router.post(
    "/requests/{request_id}/suggestion",
    response_model=CoachRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a food replacement suggestion",
)
def create_suggestion(
    request_id: Annotated[int, Path(gt=0)],
    suggestion_data: CoachSuggestionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_access_token),
) -> CoachRequestResponse:
    coach_id = _require_coach(db, current_user)
    request = (
        db.query(FoodChangeRequest)
        .filter(FoodChangeRequest.RequestID == request_id)
        .first()
    )
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food change request not found",
        )
    if request.Status != "Pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending food change requests can be reviewed.",
        )

    food = (
        db.query(FoodItem)
        .filter(
            FoodItem.FoodID == suggestion_data.SuggestedFoodID,
            FoodItem.IsActive == true(),
        )
        .first()
    )
    if food is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active suggested food item not found",
        )

    if (
        db.query(CoachSuggestion.SuggestionID)
        .filter(CoachSuggestion.RequestID == request_id)
        .first()
        is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A suggestion already exists for this request.",
        )

    suggestion = CoachSuggestion(
        RequestID=request_id,
        CoachID=coach_id,
        SuggestedFoodID=food.FoodID,
        Message=suggestion_data.Message,
        Status="Pending",
    )
    request_updated = (
        db.query(FoodChangeRequest)
        .filter(
            FoodChangeRequest.RequestID == request_id,
            FoodChangeRequest.Status == "Pending",
        )
        .update(
            {
                FoodChangeRequest.Status: "Reviewed",
                FoodChangeRequest.UpdatedAt: _utcnow(),
            },
            synchronize_session=False,
        )
    )
    if request_updated != 1:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The request has already been reviewed.",
        )
    db.add(suggestion)
    commit_or_raise(db)
    return _get_request_response(db, request_id)


@router.get(
    "/requests/{request_id}",
    response_model=CoachRequestResponse,
    summary="Get a food change request and suggestion",
)
def get_coach_request(
    request_id: Annotated[int, Path(gt=0)],
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_access_token),
) -> CoachRequestResponse:
    _require_coach(db, current_user)
    return _get_request_response(db, request_id)
