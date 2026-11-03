from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Index, text

from app.database import Base, utc_now


class DietPlan(Base):
    __tablename__ = "DietPlans"
    __table_args__ = (
        Index(
            "UX_DietPlans_UserIdempotencyKey",
            "UserID",
            "IdempotencyKey",
            unique=True,
            mssql_where=text("[IdempotencyKey] IS NOT NULL"),
        ),
    )

    PlanID = Column(Integer, primary_key=True, index=True)

    UserID = Column(
        Integer,
        ForeignKey("Users.UserID"),
        nullable=False
    )

    PlanName = Column(String(100), nullable=False)
    IdempotencyKey = Column(String(64), nullable=True)
    StartDate = Column(Date, nullable=False)
    EndDate = Column(Date, nullable=True)

    Status = Column(
        String(20),
        nullable=False,
        server_default="Active"
    )

    CreatedAt = Column(
        DateTime,
        nullable=False,
        default=utc_now
    )

    UpdatedAt = Column(DateTime, nullable=True)