from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    FullName: str = Field(..., min_length=2, max_length=100)
    Email: str = Field(..., max_length=150)
    Password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    UserID: int
    FullName: str
    Email: str
    Role: str
    IsActive: bool

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    Email: str = Field(..., max_length=150)
    Password: str = Field(..., min_length=8)