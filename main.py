from fastapi import FastAPI
import asyncpg
from config.config import settings
from src.presentation.api import router as api_router
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем приложение FastAPI
app = FastAPI()


@app.on_event("startup")
async def startup_event():
    """
    Событие, выполняемое при старте приложения.
    """
    dsn = settings.database_dsn
    try:
        # Инициализация пула соединений с базой данных
        session_pool = await asyncpg.create_pool(dsn)
        app.state.db_session = session_pool  
        app.state.settings = settings

        logger.info("Приложение успешно запущено.")
    except Exception as e:
        logger.error(f"Ошибка при инициализации: {e}")
        raise e


@app.on_event("shutdown")
async def shutdown_event():
    """
    Событие, выполняемое при завершении работы приложения.
    """
    if app.state.db_session:
        await app.state.db_session.close()
        logger.info("Пул соединений с базой данных закрыт.")
    


# Подключение маршрутов API
app.include_router(api_router, prefix="/api")


@app.get("/config-info")
async def config_info():
    """
    Endpoint для отображения текущих настроек конфигурации.
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
