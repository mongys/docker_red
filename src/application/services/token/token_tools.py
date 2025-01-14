from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException
import jwt
from config.config import settings
import logging

logger = logging.getLogger(__name__)

class TokenTools:
    def __init__(self, secret_key: str = settings.secret_key, algorithm: str = settings.algorithm):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def create_token(self, data: dict, token_type: str = "access", expires_delta: Optional[timedelta] = None) -> str:
        """
        Universal method to create both access and refresh tokens.

        Args:
            data (dict): The payload data for the token.
            token_type (str): The type of token to create ("access" or "refresh").
            expires_delta (Optional[timedelta]): The expiration duration of the token.

        Returns:
            str: The encoded JWT token.

        Raises:
            HTTPException: If token creation fails.
        """
        try:
            to_encode = data.copy()
            # Set default expiration times based on token type
            if token_type == "refresh":
                expire = datetime.utcnow() + (expires_delta or timedelta(days=7))
                to_encode.update({"type": "refresh"})  # Mark as refresh token
            else:  # Default to access token
                expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
            
            to_encode.update({"exp": expire})
            token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            logger.info(f"{token_type.capitalize()} token created: {token}")
            return token
        except Exception as e:
            logger.error(f"Error creating {token_type} token: {str(e)}")
            raise HTTPException(status_code=500, detail=f"{token_type.capitalize()} token creation failed")



    def validate_token(self, token: str) -> dict:
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
        
    async def refresh_access_token(self, refresh_token: str) -> str:
        try:
            payload = self.validate_token(refresh_token)
            logger.info(f"Refresh token payload: {payload}")
            if not payload or payload.get("type") != "refresh":
                logger.warning("Invalid token type for refresh")
                raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

            username = payload.get("sub")
            if not username:
                logger.warning("Username missing in token payload")
                raise HTTPException(status_code=401, detail="Invalid token payload")

            
            new_access_token = self.create_token(
                data={"sub": username},
                token_type="access",
                expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
            )
            
            logger.info(f"Generated new access token for user: {username}")
            return new_access_token
        except HTTPException as e:
            raise e  
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
