import jwt
from datetime import datetime, timedelta
from typing import Optional
from src.config import settings

class TokenService:
    """
    Класс для работы с JWT-токенами: генерация, проверка и декодирование.
    """
    
    def __init__(self, secret_key: str = settings.JWT_SECRET_KEY, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def generate_token(self, username: str, expires_in: int = 60) -> str:
        """
        Генерация JWT-токена для указанного пользователя.

        Args:
            username (str): Имя пользователя для включения в токен.
            expires_in (int): Срок действия токена в минутах.

        Returns:
            str: Сгенерированный JWT-токен.
        """
        expiration = datetime.utcnow() + timedelta(minutes=expires_in)
        payload = {"sub": username, "exp": expiration}
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def validate_token(self, token: str) -> Optional[str]:
        """
        Проверка валидности JWT-токена.

        Args:
            token (str): Токен для проверки.

        Returns:
            Optional[str]: Имя пользователя, если токен валиден, иначе None.
        
        Raises:
            jwt.ExpiredSignatureError: Если срок действия токена истек.
            jwt.InvalidTokenError: Если токен недействителен.
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload.get("sub")
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError:
            logger.error("Invalid token")
            return None

    def decode_token(self, token: str) -> Optional[dict]:
        """
        Декодирование JWT-токена без проверки срока действия.

        Args:
            token (str): Токен для декодирования.

        Returns:
            Optional[dict]: Полезная нагрузка токена, если токен успешно декодирован, иначе None.
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={"verify_exp": False})
            return payload
        except jwt.InvalidTokenError:
            logger.error("Failed to decode token")
            return None
