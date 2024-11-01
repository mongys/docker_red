from fastapi import FastAPI
import asyncpg
from config.config import settings
from src.presentation.api import router as api_router

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    dsn = settings.database_dsn
    try:
        session_pool = await asyncpg.create_pool(dsn)
        app.state.db_session = session_pool  
        app.state.settings = settings       
    except Exception as e:
        print(f"Failed to create a database pool: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    if app.state.db_session:
        await app.state.db_session.close()

app.include_router(api_router, prefix="/api")

@app.get("/config-info")
async def config_info():
    """
    Endpoint to display current configuration settings.
    """
    return {
        "secret_key": app.state.settings.secret_key,
        "algorithm": app.state.settings.algorithm,
        "db_host": app.state.settings.db_host,
        "docker_api_version": app.state.settings.docker_api_version,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
