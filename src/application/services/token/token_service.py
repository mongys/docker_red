from datetime import datetime, timedelta
from typing import Optional
import jwt
from config.config import settings
import logging

logger = logging.getLogger(__name__)


class TokenService:
    def __init__(self, secret_key: str = settings.secret_key, algorithm: str = settings.algorithm):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        try:
            to_encode = data.copy()
            expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
            to_encode.update({"exp": expire})
            token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            logger.info(f"Access token created: {token}")
            return token
        except Exception as e:
            logger.error(f"Error creating access token: {str(e)}")
            raise


    def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(days=7))
        to_encode.update({"exp": expire, "type": "refresh"})
        token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        logger.info(f"Created refresh token: {token}")
        return token


    def validate_token(self, token: str) -> Optional[dict]:
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
