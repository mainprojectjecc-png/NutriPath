from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey

from app.database import Base, utc_now


class DietPlan(Base):
    __tablename__ = "DietPlans"

    PlanID = Column(Integer, primary_key=True, index=True)

    UserID = Column(
        Integer,
        ForeignKey("Users.UserID"),
        nullable=False
    )

    PlanName = Column(String(100), nullable=False)
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