import logging
from fastapi import Depends, HTTPException, Request, Response
from asyncpg import Connection
from src.application.services.auth.auth_service import AuthService
from src.application.services.container.container_action_service import ContainerActionService
from src.application.services.container.container_info_service import ContainerInfoService
from src.application.services.token.token_tools import TokenTools
from src.application.services.token.refresh_token import RefreshToken
from src.infrastructure.repositories.user_repository import DatabaseUserRepository
from src.infrastructure.repositories.container_repository import DockerContainerRepository
from src.domain.entities import User
from src.database import get_db_connection
from config.config import settings

logger = logging.getLogger(__name__)

def get_user_repo(request: Request) -> DatabaseUserRepository:
    db_pool = getattr(request.app.state, "db_session", None)
    if db_pool is None:
        raise HTTPException(status_code=500, detail="Database connection pool is not initialized")
    return DatabaseUserRepository(db_pool=db_pool)

def get_container_repo(request: Request) -> DockerContainerRepository:
    db_pool = getattr(request.app.state, "db_session", None)
    if db_pool is None:
        raise HTTPException(status_code=500, detail="Database connection pool is not initialized")
    return DockerContainerRepository(db_pool=db_pool)

def get_token_tools() -> TokenTools:
    return TokenTools(secret_key=settings.secret_key, algorithm=settings.algorithm)

def get_refresh_token(
    token_tools: TokenTools = Depends(get_token_tools),
    user_repo: DatabaseUserRepository = Depends(get_user_repo)
) -> RefreshToken:
    return RefreshToken(token_tools=token_tools, user_repo=user_repo)

def get_auth_service(
    user_repo: DatabaseUserRepository = Depends(get_user_repo),
    token_tools: TokenTools = Depends(get_token_tools),
    refresh_token: RefreshToken = Depends(get_refresh_token)
) -> AuthService:
    return AuthService(user_repo=user_repo, token_tools=token_tools, refresh_token=refresh_token)

def get_container_action_service(
    container_repo: DockerContainerRepository = Depends(get_container_repo)
) -> ContainerActionService:
    return ContainerActionService(container_repo)

def get_container_info_service(
    container_repo: DockerContainerRepository = Depends(get_container_repo)
) -> ContainerInfoService:
    return ContainerInfoService(container_repo)

async def get_current_user(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    token_tools: TokenTools = Depends(get_token_tools)
) -> User:
    access_token = request.cookies.get("access_token")

    if not access_token:
        logger.warning("Access token is missing")
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        payload = token_tools.validate_token(access_token)
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Invalid access token payload")
            raise HTTPException(status_code=401, detail="Invalid access token")
    except Exception as e:
        logger.error(f"Unexpected error during token validation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

    user = await auth_service.get_user_by_username(username=username)
    if user is None:
        logger.warning(f"User not found: {username}")
        raise HTTPException(status_code=401, detail="User not found")

    return user

async def get_db_session(db_connection: Connection = Depends(get_db_connection)):
    yield db_connection