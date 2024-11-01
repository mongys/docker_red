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
        app.state.db_session = session_pool  # Store db_session in app state
    except Exception as e:
        print(f"Failed to create a database pool: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    if app.state.db_session:
        await app.state.db_session.close()

app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
