"""
Tests for the scan/recognition flow — runs directly against service layer (no HTTP).

Setup:
  - tests/assets/face1.jpg  : foto wajah orang pertama (diperlukan untuk semua tes)
  - tests/assets/face2.jpg  : foto wajah orang kedua yang BERBEDA (opsional, untuk tes negatif)

Run with:
    pytest tests/test_scan.py -v
"""

import os

import pytest
from fastapi import HTTPException

from app.services.user_service import register_user, scan_face
from tests.conftest import FACE1_PATH, FACE2_PATH

requires_face = pytest.mark.skipif(
    not os.path.exists(FACE1_PATH),
    reason=f"No test image found. Place a single-face photo at: {FACE1_PATH}",
)

requires_two_faces = pytest.mark.skipif(
    not (os.path.exists(FACE1_PATH) and os.path.exists(FACE2_PATH)),
    reason=f"Place two different face photos at {FACE1_PATH} and {FACE2_PATH}",
)


@requires_face
async def test_scan_empty_database_returns_not_recognized(db):
    image_bytes = open(FACE1_PATH, "rb").read()
    result = await scan_face(db, image_bytes)

    assert result.recognized is False
    assert result.user_id is None
    assert result.scanned_at is not None


@requires_face
async def test_scan_registered_face_is_recognized(db):
    image_bytes = open(FACE1_PATH, "rb").read()

    reg = await register_user(db, "Arya Putra", "EMP001", image_bytes)
    result = await scan_face(db, image_bytes)

    assert result.recognized is True
    assert result.user_id == reg.user_id
    assert result.employee_id == "EMP001"
    assert result.confidence is not None
    assert 0.0 < result.confidence <= 1.0


@requires_two_faces
async def test_scan_different_face_not_recognized_as_registered(db):
    face1_bytes = open(FACE1_PATH, "rb").read()
    face2_bytes = open(FACE2_PATH, "rb").read()

    await register_user(db, "Arya Putra", "EMP001", face1_bytes)
    result = await scan_face(db, face2_bytes)

    # face2 either doesn't match EMP001, or is not recognized at all
    if result.recognized:
        assert result.employee_id != "EMP001"
    else:
        assert result.recognized is False


@requires_face
async def test_scan_returns_scanned_at_timestamp(db):
    image_bytes = open(FACE1_PATH, "rb").read()
    await register_user(db, "Arya Putra", "EMP001", image_bytes)
    result = await scan_face(db, image_bytes)

    assert result.scanned_at is not None
