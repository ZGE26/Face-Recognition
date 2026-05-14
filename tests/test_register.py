"""
Tests for the register flow — runs directly against service layer (no HTTP).

Before running, place a JPEG or PNG with exactly one face at:
    tests/assets/face1.jpg

Run with:
    pytest tests/test_register.py -v
"""

import os

import pytest
from fastapi import HTTPException

from app.services.user_service import register_user
from tests.conftest import FACE1_PATH

requires_face = pytest.mark.skipif(
    not os.path.exists(FACE1_PATH),
    reason=f"No test image found. Place a single-face photo at: {FACE1_PATH}",
)


@requires_face
async def test_register_success(db):
    image_bytes = open(FACE1_PATH, "rb").read()
    result = await register_user(db, "Arya Putra", "EMP001", image_bytes)

    assert result.success is True
    assert result.user_id is not None
    assert result.name == "Arya Putra"
    assert result.employee_id == "EMP001"


@requires_face
async def test_register_duplicate_employee_id(db):
    image_bytes = open(FACE1_PATH, "rb").read()
    await register_user(db, "Arya Putra", "EMP001", image_bytes)

    with pytest.raises(HTTPException) as exc:
        await register_user(db, "Orang Lain", "EMP001", image_bytes)

    assert exc.value.status_code == 409


@requires_face
async def test_register_multiple_times_different_id(db):
    image_bytes = open(FACE1_PATH, "rb").read()

    result1 = await register_user(db, "User Satu", "EMP001", image_bytes)
    result2 = await register_user(db, "User Dua", "EMP002", image_bytes)

    assert result1.user_id != result2.user_id
    assert result1.employee_id == "EMP001"
    assert result2.employee_id == "EMP002"
