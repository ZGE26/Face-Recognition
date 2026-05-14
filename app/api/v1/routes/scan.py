from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.schemas.recognition import ScanResponse
from app.services import user_service

router = APIRouter()


@router.post("/scan", response_model=ScanResponse)
async def scan(
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    image_bytes = await image.read()
    return await user_service.scan_face(db, image_bytes)
