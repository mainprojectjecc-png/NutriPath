from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey
from app.database import Base, utc_now

class WeightProgress(Base):
    __tablename__ = "WeightProgress"

    ProgressID = Column(Integer, primary_key=True, index=True)
    UserID = Column(Integer, ForeignKey("Users.UserID"), nullable=False)
    WeightKg = Column(Numeric(6, 2), nullable=False)
    RecordDate = Column(Date, nullable=False)
    Notes = Column(String(255))
    CreatedAt = Column(DateTime, nullable=False, default=utc_now)