from fastapi import APIRouter

from app.api.v1.routes import register, scan, user, ws_scan

router = APIRouter()
router.include_router(scan.router, tags=["scan"])
router.include_router(register.router, tags=["register"])
router.include_router(ws_scan.router, tags=["ws-scan"])
router.include_router(user.router)
