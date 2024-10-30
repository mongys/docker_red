import logging
from datetime import timedelta, datetime
from typing import Optional, List
from src.domain.entities import User, Container
from src.domain.repositories import UserRepository, ContainerRepository
from src.domain.exceptions import AuthenticationException, UserAlreadyExistsException, InvalidTokenException
from jose import JWTError, jwt
from config.config import settings
from passlib.context import CryptContext
from src.application.token_service import TokenService

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, user_repo: UserRepository, token_service: TokenService):
        """
        Инициализирует AuthService с репозиторием пользователей и сервисом токенов.

        Args:
            user_repo (UserRepository): Репозиторий для доступа к данным пользователей.
            token_service (TokenService): Сервис для создания и проверки JWT токенов.
        """
        self.user_repo = user_repo
        self.token_service = token_service

    async def authenticate_user(self, username: str, password: str) -> User:
        user = await self.user_repo.get_user_by_username(username)
        if not user:
            logger.warning(f"User {username} not found")
            raise AuthenticationException("Incorrect username or password")

        if not self.verify_password(password, user.hashed_password):
            logger.warning(f"Invalid password for user {username}")
            raise AuthenticationException("Incorrect username or password")

        return user

    async def create_user(self, username: str, password: str) -> None:
        existing_user = await self.user_repo.get_user_by_username(username)
        if existing_user:
            logger.warning(f"User {username} already exists")
            raise UserAlreadyExistsException("User already exists")

        hashed_password = self.get_password_hash(password)
        user = User(username=username, hashed_password=hashed_password)
        await self.user_repo.create_user(user)
        logger.info(f"User {username} created successfully")

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Создает JWT токен с использованием TokenService.

        Args:
            data (dict): Данные для включения в токен.
            expires_delta (Optional[timedelta]): Время жизни токена.

        Returns:
            str: Закодированный JWT токен.
        """
        return self.token_service.create_access_token(data, expires_delta)

    def validate_token(self, token: str) -> Optional[dict]:
        """
        Проверяет валидность JWT токена с использованием TokenService.

        Args:
            token (str): Токен для проверки.

        Returns:
            Optional[dict]: Декодированное содержимое токена, если валиден, иначе None.
        """
        return self.token_service.validate_token(token)
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Получение пользователя по имени.

        Args:
            username (str): Имя пользователя.

        Returns:
            Optional[User]: Данные пользователя или None, если пользователь не найден.
        """
        return await self.user_repo.get_user_by_username(username)


class ContainerService:
    """
    Сервис для управления контейнерами Docker.

    Предоставляет методы для списка контейнеров, запуска, остановки, перезапуска,
    удаления и запуска контейнеров из репозитория.

    Attributes:
        container_repo (ContainerRepository): Репозиторий для взаимодействия с данными контейнеров.
    """

    def __init__(self, container_repo: ContainerRepository):
        """
        Инициализирует ContainerService с указанным репозиторием контейнеров.

        Args:
            container_repo (ContainerRepository): Репозиторий для доступа к данным контейнеров.
        """
        self.container_repo = container_repo

    async def list_containers(self) -> List[Container]:
        """
        Получает список всех контейнеров.

        Returns:
            List[Container]: Список объектов контейнеров.
        """
        return await self.container_repo.list_containers()

    async def start_container(self, container_name: str) -> None:
        """
        Запускает указанный контейнер.

        Args:
            container_name (str): Имя контейнера для запуска.
        """
        await self.container_repo.start_container(container_name)

    async def stop_container(self, container_name: str) -> None:
        """
        Останавливает указанный контейнер.

        Args:
            container_name (str): Имя контейнера для остановки.
        """
        await self.container_repo.stop_container(container_name)

    async def restart_container(self, container_name: str) -> None:
        """
        Перезапускает указанный контейнер.

        Args:
            container_name (str): Имя контейнера для перезапуска.
        """
        await self.container_repo.restart_container(container_name)

    async def get_container_info(self, container_name: str) -> Container:
        """
        Получает информацию о конкретном контейнере.

        Args:
            container_name (str): Имя контейнера.

        Returns:
            Container: Объект контейнера с информацией о нем.
        """
        return await self.container_repo.get_container_info(container_name)

    async def delete_container(self, container_name: str, force: bool = False) -> None:
        """
        Удаляет указанный контейнер.

        Args:
            container_name (str): Имя контейнера для удаления.
            force (bool): Принудительное удаление контейнера.
        """
        await self.container_repo.delete_container(container_name, force)

    async def clone_and_run_container(self, github_url: str, dockerfile_dir: str) -> None:
        """
        Клонирует репозиторий из GitHub и запускает контейнер с Dockerfile.

        Args:
            github_url (str): URL-адрес GitHub-репозитория.
            dockerfile_dir (str): Путь к директории с Dockerfile.
        """
        await self.container_repo.clone_and_run_container(github_url, dockerfile_dir)
