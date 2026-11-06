from fastapi import Request, Depends

from hiking_app.db import POIRepository, UserRepository, SessionRepository
from hiking_app.service import UserService

async def get_conn(request: Request):
    async with request.app.state.pool.acquire() as conn:
        yield conn

async def get_poi_repo(conn=Depends(get_conn)) -> POIRepository:
    return POIRepository(conn)

async def get_user_repo(conn=Depends(get_conn)) -> UserRepository:
    return UserRepository(conn)

async def get_session_repo(conn=Depends(get_conn)) -> SessionRepository:
    return SessionRepository(conn)

async def get_user_service(
    user_repo: UserRepository = Depends(get_user_repo),
    session_repo: SessionRepository = Depends(get_session_repo),
) -> UserService:
    return UserService(user_repo, session_repo)