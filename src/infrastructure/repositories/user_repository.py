import logging
from typing import Optional
from asyncpg import Pool
from src.domain.repositories import UserRepository
from src.domain.entities import User

logger = logging.getLogger(__name__)

class DatabaseUserRepository(UserRepository):
    """
    A repository for managing user data in the database.
    Implements the UserRepository interface.
    """

    def __init__(self, db_pool: Pool):
        """
        Initializes the repository with a database connection pool.

        Args:
            db_pool (Pool): The database connection pool for asyncpg.
        """
        self.db_pool = db_pool

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Retrieves a user by their username from the database.

        Args:
            username (str): The username of the user to retrieve.

        Returns:
            Optional[User]: A User object if found, or None if not found.
        """
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
        """
        Creates a new user in the database.

        Args:
            user (User): The User object containing the username and hashed password.

        Returns:
            None
        """
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (username, hashed_password) VALUES ($1, $2)",
                user.username,
                user.hashed_password,
            )
        logger.info(f"User {user.username} created successfully")
