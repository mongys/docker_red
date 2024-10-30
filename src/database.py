import asyncpg
from config.config import settings
DATABASE_URL = f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"

async def get_db_connection():
    return await asyncpg.connect(dsn=DATABASE_URL)
