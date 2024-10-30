import asyncpg
from config.config import settings

# Используем параметры для подключения к базе данных
DATABASE_URL = settings.database_dsn

async def get_db_connection():
    return await asyncpg.connect(dsn=DATABASE_URL)
