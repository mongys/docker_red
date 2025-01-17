import logging
from typing import Optional
from asyncpg import Pool
from src.domain.repositories import UserRepository
from src.domain.entities import User

logger = logging.getLogger(__name__)


class DatabaseUserRepository(UserRepository):
    def __init__(self, db_pool: Pool):
        self.db_pool = db_pool

    async def get_user_by_username(self, username: str) -> Optional[User]:
        async with self.db_pool.acquire() as conn:  # Acquire connection from the pool
            user_record = await conn.fetchrow(
                "SELECT username, hashed_password FROM users WHERE username = $1",
                username,
            )
        if user_record:
            return User(
                username=user_record["username"],
                hashed_password=user_record["hashed_password"],
            )
        return None

    async def create_user(self, user: User) -> None:
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (username, hashed_password) VALUES ($1, $2)",
                user.username,
                user.hashed_password,
            )
        logger.info(f"User {user.username} created successfully")
