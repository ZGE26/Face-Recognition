from pydantic import BaseModel


class UserRegisterResponse(BaseModel):
    success: bool
    message: str
    user_id: int | None = None
    name: str | None = None
    employee_id: str | None = None
