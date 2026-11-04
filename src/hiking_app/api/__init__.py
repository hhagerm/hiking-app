from fastapi import APIRouter

from .peaks import peaks_router

router = APIRouter()
router.include_router(peaks_router, prefix="/peaks", tags=["Peaks"])


__all__ = ["router"]
