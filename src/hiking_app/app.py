from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from hiking_app.core.config import PG_DB_URL
from hiking_app.api import router
from hiking_app.core.exception_handlers import register_exception_handlers

def make_lifespan(db_url: str):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        pool = await asyncpg.create_pool(db_url)
        app.state.pool = pool
        try:
            yield
        finally:
            await pool.close()

    return lifespan

def create_app(db_url: str = PG_DB_URL) -> FastAPI:
    app = FastAPI(lifespan=make_lifespan(db_url))
    
    register_exception_handlers(app)
        
    app.include_router(router)
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
    
    return app

app = create_app()