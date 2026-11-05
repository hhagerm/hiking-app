from fastapi import Request, Depends

from hiking_app.db import POIRepository, UserRepository

async def get_conn(request: Request):
    async with request.app.state.pool.acquire() as conn:
        yield conn

async def get_poi_repo(conn=Depends(get_conn)) -> POIRepository:
    return POIRepository(conn)

async def get_user_repo(conn=Depends(get_conn)) -> UserRepository:
    return UserRepository(conn)