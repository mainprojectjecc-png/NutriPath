
from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean, DateTime,
    Index, text
)
from app.database import Base, utc_now
from sqlalchemy import ForeignKey, Text


class FoodItem(Base):
    __tablename__ = "FoodItems"

    __table_args__ = (
        Index(
            "UX_FoodItems_CatalogID",
            "CatalogID",
            unique=True,
            mssql_where=text("[CatalogID] IS NOT NULL"),
        ),
    )

    FoodID = Column(Integer, primary_key=True, index=True)
    CatalogID = Column(String(80), nullable=True)
    FoodName = Column(String(150), nullable=False)
    Category = Column(String(50))
    Calories = Column(Numeric(8, 2), nullable=False)
    Protein = Column(Numeric(8, 2), nullable=False, server_default="0")
    Carbs = Column(Numeric(8, 2), nullable=False, server_default="0")
    Fat = Column(Numeric(8, 2), nullable=False, server_default="0")
    Fiber = Column(Numeric(8, 2), nullable=False, server_default="0")
    ServingSize = Column(String(50))
    IsActive = Column(Boolean, nullable=False, server_default="1")
    CreatedAt = Column(DateTime, nullable=False, default=utc_now)


class FoodSafetyMetadata(Base):
    __tablename__ = "FoodSafetyMetadata"

    FoodID = Column(
        Integer,
        ForeignKey("FoodItems.FoodID"),
        primary_key=True,
    )

    Ingredients = Column(Text, nullable=True)
    Allergens = Column(Text, nullable=True)
    DietaryClassifications = Column(Text, nullable=True)
    AnimalDerivedIngredients = Column(Text, nullable=True)
    CrossContactWarnings = Column(Text, nullable=True)
    VerificationSource = Column(Text, nullable=True)

    IsVerified = Column(
        Boolean,
        nullable=False,
        server_default="0",
    )

    IsVegetarian = Column(Boolean, nullable=True)
    IsVegan = Column(Boolean, nullable=True)
    ContainsEgg = Column(Boolean, nullable=True)
    ContainsDairy = Column(Boolean, nullable=True)
    ContainsHoney = Column(Boolean, nullable=True)
    ContainsFish = Column(Boolean, nullable=True)
    ContainsSeafood = Column(Boolean, nullable=True)
    ContainsMeat = Column(Boolean, nullable=True)

    VerifiedAt = Column(DateTime, nullable=True)