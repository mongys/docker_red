# infrastructure/repositories/user_repository.py

import logging
from typing import Optional
from domain.repositories import UserRepository
from domain.entities import User
from src.database import get_db_connection

logger = logging.getLogger(__name__)

class DatabaseUserRepository(UserRepository):
    async def get_user_by_username(self, username: str) -> Optional[User]:
        conn = await get_db_connection()
        user_record = await conn.fetchrow(
            "SELECT username, hashed_password FROM users WHERE username = $1", username
        )
        await conn.close()
        if user_record:
            return User(
                username=user_record["username"],
                hashed_password=user_record["hashed_password"]
            )
        return None

    async def create_user(self, user: User) -> None:
        conn = await get_db_connection()
        await conn.execute(
            "INSERT INTO users (username, hashed_password) VALUES ($1, $2)",
            user.username, user.hashed_password
        )
        await conn.close()
        logger.info(f"User {user.username} created successfully")
    