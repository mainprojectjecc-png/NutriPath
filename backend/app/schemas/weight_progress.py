from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class WeightProgressCreate(BaseModel):
    WeightKg: Decimal = Field(..., gt=0, max_digits=6, decimal_places=2)
    RecordDate: date
    Notes: str | None = Field(default=None, max_length=255)


class WeightProgressUpdate(WeightProgressCreate):
    pass


class WeightProgressResponse(BaseModel):
    ProgressID: int
    UserID: int
    WeightKg: Decimal
    RecordDate: date
    Notes: str | None
    CreatedAt: datetime

    model_config = ConfigDict(from_attributes=True)