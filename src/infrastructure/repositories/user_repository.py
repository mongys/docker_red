import logging
from typing import Optional
from asyncpg import Pool, Connection
from src.domain.repositories import UserRepository
from src.domain.entities import User

logger = logging.getLogger(__name__)

class DatabaseUserRepository(UserRepository):
    """
    Реализация репозитория пользователей, взаимодействующего с базой данных.
    
    Методы этого класса используют соединение с базой данных для выполнения операций
    по получению и созданию пользователей.
    """

    def __init__(self, db_pool: Pool):
        """
        Initialize the repository with a connection pool.

        Args:
            db_pool (Pool): The asyncpg connection pool.
        """
        self.db_pool = db_pool

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Получает пользователя из базы данных по его имени.

        Args:
            username (str): Имя пользователя.

        Returns:
            Optional[User]: Объект пользователя, если он найден, иначе None.
        """
        async with self.db_pool.acquire() as conn:  # Acquire connection from the pool
            user_record = await conn.fetchrow(
                "SELECT username, hashed_password FROM users WHERE username = $1", username
            )
        if user_record:
            return User(
                username=user_record["username"],
                hashed_password=user_record["hashed_password"]
            )
        return None

    async def create_user(self, user: User) -> None:
        """
        Создает нового пользователя в базе данных.

        Args:
            user (User): Объект пользователя, содержащий имя и хэш пароля.

        Raises:
            Exception: В случае возникновения ошибки записи в базу данных.
        """
        async with self.db_pool.acquire() as conn:  # Acquire connection from the pool
            await conn.execute(
                "INSERT INTO users (username, hashed_password) VALUES ($1, $2)",
                user.username, user.hashed_password
            )
        logger.info(f"User {user.username} created successfully")
