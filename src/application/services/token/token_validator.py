import logging
from fastapi import HTTPException
import jwt
from config.config import settings

logger = logging.getLogger(__name__)


class TokenValidator:
    def __init__(
        self, secret_key: str = settings.secret_key, algorithm: str = settings.algorithm
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def validate_token(self, token: str) -> dict:
        """
        Validates a JWT token.

        Args:
            token (str): The JWT token to validate.

        Returns:
            dict: The decoded payload of the token.

        Raises:
            HTTPException: If the token is invalid or expired.
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            logger.info(f"Validated token payload: {payload}")
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token error: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid token")
