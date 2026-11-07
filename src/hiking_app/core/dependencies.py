from fastapi import Request, Depends
from fastapi.security import APIKeyCookie

from hiking_app.core.auth import hash_token
from hiking_app.models import User
from hiking_app.core.exceptions import NotAuthenticated
from hiking_app.db import POIRepository, UserRepository, SessionRepository
from hiking_app.service import UserService

session_cookie = APIKeyCookie(name="session", auto_error=False)

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

async def get_current_user(
    token: str | None = Depends(session_cookie),
    session_repo: SessionRepository = Depends(get_session_repo),
) -> User:
    if token is None:
        raise NotAuthenticated
    user = await session_repo.get_user_by_token(hash_token(token))
    if user is None:
        raise NotAuthenticated
    return user