from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.schemas.user import UserRegisterResponse
from app.services import user_service

router = APIRouter()


@router.post("/register", response_model=UserRegisterResponse, status_code=201)
async def register(
    name: str = Form(...),
    employee_id: str = Form(...),
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    image_bytes = await image.read()
    return await user_service.register_user(db, name, employee_id, image_bytes)
