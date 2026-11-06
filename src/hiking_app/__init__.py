from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from hiking_app.core.config import PG_DB_URL
from hiking_app.api import router
from hiking_app.core.exceptions import ValidationFailed, InvalidCredentials

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await asyncpg.create_pool(PG_DB_URL)
    try:
        yield
    finally:
        await app.state.pool.close()

def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    
    @app.exception_handler(ValidationFailed)
    async def validation_failed_handler(
        request: Request, exc: ValidationFailed
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"errors": [{"field": exc.field, "message": exc.message}]},
        )
    
    @app.exception_handler(InvalidCredentials)
    async def invalid_credentials_handler(
        request: Request, exc: InvalidCredentials
    ) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={"errors": [{"field": None, "message": "incorrect username or password"}]},
            headers={"WWW-Authenticate": "Bearer"},
        )
    app.include_router(router)
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
    
    return app

app = create_app()