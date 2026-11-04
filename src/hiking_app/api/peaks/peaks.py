from typing import Annotated

from fastapi import APIRouter, Depends, Query

from hiking_app.db import POIRepository
from hiking_app.models import PeakDistance
from hiking_app.core.dependencies import get_poi_repo

peaks_router = APIRouter()

@peaks_router.get(
    "/nearby",
    summary="Get Peaks within radius",
)
async def peaks_nearby(
    lat: Annotated[float, Query(ge=-90, le=90)],
    lon: Annotated[float, Query(ge=-180, le=180)],
    radius_m: Annotated[int, Query(gt=0, le=50_000)] = 5000,
    limit: Annotated[int, Query(gt=0, le=200)] = 50,
    repo: POIRepository = Depends(get_poi_repo),
    ) -> list[PeakDistance]:
    return await repo.peaks_within_radius(lat, lon, radius_m, limit)