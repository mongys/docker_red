# interfaces/dependencies.py

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from application.services import AuthService, ContainerService
from infrastructure.repositories.user_repository import DatabaseUserRepository
from infrastructure.repositories.container_repository import DockerContainerRepository
from domain.exceptions import InvalidTokenException
from domain.entities import User
from jose import JWTError, jwt
from config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def get_user_repo():
    return DatabaseUserRepository()

def get_container_repo():
    return DockerContainerRepository()

def get_auth_service(user_repo = Depends(get_user_repo)):
    return AuthService(user_repo)

def get_container_service(container_repo = Depends(get_container_repo)):
    return ContainerService(container_repo)

async def get_current_user(token: str = Depends(oauth2_scheme), auth_service: AuthService = Depends(get_auth_service)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await auth_service.get_user_by_username(username=username)
    if user is None:
        raise credentials_exception
    return user
