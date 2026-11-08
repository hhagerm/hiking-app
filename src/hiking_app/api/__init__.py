from fastapi import APIRouter

from .peaks import peaks_router
from .user import user_router
from .collection import collection_router

router = APIRouter()
router.include_router(peaks_router, prefix="/peaks", tags=["Peaks"])
router.include_router(user_router, prefix="/user", tags=["User"])
router.include_router(collection_router, prefix="/collection", tags=["Collection"])


__all__ = ["router"]
