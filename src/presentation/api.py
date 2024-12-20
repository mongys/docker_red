"""
This module defines the API endpoints for user authentication and Docker container management.

Endpoints include:
- User registration and authentication
- Retrieving current user information
- Listing, starting, stopping, restarting, deleting Docker containers
- Cloning repositories and running containers
- Retrieving container statistics and detailed information
"""
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from src.application.services.auth.auth_service import AuthService
from src.application.services.container.container_action_service import ContainerActionService
from src.application.services.token.token_tools import TokenTools
from src.application.services.container.container_info_service import ContainerInfoService
from src.presentation.dependencies import (
    get_auth_service, get_container_action_service, 
    get_container_info_service, get_current_user
)
from src.presentation.schemas import (
    UserCreateModel, TokenModel, UserResponseModel, ContainerInfoModel,
    ContainerActionRequest, CloneAndRunRequest
)
from src.domain.entities import User
from src.domain.exceptions import (
    AuthenticationException, UserAlreadyExistsException,
    ContainerNotFoundException, DockerAPIException, UserNotFoundException
)
from typing import List, Dict, Any
from datetime import timedelta
from config.config import settings
from src.presentation.dependencies import oauth2_scheme

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post(
    "/auth/signup",
    response_model=dict,
    summary="Register a new user",
    description="Creates a new user in the system. Returns a message about successful registration.",
    tags=["Authentication"],
    responses={
        200: {"description": "User successfully created."},
        400: {"description": "A user with this username already exists."},
    }
)
async def signup(user_data: UserCreateModel, auth_service: AuthService = Depends(get_auth_service)) -> Dict[str, str]:
    """
    Registers a new user with the provided username and password.

    Args:
        user_data (UserCreateModel): The data containing the username and password for the new user.
        auth_service (AuthService): The authentication service dependency.

    Returns:
        Dict[str, str]: A dictionary containing a success message.

    Raises:
        HTTPException: If a user with the provided username already exists.
    """
    try:
        await auth_service.create_user(user_data.username, user_data.password)
        return {"message": "User created successfully"}
    except UserAlreadyExistsException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/auth/token",
    response_model=TokenModel,
    summary="Get an access token",
    description="Authenticates a user with their credentials and returns an access token. "
                "The refresh token is set in an HttpOnly cookie for secure long-term authentication.",
    tags=["Authentication"],
)
async def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenModel:
    logger.info(f"Attempting login for username: {form_data.username}")
    try:
        user = await auth_service.authenticate_user(form_data.username, form_data.password)
        logger.info(f"User authenticated: {user.username}")

        access_token = auth_service.create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
        )
        logger.info(f"Access token created for user: {user.username}")

        refresh_token = auth_service.create_refresh_token(
            data={"sub": user.username},
            expires_delta=timedelta(days=settings.refresh_token_expire_days)
        )
        logger.info(f"Refresh token created for user: {user.username}")

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax"
        )
        logger.info("Refresh token set in cookies")

        return {"access_token": access_token, "token_type": "bearer"}
    except AuthenticationException:
        logger.warning("Authentication failed for user")
        raise HTTPException(status_code=401, detail="Invalid username or password")
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get(
    "/auth/tokens/current",
    response_model=Dict[str, str],
    summary="Get current tokens and expiration info",
    description="Returns the current access and refresh tokens along with their expiration times for the authenticated user.",
    tags=["Authentication"],
    responses={
        200: {"description": "Tokens and expiration information retrieved successfully."},
        401: {"description": "Unauthorized access."},
    }
)
async def get_current_tokens(
    request: Request,
    current_user: User = Depends(get_current_user),
    token_tools: TokenTools = Depends()
) -> Dict[str, str]:
    """
    Retrieves the current access and refresh tokens along with their expiration times for the authenticated user.

    Args:
        request (Request): The HTTP request object containing cookies.
        current_user (User): The currently authenticated user, provided by the dependency.
        token_tools (TokenTools): The service for handling token operations.

    Returns:
        Dict[str, str]: A dictionary containing access and refresh tokens, and their expiration times.
    """
    try:
        # Extract tokens from request
        auth_header = request.headers.get("Authorization")
        access_token = auth_header.split(" ")[1] if auth_header and " " in auth_header else None
        refresh_token = request.cookies.get("refresh_token")

        if not access_token:
            raise HTTPException(status_code=401, detail="Access token is missing.")
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Refresh token is missing.")

        # Decode tokens to extract expiration information
        try:
            access_payload = token_tools.validate_token(access_token)
        except HTTPException as e:
            raise HTTPException(status_code=401, detail="Invalid access token.") from e

        try:
            refresh_payload = token_tools.validate_token(refresh_token)
        except HTTPException as e:
            raise HTTPException(status_code=401, detail="Invalid refresh token.") from e

        return {
            "access_token": access_token,
            "access_token_expiry": datetime.utcfromtimestamp(access_payload["exp"]).isoformat(),
            "refresh_token": refresh_token,
            "refresh_token_expiry": datetime.utcfromtimestamp(refresh_payload["exp"]).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error retrieving tokens: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not retrieve tokens and expiration info.")

@router.post(
    "/auth/refresh_token",
    response_model=TokenModel,
    summary="Refresh access token",
    description="Refreshes an expired access token using the refresh token stored in the HttpOnly cookie.",
    tags=["Authentication"],
)
async def refresh_access_token_endpoint(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenModel:
    # Получаем refresh_token из cookies
    refresh_token = request.cookies.get("refresh_token")
    logger.info(f"Received refresh_token: {refresh_token}")

    if not refresh_token:
        logger.warning("Refresh token is missing in the cookies")
        raise HTTPException(status_code=401, detail="Refresh token is missing")
        
    try:
        # Используем метод AuthService для обновления токена
        new_access_token = await auth_service.refresh_access_token(refresh_token)
        return {"access_token": new_access_token, "token_type": "bearer"}
    except HTTPException as e:
        logger.warning(f"HTTPException during refresh token: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during refresh token: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/auth/users/me",
    response_model=UserResponseModel,
    summary="Get current user information",
    description="Returns information about the currently authenticated user.",
    tags=["Authentication"]
)
async def read_users_me(current_user: User = Depends(get_current_user)) -> UserResponseModel:
    """
    Retrieves information about the currently authenticated user.

    Args:
        current_user (User): The currently authenticated user, provided by the dependency.

    Returns:
        UserResponseModel: A Pydantic model containing the user's information.
    """
    return UserResponseModel(username=current_user.username)

@router.get(
    "/containers/",
    response_model=List[ContainerInfoModel],
    summary="Get a list of containers",
    description="Returns a list of all containers available on the system.",
    tags=["Containers"],
    responses={
        200: {"description": "Container list successfully received."},
        502: {"description": "Error of interaction with Docker API."},
    }
)
async def list_containers(
    current_user: User = Depends(get_current_user),
    container_info_service: ContainerInfoService = Depends(get_container_info_service)
) -> List[ContainerInfoModel]:
    """
    Retrieves a list of all Docker containers available on the system.

    Args:
        current_user (User): The currently authenticated user.
        container_info_service (ContainerInfoService): The service to retrieve container information.

    Returns:
        List[ContainerInfoModel]: A list of Pydantic models representing Docker containers.

    Raises:
        HTTPException: If there is an error communicating with the Docker API.
    """
    try:
        containers = await container_info_service.list_containers()
        return [ContainerInfoModel(**container.__dict__) for container in containers]
    except DockerAPIException as e:
        raise HTTPException(status_code=502, detail="Error communicating with Docker API")

@router.post(
    "/containers/start/",
    response_model=dict,
    summary="Start a container",
    description="Starts a container by the specified ID.",
    tags=["Containers"],
    responses={
        200: {"description": "Container successfully started."},
        409: {"description": "Container is not found in the system."},
    }
)
async def start_container(
    request: ContainerActionRequest,
    current_user: User = Depends(get_current_user),
    container_action_service: ContainerActionService = Depends(get_container_action_service)
) -> Dict[str, str]:
    """
    Starts a Docker container identified by its ID.

    Args:
        request (ContainerActionRequest): The request containing the container ID to start.
        current_user (User): The currently authenticated user.
        container_action_service (ContainerActionService): The service to perform container actions.

    Returns:
        Dict[str, str]: A dictionary containing a success message.

    Raises:
        HTTPException: If the container is not found in the system.
    """
    try:
        await container_action_service.start_container(request.container_id)
        return {"message": f"Container {request.container_id} started"}
    except ContainerNotFoundException:
        raise HTTPException(status_code=409, detail="Container is not found in the system")

@router.post(
    "/containers/stop/",
    response_model=dict,
    summary="Stop a container",
    description="Stops a container by the specified ID.",
    tags=["Containers"],
    responses={
        200: {"description": "Container successfully stopped."},
        409: {"description": "Container is not found in the system."},
    }
)
async def stop_container(
    request: ContainerActionRequest,
    current_user: User = Depends(get_current_user),
    container_action_service: ContainerActionService = Depends(get_container_action_service)
) -> Dict[str, str]:
    """
    Stops a Docker container identified by its ID.

    Args:
        request (ContainerActionRequest): The request containing the container ID to stop.
        current_user (User): The currently authenticated user.
        container_action_service (ContainerActionService): The service to perform container actions.

    Returns:
        Dict[str, str]: A dictionary containing a success message.

    Raises:
        HTTPException: If the container is not found in the system.
    """
    try:
        await container_action_service.stop_container(request.container_id)
        return {"message": f"Container {request.container_id} stopped"}
    except ContainerNotFoundException:
        raise HTTPException(status_code=409, detail="Container is not found in the system")

@router.post(
    "/containers/restart/",
    response_model=dict,
    summary="Restart a container",
    description="Restarts a container by the specified ID.",
    tags=["Containers"],
    responses={
        200: {"description": "Container successfully restarted."},
        409: {"description": "Container is not found in the system."},
    }
)
async def restart_container(
    request: ContainerActionRequest,
    current_user: User = Depends(get_current_user),
    container_action_service: ContainerActionService = Depends(get_container_action_service)
) -> Dict[str, str]:
    """
    Restarts a Docker container identified by its ID.

    Args:
        request (ContainerActionRequest): The request containing the container ID to restart.
        current_user (User): The currently authenticated user.
        container_action_service (ContainerActionService): The service to perform container actions.

    Returns:
        Dict[str, str]: A dictionary containing a success message.

    Raises:
        HTTPException: If the container is not found in the system.
    """
    try:
        await container_action_service.restart_container(request.container_id)
        return {"message": f"Container {request.container_id} restarted"}
    except ContainerNotFoundException:
        raise HTTPException(status_code=409, detail="Container is not found in the system")

@router.delete(
    "/containers/delete/",
    response_model=dict,
    summary="Delete a container",
    description="Deletes a container by the specified ID.",
    tags=["Containers"],
    responses={
        200: {"description": "Container successfully deleted."},
        409: {"description": "Container is not found in the system."},
    }
)
async def delete_container(
    request: ContainerActionRequest,
    force: bool = False,
    current_user: User = Depends(get_current_user),
    container_action_service: ContainerActionService = Depends(get_container_action_service)
) -> Dict[str, str]:
    """
    Deletes a Docker container identified by its ID.

    Args:
        request (ContainerActionRequest): The request containing the container ID to delete.
        force (bool): Whether to force delete the container. Defaults to False.
        current_user (User): The currently authenticated user.
        container_action_service (ContainerActionService): The service to perform container actions.

    Returns:
        Dict[str, str]: A dictionary containing a success message.

    Raises:
        HTTPException: If the container is not found in the system.
    """
    try:
        await container_action_service.delete_container(request.container_id, force)
        return {"message": f"Container {request.container_id} deleted"}
    except ContainerNotFoundException:
        raise HTTPException(status_code=409, detail="Container is not found in the system")

@router.post(
    "/containers/clone_and_run/",
    response_model=dict,
    summary="Clone and run a container",
    description="Clones a repository, builds a Docker image, and runs a container.",
    tags=["Containers"],
    responses={
        200: {"description": "Container successfully cloned and started."},
        500: {"description": "Error during cloning and starting process."},
    }
)
async def clone_and_run_container(
    request: CloneAndRunRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    container_action_service: ContainerActionService = Depends(get_container_action_service)
) -> Dict[str, str]:
    """
    Clones a GitHub repository, builds a Docker image from it, and runs the container.

    Args:
        request (CloneAndRunRequest): The request containing the GitHub URL and Dockerfile directory.
        background_tasks (BackgroundTasks): FastAPI BackgroundTasks for running tasks in the background.
        current_user (User): The currently authenticated user.
        container_action_service (ContainerActionService): The service to perform container actions.

    Returns:
        Dict[str, str]: A dictionary containing a success message.

    Raises:
        HTTPException: If an error occurs during cloning, building, or running the container.
    """
    background_tasks.add_task(container_action_service.clone_and_run_container, request.github_url, request.dockerfile_dir)
    return {"message": "Container successfully cloned and started"}

@router.get(
    "/containers/{container_id}/stats",
    response_model=dict,
    summary="Get container statistics",
    description="Returns resource usage statistics for the specified container.",
    tags=["Containers"],
    responses={
        200: {"description": "Statistics successfully retrieved."},
        404: {"description": "Container not found."},
        502: {"description": "Error interacting with Docker API."},
    }
)
async def get_container_stats(
    container_id: str,
    current_user: User = Depends(get_current_user),
    container_info_service: ContainerInfoService = Depends(get_container_info_service)
) -> Dict[str, Any]:
    """
    Retrieves resource usage statistics for a specified Docker container.

    Args:
        container_id (str): The unique identifier of the Docker container.
        current_user (User): The currently authenticated user.
        container_info_service (ContainerInfoService): The service to retrieve container information.

    Returns:
        Dict[str, Any]: A dictionary containing CPU usage, memory usage, and network I/O statistics.

    Raises:
        HTTPException: If the container is not found or there is an error communicating with the Docker API.
    """
    try:
        stats = await container_info_service.get_container_stats(container_id)
        return {
            "cpu_usage": stats.get("cpu_usage_percent", 0),
            "memory_usage": stats.get("memory_usage", "0 B"),
            "memory_limit": stats.get("memory_limit", "0 B"),
            "network_io": stats.get("network_io", {}),
        }
    except (ContainerNotFoundException, DockerAPIException):
        raise HTTPException(status_code=404, detail="Container not found")

@router.get(
    "/containers/{container_id}",
    response_model=ContainerInfoModel,
    summary="Get container information",
    description="Retrieve detailed information about a specific Docker container.",
    tags=["Containers"],
    responses={
        200: {"description": "Container information retrieved successfully."},
        404: {"description": "Container not found."},
    }
)
async def get_container_info(
    container_id: str,
    current_user: User = Depends(get_current_user),
    container_info_service: ContainerInfoService = Depends(get_container_info_service)
) -> ContainerInfoModel:
    """
    Retrieves detailed information about a specific Docker container.

    Args:
        container_id (str): The unique identifier of the Docker container.
        current_user (User): The currently authenticated user.
        container_info_service (ContainerInfoService): The service to retrieve container information.

    Returns:
        ContainerInfoModel: A Pydantic model containing detailed information about the container.

    Raises:
        HTTPException: If the container is not found.
    """
    try:
        container = await container_info_service.get_container_info(container_id)
        return ContainerInfoModel(**container.__dict__)
    except ContainerNotFoundException:
        raise HTTPException(status_code=404, detail="Container not found")
