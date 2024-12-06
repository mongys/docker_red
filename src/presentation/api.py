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
    try:
        await auth_service.create_user(user_data.username, user_data.password)
        return {"message": "User created successfully"}
    except UserAlreadyExistsException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post(
    "/auth/token",
    response_model=TokenModel,
    summary="Get an access token",
    description="Authenticates a user and returns an access token.",
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
    try:
        user = await auth_service.authenticate_user(form_data.username, form_data.password)
        access_token = auth_service.create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
        )
        return {"access_token": access_token, "token_type": "bearer"}
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
    try:
        stats = await container_info_service.get_container_stats(container_id)
        return {
            "cpu_usage": stats.get("cpu_usage", 0),
            "system_cpu_usage": stats.get("system_cpu_usage", 0),
            "memory_usage": stats.get("memory_usage", 0),
            "memory_limit": stats.get("memory_limit", 0),
            "network_io": stats.get("network_io", {}),
        }
    except ContainerNotFoundException:
        raise HTTPException(status_code=404, detail="Container not found")
    except DockerAPIException:
        raise HTTPException(status_code=404, detail="Container not found")
