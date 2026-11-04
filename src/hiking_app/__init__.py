from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from hiking_app.core.config import PG_DB_URL
from hiking_app.api import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await asyncpg.create_pool(PG_DB_URL)
    try:
        yield
    finally:
        await app.state.pool.close()

def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.include_router(router)
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
    
    return app

app = create_app()