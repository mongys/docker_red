from datetime import timedelta
from fastapi import HTTPException
from src.application.services.token.token_validator import TokenValidator
from src.application.services.token.token_creator import TokenCreator
from src.domain.repositories import UserRepository
from config.config import settings
import logging

logger = logging.getLogger(__name__)

class RefreshToken:
    def __init__(self, TokenCreator: TokenCreator, user_repo: UserRepository, token_validator: TokenValidator):
        self.TokenCreator = TokenCreator
        self.user_repo = user_repo
        self.token_validator = token_validator


    async def __call__(self, refresh_token: str) -> str:
        """
        Refreshes an expired access token using the provided refresh token.

        Args:
            refresh_token (str): The refresh JWT token.

        Returns:
            str: A new access JWT token.

        Raises:
            HTTPException: If the refresh token is invalid or expired.
        """
        try:
            payload = self.token_validator.validate_token(refresh_token)
            logger.info(f"Refresh token payload: {payload}")

            if not payload or payload.get("type") != "refresh":
                logger.warning("Invalid token type for refresh")
                raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

            username = payload.get("sub")
            if not username:
                logger.warning("Username missing in token payload")
                raise HTTPException(status_code=401, detail="Invalid token payload")

            user = await self.user_repo.get_user_by_username(username)
            if not user:
                logger.warning(f"User not found: {username}")
                raise HTTPException(status_code=401, detail="User not found")

            new_access_token = self.TokenCreator.create_token(
                data={"sub": username},
                token_type="access",
                expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
            )

            logger.info(f"Generated new access token for user: {username}")
            return new_access_token

        except HTTPException as e:
            logger.warning(f"HTTPException during refresh token: {e.detail}")
            raise
        except Exception as e:
            logger.error(f"Error refreshing access token: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
