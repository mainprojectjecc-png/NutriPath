from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth import verify_access_token
from app.database import get_db
from app.models.weight_progress import WeightProgress
from app.schemas.weight_progress import (
    WeightProgressCreate,
    WeightProgressResponse,
    WeightProgressUpdate,
)

router = APIRouter(
    prefix="/api/v1/weight-progress",
    tags=["Weight Progress"],
)


def _is_duplicate_key_error(error: IntegrityError) -> bool:
    return any(
        error_code in str(argument)
        for argument in getattr(error.orig, "args", ())
        for error_code in ("2601", "2627")
    )


def _commit_changes(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        if _is_duplicate_key_error(error):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A weight record already exists for this date.",
            ) from error
        raise
    except SQLAlchemyError:
        db.rollback()
        raise


@router.post(
    "/",
    response_model=WeightProgressResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_weight_progress(
    progress_data: WeightProgressCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_access_token),
):
    progress = WeightProgress(
        UserID=current_user["user_id"],
        WeightKg=progress_data.WeightKg,
        RecordDate=progress_data.RecordDate,
        Notes=progress_data.Notes,
    )
    db.add(progress)
    _commit_changes(db)
    db.refresh(progress)
    return progress


@router.get("/", response_model=list[WeightProgressResponse])
def get_weight_history(
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_access_token),
):
    return (
        db.query(WeightProgress)
        .filter(WeightProgress.UserID == current_user["user_id"])
        .order_by(
            WeightProgress.RecordDate.asc(),
            WeightProgress.ProgressID.asc(),
        )
        .all()
    )


@router.get("/latest", response_model=WeightProgressResponse)
def get_latest_weight(
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_access_token),
):
    progress = (
        db.query(WeightProgress)
        .filter(WeightProgress.UserID == current_user["user_id"])
        .order_by(
            WeightProgress.RecordDate.desc(),
            WeightProgress.ProgressID.desc(),
        )
        .first()
    )
    if progress is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Weight record not found",
        )
    return progress


@router.put("/{progress_id}", response_model=WeightProgressResponse)
def update_weight_progress(
    progress_id: int,
    progress_data: WeightProgressUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_access_token),
):
    progress = (
        db.query(WeightProgress)
        .filter(
            WeightProgress.ProgressID == progress_id,
            WeightProgress.UserID == current_user["user_id"],
        )
        .first()
    )
    if progress is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Weight record not found",
        )

    progress.WeightKg = progress_data.WeightKg
    progress.RecordDate = progress_data.RecordDate
    progress.Notes = progress_data.Notes
    _commit_changes(db)
    db.refresh(progress)
    return progress


@router.delete(
    "/{progress_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_weight_progress(
    progress_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_access_token),
) -> Response:
    progress = (
        db.query(WeightProgress)
        .filter(
            WeightProgress.ProgressID == progress_id,
            WeightProgress.UserID == current_user["user_id"],
        )
        .first()
    )
    if progress is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Weight record not found",
        )

    db.delete(progress)
    _commit_changes(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
