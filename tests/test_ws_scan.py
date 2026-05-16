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

    assert result.get("error")
    assert "recognized" not in result


@requires_face
async def test_process_frame_empty_db_returns_not_recognized(db):
    from app.api.v1.routes.ws_scan import process_frame

    with open(FACE1_PATH, "rb") as f:
        image_bytes = f.read()
    result = await process_frame(db, image_bytes)

    assert result["recognized"] is False
    assert result.get("user_id") is None
    assert "scanned_at" in result


@requires_face
async def test_process_frame_registered_face_returns_recognized(db):
    from app.api.v1.routes.ws_scan import process_frame

    with open(FACE1_PATH, "rb") as f:
        image_bytes = f.read()
    reg = await register_user(db, "Arya", "EMP999", image_bytes)
    result = await process_frame(db, image_bytes)

    assert result["recognized"] is True
    assert result["user_id"] == reg.user_id
    assert 0.0 < result["confidence"] <= 1.0
    assert "scanned_at" in result
