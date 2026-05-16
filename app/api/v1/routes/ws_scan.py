import asyncio
import logging
from datetime import datetime, timezone
from functools import partial

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.core.config import settings
from app.repositories import user_repository
from app.schemas.recognition import ScanResponse
from app.services import face_service
from app.utils.image_utils import decode_image_rgb

logger = logging.getLogger(__name__)

router = APIRouter()


async def process_frame(db: AsyncSession, frame_bytes: bytes) -> dict:
    loop = asyncio.get_running_loop()

    def _decode_and_extract(data: bytes):
        img = decode_image_rgb(data)
        return face_service.extract_best_embedding(img)

    try:
        embedding = await loop.run_in_executor(None, _decode_and_extract, frame_bytes)
    except ValueError as e:
        return {"error": str(e)}
    if embedding is None:
        return ScanResponse(
            recognized=False, scanned_at=datetime.now(timezone.utc)
        ).model_dump(mode="json")

    candidates = await user_repository.get_all_encodings(db)
    match = await loop.run_in_executor(
        None,
        partial(
            face_service.find_best_match,
            embedding,
            candidates,
            settings.RECOGNITION_TOLERANCE,
        ),
    )

    if match is None:
        return ScanResponse(
            recognized=False, scanned_at=datetime.now(timezone.utc)
        ).model_dump(mode="json")

    user_id, confidence = match
    user = await user_repository.get_user_by_id(db, user_id)
    if user is None:
        return ScanResponse(
            recognized=False, scanned_at=datetime.now(timezone.utc)
        ).model_dump(mode="json")
    return ScanResponse(
        recognized=True,
        user_id=user.id,
        name=user.name,
        employee_id=user.employee_id,
        confidence=confidence,
        scanned_at=datetime.now(timezone.utc),
    ).model_dump(mode="json")


@router.websocket("/ws/scan")
async def ws_scan(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    await websocket.accept()

    # Single-slot buffer: newer frames silently overwrite unprocessed ones (intentional drop).
    latest_frame: bytes | None = None
    frame_event = asyncio.Event()
    disconnected = False

    async def _receive_loop():
        nonlocal latest_frame, disconnected
        try:
            while True:
                data = await websocket.receive_bytes()
                latest_frame = data
                frame_event.set()
        except WebSocketDisconnect:
            disconnected = True
            frame_event.set()
        except Exception:
            logger.exception("Unexpected error in WS receive loop")
            disconnected = True
            frame_event.set()

    async def _process_loop():
        nonlocal latest_frame
        while True:
            await frame_event.wait()
            frame_event.clear()
            if disconnected:
                break
            frame = latest_frame
            if frame is None:
                continue
            latest_frame = None
            try:
                result = await process_frame(db, frame)
            except Exception:
                logger.exception("Unhandled error processing frame")
                await websocket.close(code=1011)
                break
            try:
                await websocket.send_json(result)
            except Exception:
                logger.exception("Failed to send WS result")
                await websocket.close(code=1011)
                break

    await asyncio.gather(_receive_loop(), _process_loop())
