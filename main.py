from fastapi import FastAPI
import asyncpg
from config.config import settings
from src.interfaces.api import router as api_router

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    # Инициализация пула соединений к базе данных
    dsn = settings.database_dsn
    session_pool = await asyncpg.create_pool(dsn)
    app.state.db_session = session_pool
    app.state.config = settings

@app.on_event("shutdown")
async def shutdown_event():
    # Закрытие пула соединений при завершении работы приложения
    await app.state.db_session.close()

# Подключение роутера
app.include_router(api_router, prefix="/api")

# Проверка конфигурации
@app.get("/config-info")
async def config_info():
    return {
        "secret_key": settings.secret_key,
        "algorithm": settings.algorithm,
        "db_host": settings.db_host,
        "docker_api_version": settings.docker_api_version,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
