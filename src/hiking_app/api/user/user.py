from fastapi import APIRouter, Depends

from hiking_app.db import UserRepository
from hiking_app.core.dependencies import get_user_repo
from hiking_app.service import UserService
from hiking_app.models import User
from .request import RegisterUserRequest
from .response import RegisterUserResponse


user_router = APIRouter()

@user_router.post(
    "/register",
    response_model=RegisterUserResponse,
    summary="Register user",
    status_code=201
)
async def register_user(
    req: RegisterUserRequest,
    repo: UserRepository = Depends(get_user_repo)
    ) -> User:
    return await UserService(repo).register_account(**req.model_dump())