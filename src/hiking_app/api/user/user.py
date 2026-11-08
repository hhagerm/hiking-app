from fastapi import APIRouter, Depends, Response
from fastapi.security import APIKeyCookie

from hiking_app.core.dependencies import get_user_service, get_current_user
from hiking_app.core.auth import SESSION_TTL
from hiking_app.service import UserService
from hiking_app.models import User
from .request import RegisterUserRequest, LoginUserRequest
from .response import RegisterUserResponse, UserResponse


user_router = APIRouter()


session_cookie = APIKeyCookie(name="session", auto_error=False)


@user_router.post(
    "/register",
    response_model=RegisterUserResponse,
    summary="Register user",
    status_code=201
)
async def register_user(
    req: RegisterUserRequest,
    svc: UserService = Depends(get_user_service),
    ) -> User:
    return await svc.register_account(**req.model_dump())


@user_router.post(
    "/login",
    response_model=UserResponse,
    summary="Login user"
)
async def login_user(
    req: LoginUserRequest,
    response: Response,
    svc: UserService = Depends(get_user_service),
    ):
    user, token = await svc.login_user(**req.model_dump())
    response.set_cookie(
        "session", token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=int(SESSION_TTL.total_seconds()),
        path="/",
    )
    return user

@user_router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user info"
)
async def get_me(
    user: User = Depends(get_current_user),
    ):
    return user