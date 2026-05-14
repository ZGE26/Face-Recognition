from fastapi import APIRouter

from app.api.v1.routes import register, scan

router = APIRouter()
router.include_router(scan.router, tags=["scan"])
router.include_router(register.router, tags=["register"])
