import logging
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories import user_repository
from app.schemas.recognition import ScanResponse
from app.schemas.user import UserRegisterResponse
from app.services import face_service
from app.utils.image_utils import decode_image_rgb

logger = logging.getLogger(__name__)


async def register_user(
    db: AsyncSession,
    name: str,
    employee_id: str,
    image_bytes: bytes,
) -> UserRegisterResponse:
    existing = await user_repository.get_user_by_employee_id(db, employee_id)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Employee ID '{employee_id}' is already registered",
        )

    try:
        image_rgb = decode_image_rgb(image_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    embedding = face_service.extract_single_embedding(image_rgb)
    if embedding is None:
        raise HTTPException(
            status_code=400,
            detail="Exactly one face must be present in the image",
        )

    try:
        user = await user_repository.create_user(db, name, employee_id)
        await user_repository.save_encoding(db, user.id, embedding)
        await db.commit()
    except Exception:
        await db.rollback()
        logger.exception("Failed to persist user during registration")
        raise HTTPException(status_code=500, detail="Failed to save user data")

    return UserRegisterResponse(
        success=True,
        message="User registered successfully",
        user_id=user.id,
        name=user.name,
        employee_id=user.employee_id,
    )


async def scan_face(db: AsyncSession, image_bytes: bytes) -> ScanResponse:
    try:
        image_rgb = decode_image_rgb(image_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    embedding = face_service.extract_best_embedding(image_rgb)
    if embedding is None:
        raise HTTPException(status_code=400, detail="No face detected in the image")

    candidates = await user_repository.get_all_encodings(db)
    match = face_service.find_best_match(embedding, candidates, settings.RECOGNITION_TOLERANCE)

    if match is None:
        return ScanResponse(recognized=False, scanned_at=datetime.utcnow())

    user_id, confidence = match
    user = await user_repository.get_user_by_id(db, user_id)

    return ScanResponse(
        recognized=True,
        user_id=user.id,
        name=user.name,
        employee_id=user.employee_id,
        confidence=confidence,
        scanned_at=datetime.utcnow(),
    )


async def get_user_info(db: AsyncSession, employee_id: str) -> UserRegisterResponse:
    user = await user_repository.get_user_by_employee_id(db, employee_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserRegisterResponse(
        success=True,
        message="User found",
        user_id=user.id,
        name=user.name,
        employee_id=user.employee_id,
    )