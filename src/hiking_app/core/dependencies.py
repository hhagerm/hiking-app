from fastapi import Request, Depends

from hiking_app.db.poi_repository import POIRepository

async def get_conn(request: Request):
    async with request.app.state.pool.acquire() as conn:
        yield conn

async def get_poi_repo(conn=Depends(get_conn)) -> POIRepository:
    return POIRepository(conn)