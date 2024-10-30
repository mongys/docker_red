import asyncpg
from config.config import settings

# Используем параметры для подключения к базе данных
DATABASE_URL = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

async def get_db_connection():
    return await asyncpg.connect(dsn=DATABASE_URL)
