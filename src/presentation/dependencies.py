from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
import jwt
from asyncpg import Connection
from src.application.services.auth.auth_service import AuthService
from src.application.services.container.container_action_service import ContainerActionService
from src.application.services.container.container_info_service import ContainerInfoService
from src.application.services.token.token_service import TokenService
from src.infrastructure.repositories.user_repository import DatabaseUserRepository
from src.infrastructure.repositories.container_repository import DockerContainerRepository
from src.domain.entities import User
from src.database import get_db_connection
from config.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def get_user_repo(request: Request) -> DatabaseUserRepository:
    """
    Dependency to retrieve a user repository.

    Args:
        request (Request): The FastAPI request object.

    Returns:
        DatabaseUserRepository: An instance of the user repository.

    Raises:
        HTTPException: If the database connection pool is not initialized.
    """
    db_pool = getattr(request.app.state, "db_session", None)
    if db_pool is None:
        raise HTTPException(status_code=500, detail="Database connection pool is not initialized")
    return DatabaseUserRepository(db_pool=db_pool)


def get_container_repo(request: Request) -> DockerContainerRepository:
    """
    Dependency to retrieve a container repository.

    Args:
        request (Request): The FastAPI request object.

    Returns:
        DockerContainerRepository: An instance of the container repository.

    Raises:
        HTTPException: If the database connection pool is not initialized.
    """
    db_pool = getattr(request.app.state, "db_session", None)
    if db_pool is None:
        raise HTTPException(status_code=500, detail="Database connection pool is not initialized")
    return DockerContainerRepository(db_pool=db_pool)


def get_token_service() -> TokenService:
    """
    Dependency to retrieve the token service.

    Returns:
        TokenService: An instance of the token service.
    """
    return TokenService(secret_key=settings.secret_key, algorithm=settings.algorithm)


def get_auth_service(
    user_repo: DatabaseUserRepository = Depends(get_user_repo),
    token_service: TokenService = Depends(get_token_service)
) -> AuthService:
    """
    Dependency to retrieve the authentication service.

    Args:
        user_repo (DatabaseUserRepository): The user repository dependency.
        token_service (TokenService): The token service dependency.

    Returns:
        AuthService: An instance of the authentication service.
    """
    return AuthService(user_repo=user_repo, token_service=token_service)


def get_container_action_service(
    container_repo: DockerContainerRepository = Depends(get_container_repo)
) -> ContainerActionService:
    """
    Dependency to retrieve the container action service.

    Args:
        container_repo (DockerContainerRepository): The container repository dependency.

    Returns:
        ContainerActionService: An instance of the container action service.
    """
    return ContainerActionService(container_repo)


def get_container_info_service(
    container_repo: DockerContainerRepository = Depends(get_container_repo)
) -> ContainerInfoService:
    """
    Dependency to retrieve the container information service.

    Args:
        container_repo (DockerContainerRepository): The container repository dependency.

    Returns:
        ContainerInfoService: An instance of the container information service.
    """
    return ContainerInfoService(container_repo)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
    token_service: TokenService = Depends(get_token_service)
) -> User:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Проверяем токен с помощью validate_token из TokenService
        payload = token_service.validate_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except HTTPException as e:
        raise e  # Перебрасываем уже пойманное исключение
    except Exception as e:
        raise credentials_exception

    user = await auth_service.get_user_by_username(username=username)
    if user is None:
        raise credentials_exception

    return user


async def get_db_session(db_connection: Connection = Depends(get_db_connection)):
    """
    Dependency to retrieve the database session.

    Args:
        db_connection (Connection): The database connection dependency.

    Yields:
        Connection: The active database connection.
    """
    yield db_connection
