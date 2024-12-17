from datetime import timedelta
from typing import Optional

from fastapi import HTTPException
from src.domain.entities import User
from src.domain.repositories import UserRepository
from src.domain.exceptions import AuthenticationException, UserAlreadyExistsException
from passlib.context import CryptContext
from src.application.services.token.token_service import TokenService
import logging

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, user_repo: UserRepository, token_service: TokenService):
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
        return self.token_service.create_access_token(data, expires_delta)

    def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        return self.token_service.create_refresh_token(data, expires_delta)

    def validate_token(self, token: str) -> Optional[dict]:
        return self.token_service.validate_token(token)

    async def get_user_by_username(self, username: str) -> Optional[User]:
        return await self.user_repo.get_user_by_username(username)

    async def refresh_access_token(self, refresh_token: str) -> (str, str):
        """
        Валидирует Refresh Token и генерирует новый Access Token и Refresh Token.
        """
        payload = self.validate_token(refresh_token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        user = await self.get_user_by_username(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Генерируем новый Access Token и Refresh Token
        new_access_token = self.create_access_token(data={"sub": username})
        new_refresh_token = self.create_refresh_token(data={"sub": username})

        return new_access_token, new_refresh_token

