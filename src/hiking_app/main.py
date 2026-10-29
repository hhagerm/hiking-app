from contextlib import asynccontextmanager

import asyncpg
from fastapi import Depends, FastAPI

from hiking_app.config import PG_DB_URL
from hiking_app.db.poi_repository import POIRepository
from hiking_app.models import PeakDistance

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await asyncpg.create_pool(PG_DB_URL)
    try:
        yield
    finally:
        await app.state.pool.close()


app = FastAPI(lifespan=lifespan)



async def get_poi_repo():
    async with app.state.pool.acquire() as conn:
        yield POIRepository(conn)
    

@app.get("/peaks/nearby")
async def peaks_nearby(
    lat: float, 
    lon: float, 
    radius_m: int = 5000, 
    limit: int = 50, 
    repo: POIRepository = Depends(get_poi_repo)
    ) -> list[PeakDistance]:
    result = await repo.peaks_within_radius(lat, lon, radius_m, limit)
    return result
