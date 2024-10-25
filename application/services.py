import logging
from datetime import timedelta, datetime
from typing import Optional, List
from domain.entities import User, Container
from domain.repositories import UserRepository, ContainerRepository
from domain.exceptions import (
    AuthenticationException,
    UserAlreadyExistsException,
    InvalidTokenException,
)
from jose import JWTError, jwt
from config import settings
from passlib.context import CryptContext

# Настройка логирования и контекста для хэширования паролей
logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """
    Сервис для управления аутентификацией и регистрацией пользователей.

    Предоставляет методы для аутентификации пользователей, создания новых пользователей,
    управления JWT-токенами и хэширования паролей.

    Attributes:
        user_repo (UserRepository): Репозиторий для взаимодействия с данными пользователей.
    """

    def __init__(self, user_repo: UserRepository):
        """
        Инициализирует AuthService с указанным репозиторием пользователей.

        Args:
            user_repo (UserRepository): Репозиторий для доступа к данным пользователей.
        """
        self.user_repo = user_repo

    async def authenticate_user(self, username: str, password: str) -> User:
        """
        Аутентификация пользователя.

        Проверяет существование пользователя в базе данных и проверяет правильность пароля.

        Args:
            username (str): Имя пользователя.
            password (str): Пароль пользователя.

        Raises:
            AuthenticationException: Если пользователь не найден или пароль неверен.

        Returns:
            User: Информация о пользователе, если аутентификация успешна.
        """
        user = await self.user_repo.get_user_by_username(username)
        if not user:
            logger.warning(f"User {username} not found")
            raise AuthenticationException("Incorrect username or password")

        if not self.verify_password(password, user.hashed_password):
            logger.warning(f"Invalid password for user {username}")
            raise AuthenticationException("Incorrect username or password")

        return user

    async def create_user(self, username: str, password: str) -> None:
        """
        Создание нового пользователя с хэшированным паролем.

        Args:
            username (str): Имя пользователя.
            password (str): Пароль пользователя.

        Raises:
            UserAlreadyExistsException: Если пользователь с таким именем уже существует.
        """
        existing_user = await self.user_repo.get_user_by_username(username)
        if existing_user:
            logger.warning(f"User {username} already exists")
            raise UserAlreadyExistsException("User already exists")

        hashed_password = self.get_password_hash(password)
        user = User(username=username, hashed_password=hashed_password)
        await self.user_repo.create_user(user)
        logger.info(f"User {username} created successfully")

    def get_password_hash(self, password: str) -> str:
        """
        Хэширует пароль с использованием bcrypt.

        Args:
            password (str): Пароль для хэширования.

        Returns:
            str: Хэшированный пароль.
        """
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Проверка пароля пользователя.

        Args:
            plain_password (str): Введенный пользователем пароль.
            hashed_password (str): Хэшированный пароль, сохраненный в базе данных.

        Returns:
            bool: True, если пароль верен, иначе False.
        """
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Создает JWT токен для доступа.

        Args:
            data (dict): Данные для включения в токен.
            expires_delta (Optional[timedelta]): Время жизни токена, по умолчанию 15 минут.

        Returns:
            str: Закодированный JWT токен.
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

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
