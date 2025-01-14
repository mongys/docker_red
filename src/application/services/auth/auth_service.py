from datetime import timedelta
from typing import Optional
from src.domain.entities import User
from src.domain.repositories import UserRepository
from src.domain.exceptions import AuthenticationException, UserAlreadyExistsException
from src.application.services.token.token_tools import TokenTools
from src.application.services.token.refresh_token import RefreshToken
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, user_repo: UserRepository, token_tools: TokenTools, refresh_token: RefreshToken):
        self.user_repo = user_repo
        self.token_tools = token_tools
        self.refresh_token = refresh_token

    async def authenticate_user(self, username: str, password: str) -> User:
        logger.info(f"Authenticating user: {username}")
        try:
            user = await self.user_repo.get_user_by_username(username)
            if not user:
                logger.warning(f"User not found: {username}")
                raise AuthenticationException("Incorrect username or password")

            if not self.verify_password(password, user.hashed_password):
                logger.warning(f"Invalid password for user: {username}")
                raise AuthenticationException("Incorrect username or password")

            logger.info(f"User authenticated: {username}")
            return user
        except Exception as e:
            logger.error(f"Error during user authentication: {str(e)}")
            raise

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

    def create_token(self, data: dict, token_type: str, expires_delta: Optional[timedelta] = None) -> str:
        return self.token_tools.create_token(data, token_type, expires_delta)

    def validate_token(self, token: str) -> dict:
        return self.token_tools.validate_token(token)

    async def get_user_by_username(self, username: str) -> Optional[User]:
        return await self.user_repo.get_user_by_username(username)

    async def refresh_access_token(self, refresh_token: str) -> str:
        return await self.refresh_token.refresh_access_token(refresh_token)



