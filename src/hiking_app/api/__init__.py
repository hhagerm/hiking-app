from fastapi import APIRouter

from .peaks import peaks_router
from .user import user_router

router = APIRouter()
router.include_router(peaks_router, prefix="/peaks", tags=["Peaks"])
router.include_router(user_router, prefix="/user", tags=["User"])


__all__ = ["router"]
