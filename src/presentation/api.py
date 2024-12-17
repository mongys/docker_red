"""
This module defines the API endpoints for user authentication and Docker container management.

Endpoints include:
- User registration and authentication
- Retrieving current user information
- Listing, starting, stopping, restarting, deleting Docker containers
- Cloning repositories and running containers
- Retrieving container statistics and detailed information
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from src.application.services.auth.auth_service import AuthService
from src.application.services.container.container_action_service import ContainerActionService
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
    ContainerNotFoundException, DockerAPIException
)
from typing import List, Dict, Any
from datetime import timedelta
from config.config import settings
from src.presentation.dependencies import oauth2_scheme

router = APIRouter()

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
    description="Authenticates a user and returns an access token and a refresh token.",
    tags=["Authentication"],
    responses={
        200: {"description": "Token successfully issued."},
        401: {"description": "Authentication error."},
    }
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenModel:
    """
    Authenticates a user and issues both an access token and a refresh token.

    Args:
        form_data (OAuth2PasswordRequestForm): The form data containing username and password.
        auth_service (AuthService): The authentication service dependency.

    Returns:
        TokenModel: A Pydantic model containing the access token and refresh token.

    Raises:
        HTTPException: If authentication fails due to invalid credentials.
    """
    try:
        user = await auth_service.authenticate_user(form_data.username, form_data.password)
        access_token = auth_service.create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
        )
        refresh_token = auth_service.create_refresh_token(
            data={"sub": user.username},
            expires_delta=timedelta(days=7)  # Refresh token valid for 7 days
        )
        return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}
    except AuthenticationException as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post(
    "/auth/refresh_token",
    response_model=TokenModel,
    summary="Refresh access token using the refresh token",
    description="Refreshes the access token using the provided refresh token.",
    tags=["Authentication"],
    responses={
        200: {"description": "Access token successfully refreshed."},
        401: {"description": "Invalid or expired refresh token."},
    }
)
async def refresh_access_token(
    refresh_token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenModel:
    """
    Refreshes the access token using the provided refresh token.

    Args:
        refresh_token (str): The refresh token provided in the request.
        auth_service (AuthService): The authentication service dependency.

    Returns:
        TokenModel: A Pydantic model containing the new access token.

    Raises:
        HTTPException: If the refresh token is invalid or expired.
    """
    try:
        new_access_token = await auth_service.refresh_access_token(refresh_token)  # Add await here
        return {"access_token": new_access_token, "token_type": "bearer"}
    except AuthenticationException as e:
        raise HTTPException(status_code=401, detail=str(e))


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
