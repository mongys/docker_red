# application/services.py

from typing import List
from domain.entities import User, Container
from domain.repositories import UserRepository, ContainerRepository
from domain.exceptions import AuthenticationException, UserAlreadyExistsException
# application/services.py

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

logger = logging.getLogger(__name__)

from passlib.context import CryptContext

# Настройка контекста для хэширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def authenticate_user(self, username: str, password: str) -> User:
        """
        Аутентификация пользователя.

        Проверяет существование пользователя в базе данных и проверяет правильность пароля.

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
        existing_user = await self.user_repo.get_user_by_username(username)
        if existing_user:
            logger.warning(f"User {username} already exists")
            raise UserAlreadyExistsException("User already exists")

        hashed_password = self.get_password_hash(password)
        user = User(username=username, hashed_password=hashed_password)
        await self.user_repo.create_user(user)
        logger.info(f"User {username} created successfully")

    def get_password_hash(self, password: str) -> str:
        """Хэширование пароля."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля."""
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Создание JWT токена для доступа."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Получение пользователя по имени."""
        return await self.user_repo.get_user_by_username(username)


class ContainerService:
    def __init__(self, container_repo: ContainerRepository):
        self.container_repo = container_repo

    async def list_containers(self) -> List[Container]:
        return await self.container_repo.list_containers()

    async def start_container(self, container_name: str) -> None:
        await self.container_repo.start_container(container_name)

    async def stop_container(self, container_name: str) -> None:
        await self.container_repo.stop_container(container_name)

    async def restart_container(self, container_name: str) -> None:
        await self.container_repo.restart_container(container_name)

    async def get_container_info(self, container_name: str) -> Container:
        return await self.container_repo.get_container_info(container_name)

    async def delete_container(self, container_name: str, force: bool = False) -> None:
        await self.container_repo.delete_container(container_name, force)

    async def clone_and_run_container(self, github_url: str, dockerfile_dir: str) -> None:
        await self.container_repo.clone_and_run_container(github_url, dockerfile_dir)
