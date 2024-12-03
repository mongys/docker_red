import asyncpg
from typing import AsyncGenerator
from fastapi import FastAPI, Depends
from config.config import settings

DATABASE_URL = settings.database_dsn

async def init_db_pool():
    return await asyncpg.create_pool(dsn=DATABASE_URL)

async def get_db_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    async with app.state.db_pool.acquire() as connection:
        yield connection

def setup_database(app: FastAPI):
    @app.on_event("startup")
    async def startup_event():
        app.state.db_pool = await init_db_pool()

    @app.on_event("shutdown")
    async def shutdown_event():
        db_pool = app.state.db_pool
        if db_pool:
            await db_pool.close()
        