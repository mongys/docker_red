import logging
from typing import Optional
from domain.repositories import UserRepository
from domain.entities import User
from src.database import get_db_connection

logger = logging.getLogger(__name__)

class DatabaseUserRepository(UserRepository):
    """
    Реализация репозитория пользователей, взаимодействующего с базой данных.

    Методы этого класса используют соединение с базой данных для выполнения операций
    по получению и созданию пользователей.
    """

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Получает пользователя из базы данных по его имени.

        Args:
            username (str): Имя пользователя.

        Returns:
            Optional[User]: Объект пользователя, если он найден, иначе None.
        """
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
        """
        Создает нового пользователя в базе данных.

        Args:
            user (User): Объект пользователя, содержащий имя и хэш пароля.

        Side effects:
            Выполняет запись в базу данных.

        Raises:
            Exception: В случае возникновения ошибки записи в базу данных.
        """
        conn = await get_db_connection()
        await conn.execute(
            "INSERT INTO users (username, hashed_password) VALUES ($1, $2)",
            user.username, user.hashed_password
        )
        await conn.close()
        logger.info(f"User {user.username} created successfully")
