from datetime import datetime

from pydantic import BaseModel


class UserRegisterResponse(BaseModel):
    success: bool
    message: str
    user_id: int | None = None
    name: str | None = None
    employee_id: str | None = None


class UserResponse(BaseModel):
    id: int
    name: str
    employee_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    total: int
    users: list[UserResponse]
