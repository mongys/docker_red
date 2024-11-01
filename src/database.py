import asyncpg
from typing import AsyncGenerator
from fastapi import FastAPI, Depends
from config.config import settings

DATABASE_URL = settings.database_dsn

async def init_db_pool():
    """
    Initializes and returns a connection pool to the database.

    Returns:
        asyncpg.Pool: A pool of connections to the database.
    """
    return await asyncpg.create_pool(dsn=DATABASE_URL)

async def get_db_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """
    Provides a database connection from the pool.
    This function is used as a dependency in request handlers.

    Yields:
        asyncpg.Connection: A database connection.
    """
    async with app.state.db_pool.acquire() as connection:
        yield connection

def setup_database(app: FastAPI):
    """
    Sets up the database connection pool and adds event handlers
    for startup and shutdown to manage the pool lifecycle.

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    @app.on_event("startup")
    async def startup_event():
        """
        Initializes the database connection pool and stores it in the app's state.
        """
        app.state.db_pool = await init_db_pool()

    @app.on_event("shutdown")
    async def shutdown_event():
        """
        Closes the database connection pool when the application shuts down.
        """
        db_pool = app.state.db_pool
        if db_pool:
            await db_pool.close()
        