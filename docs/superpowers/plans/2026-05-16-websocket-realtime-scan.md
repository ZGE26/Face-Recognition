# WebSocket Real-Time Face Scan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a WebSocket endpoint `/api/v1/ws/scan` that accepts continuous JPEG frames from a browser and streams back JSON face recognition results in real-time.

**Architecture:** Two coroutines per connection (`_receive_loop`, `_process_loop`) run via `asyncio.gather`. The receive loop writes incoming frames to a single shared slot, overwriting stale frames. The process loop consumes the latest frame, runs CPU-bound face recognition in a thread pool, queries the DB, and sends back JSON. One `AsyncSession` per connection (not per frame).

**Tech Stack:** FastAPI WebSocket, asyncio, `face_recognition` via `ThreadPoolExecutor` (`run_in_executor`), SQLAlchemy `AsyncSession`, Pydantic v2 `model_dump(mode='json')`, pytest-asyncio (`asyncio_mode=auto`)

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Create | `app/api/v1/routes/ws_scan.py` | WebSocket handler + `process_frame` logic |
| Modify | `app/api/v1/router.py` | Register `ws_scan` router |
| Create | `tests/test_ws_scan.py` | Tests for `process_frame` function |

---

### Task 1: Write failing tests for `process_frame`

**Files:**
- Create: `tests/test_ws_scan.py`

- [ ] **Step 1: Write the failing test file**

Create `tests/test_ws_scan.py` with this content:

```python
"""
Tests for process_frame — the core recognition logic for the WebSocket scan endpoint.

Run with:
    pytest tests/test_ws_scan.py -v
"""

import os

import pytest

from app.services.user_service import register_user
from tests.conftest import FACE1_PATH

requires_face = pytest.mark.skipif(
    not os.path.exists(FACE1_PATH),
    reason=f"No test image found. Place a single-face photo at: {FACE1_PATH}",
)


async def test_process_frame_corrupt_bytes_returns_error_dict(db):
    from app.api.v1.routes.ws_scan import process_frame

    result = await process_frame(db, b"not an image")

    assert "error" in result
    assert "recognized" not in result


@requires_face
async def test_process_frame_empty_db_returns_not_recognized(db):
    from app.api.v1.routes.ws_scan import process_frame

    image_bytes = open(FACE1_PATH, "rb").read()
    result = await process_frame(db, image_bytes)

    assert result["recognized"] is False
    assert result.get("user_id") is None
    assert "scanned_at" in result


@requires_face
async def test_process_frame_registered_face_returns_recognized(db):
    from app.api.v1.routes.ws_scan import process_frame

    image_bytes = open(FACE1_PATH, "rb").read()
    reg = await register_user(db, "Arya", "EMP999", image_bytes)
    result = await process_frame(db, image_bytes)

    assert result["recognized"] is True
    assert result["user_id"] == reg.user_id
    assert 0.0 < result["confidence"] <= 1.0
    assert "scanned_at" in result
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_ws_scan.py -v
```

Expected: `ImportError` — module `app.api.v1.routes.ws_scan` does not exist yet.

---

### Task 2: Implement `ws_scan.py`

**Files:**
- Create: `app/api/v1/routes/ws_scan.py`

- [ ] **Step 3: Create `app/api/v1/routes/ws_scan.py`**

```python
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
    try:
        image_rgb = decode_image_rgb(frame_bytes)
    except ValueError as e:
        return {"error": str(e)}

    embedding = await loop.run_in_executor(
        None, face_service.extract_best_embedding, image_rgb
    )
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
            result = await process_frame(db, frame)
            try:
                await websocket.send_json(result)
            except Exception:
                logger.exception("Failed to send WS result")
                break

    await asyncio.gather(_receive_loop(), _process_loop())
```

- [ ] **Step 4: Run tests — should now pass**

```bash
pytest tests/test_ws_scan.py -v
```

Expected:

```
tests/test_ws_scan.py::test_process_frame_corrupt_bytes_returns_error_dict PASSED
tests/test_ws_scan.py::test_process_frame_empty_db_returns_not_recognized PASSED (or SKIPPED if face1.jpg absent)
tests/test_ws_scan.py::test_process_frame_registered_face_returns_recognized PASSED (or SKIPPED if face1.jpg absent)
```

- [ ] **Step 5: Commit**

```bash
git add app/api/v1/routes/ws_scan.py tests/test_ws_scan.py
git commit -m "feat: add WebSocket scan endpoint with frame-drop processing"
```

---

### Task 3: Register the WebSocket router

**Files:**
- Modify: `app/api/v1/router.py`

- [ ] **Step 6: Update `app/api/v1/router.py`**

Replace the current content:

```python
from fastapi import APIRouter

from app.api.v1.routes import register, scan

router = APIRouter()
router.include_router(scan.router, tags=["scan"])
router.include_router(register.router, tags=["register"])
```

With:

```python
from fastapi import APIRouter

from app.api.v1.routes import register, scan, ws_scan

router = APIRouter()
router.include_router(scan.router, tags=["scan"])
router.include_router(register.router, tags=["register"])
router.include_router(ws_scan.router, tags=["ws-scan"])
```

- [ ] **Step 7: Verify the server starts without errors**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Expected: server starts cleanly. The endpoint is reachable at `ws://localhost:8000/api/v1/ws/scan`.

- [ ] **Step 8: Run the full test suite to confirm no regressions**

```bash
pytest tests/ -v
```

Expected: all previously passing tests still pass.

- [ ] **Step 9: Commit**

```bash
git add app/api/v1/router.py
git commit -m "feat: register WebSocket scan router"
```
