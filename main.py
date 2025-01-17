from fastapi import FastAPI
import asyncpg
from config.config import settings
from src.presentation.router import api_router
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    """
    Initializes the application during the startup phase.
    Sets up a database connection pool and loads application settings.
    """
    dsn = settings.database_dsn
    try:
        session_pool = await asyncpg.create_pool(dsn)
        app.state.db_session = session_pool
        app.state.settings = settings

        logger.info("Application successfully started.")
    except Exception as e:
        logger.error(f"Error during initialization: {e}")
        raise e


@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleans up resources during the shutdown phase.
    Closes the database connection pool.
    """
    if app.state.db_session:
        await app.state.db_session.close()
        logger.info("Database connection pool closed.")


# Include the central router with a prefix /api
app.include_router(api_router, prefix="/api")


@app.get("/config-info")
async def config_info():
    """
    Endpoint to retrieve configuration information.
    Returns:
        dict: Configuration details such as secret key, algorithm, DB host, and Docker API version.
    """
    return {
        "secret_key": app.state.settings.secret_key,
        "algorithm": app.state.settings.algorithm,
        "db_host": app.state.settings.database_dsn.split("@")[1].split("/")[0],
        "docker_api_version": app.state.settings.docker_api_version,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
