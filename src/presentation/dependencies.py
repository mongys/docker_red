from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from src.application.services.auth.auth_service import AuthService
from src.application.services.container.container_action_service import ContainerActionService
from src.application.services.container.container_info_service import ContainerInfoService
from src.application.services.token.token_service import TokenService
from src.infrastructure.repositories.user_repository import DatabaseUserRepository
from src.infrastructure.repositories.container_repository import DockerContainerRepository
from src.domain.exceptions import InvalidTokenException
from src.domain.entities import User
from jose import JWTError
from asyncpg import Connection
from src.database import get_db_connection
from config.config import settings
from fastapi import Depends, Request
from src.infrastructure.repositories.user_repository import DatabaseUserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def get_user_repo(request: Request) -> DatabaseUserRepository:
    """
    Returns an instance of DatabaseUserRepository with the database pool.

    Args:
        request (Request): The request object to access the application state.

    Returns:
        DatabaseUserRepository: An instance of the repository with the db pool.
    """
    db_pool = getattr(request.app.state, "db_session", None)
    if db_pool is None:
        raise HTTPException(status_code=500, detail="Database connection pool is not initialized")
    return DatabaseUserRepository(db_pool=db_pool)

def get_container_repo() -> DockerContainerRepository:
    """
    Создает и возвращает экземпляр репозитория контейнеров для взаимодействия с Docker-контейнерами.

    Returns:
        DockerContainerRepository: Экземпляр репозитория контейнеров.
    """
    return DockerContainerRepository()

def get_token_service() -> TokenService:
    """
    Создает и возвращает экземпляр сервиса для работы с токенами.

    Returns:
        TokenService: Экземпляр сервиса для работы с токенами.
    """
    return TokenService(secret_key=settings.secret_key, algorithm=settings.algorithm)

def get_auth_service(user_repo: DatabaseUserRepository = Depends(get_user_repo), 
                     token_service: TokenService = Depends(get_token_service)) -> AuthService:
    """
    Создает и возвращает экземпляр сервиса аутентификации, используя указанный репозиторий пользователей и сервис токенов.

    Args:
        user_repo (DatabaseUserRepository): Репозиторий для доступа к данным пользователей.
        token_service (TokenService): Сервис для работы с токенами.

    Returns:
        AuthService: Экземпляр сервиса аутентификации.
    """
    return AuthService(user_repo=user_repo, token_service=token_service)

def get_container_action_service(container_repo: DockerContainerRepository = Depends(get_container_repo)) -> ContainerActionService:
    """
    Создает и возвращает экземпляр сервиса управления действиями с контейнерами.

    Args:
        container_repo (DockerContainerRepository): Репозиторий для доступа к данным контейнеров.

    Returns:
        ContainerActionService: Экземпляр сервиса управления действиями с контейнерами.
    """
    return ContainerActionService(container_repo)

def get_container_info_service(container_repo: DockerContainerRepository = Depends(get_container_repo)) -> ContainerInfoService:
    """
    Создает и возвращает экземпляр сервиса для получения информации о контейнерах.

    Args:
        container_repo (DockerContainerRepository): Репозиторий для доступа к данным контейнеров.

    Returns:
        ContainerInfoService: Экземпляр сервиса получения информации о контейнерах.
    """
    return ContainerInfoService(container_repo)

async def get_current_user(token: str = Depends(oauth2_scheme), 
                            auth_service: AuthService = Depends(get_auth_service)) -> User:
    """
    Проверяет токен доступа и возвращает текущего пользователя, если аутентификация успешна.

    Args:
        token (str): Токен доступа для аутентификации пользователя.
        auth_service (AuthService): Сервис аутентификации для проверки токена и получения данных пользователя.

    Raises:
        HTTPException: Если токен недействителен или пользователь не найден.

    Returns:
        User: Экземпляр пользователя, соответствующего переданному токену.
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Используем AuthService для декодирования и валидации токена
        payload = auth_service.token_service.validate_token(token)
        if payload is None:
            raise credentials_exception
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await auth_service.get_user_by_username(username=username)
    if user is None:
        raise credentials_exception

    return user


async def get_db_session(db_connection: Connection = Depends(get_db_connection)):
    """
    Возвращает сессию базы данных для использования в репозиториях и сервисах.
    """
    yield db_connection
