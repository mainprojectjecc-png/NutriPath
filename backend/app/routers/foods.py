from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import true
from sqlalchemy.orm import Query as SQLAlchemyQuery
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.food_item import FoodItem
from app.schemas.food_item import FoodItemResponse

router = APIRouter(
    prefix="/api/v1/foods",
    tags=["Foods"],
)


def _active_foods_query(db: Session) -> SQLAlchemyQuery:
    return db.query(FoodItem).filter(FoodItem.IsActive == true())


@router.get(
    "/",
    response_model=list[FoodItemResponse],
    summary="List active food items",
    description="List active foods with optional category and food-name filters.",
)
def list_foods(
    category: str | None = Query(default=None, max_length=50),
    search: str | None = Query(default=None, max_length=150),
    db: Session = Depends(get_db),
) -> list[FoodItem]:
    foods = _active_foods_query(db)

    if category and category.strip():
        foods = foods.filter(FoodItem.Category == category.strip())
    if search and search.strip():
        foods = foods.filter(FoodItem.FoodName.ilike(f"%{search.strip()}%"))

    return foods.order_by(FoodItem.FoodName.asc(), FoodItem.FoodID.asc()).all()


@router.get(
    "/search",
    response_model=list[FoodItemResponse],
    summary="Search active food items",
    description="Search active foods by name or category.",
)
def search_foods(
    query: str | None = Query(default=None, max_length=150),
    db: Session = Depends(get_db),
) -> list[FoodItem]:
    foods = _active_foods_query(db)

    if query and query.strip():
        search_pattern = f"%{query.strip()}%"
        foods = foods.filter(
            FoodItem.FoodName.ilike(search_pattern)
            | FoodItem.Category.ilike(search_pattern)
        )

    return foods.order_by(FoodItem.FoodName.asc(), FoodItem.FoodID.asc()).all()


@router.get(
    "/{food_id}",
    response_model=FoodItemResponse,
    summary="Get an active food item",
    description="Return one active food item by its ID.",
)
def get_food(
    food_id: int = Path(ge=1),
    db: Session = Depends(get_db),
) -> FoodItem:
    food = (
        _active_foods_query(db)
        .filter(FoodItem.FoodID == food_id)
        .first()
    )
    if food is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food item not found",
        )
    return food
