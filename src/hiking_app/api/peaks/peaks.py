from fastapi import APIRouter, Depends

from hiking_app.db import POIRepository
from hiking_app.models import PeakDistance
from hiking_app.core.dependencies import get_poi_repo

peaks_router = APIRouter()

@peaks_router.get(
    "/nearby",
    summary="Get Peaks within radius",
)
async def peaks_nearby(
    lat: float, 
    lon: float, 
    radius_m: int = 5000, 
    limit: int = 50, 
    repo: POIRepository = Depends(get_poi_repo)
    ) -> list[PeakDistance]:
    result = await repo.peaks_within_radius(lat, lon, radius_m, limit)
    return result