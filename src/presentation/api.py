from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from src.application.services.auth.auth_service import AuthService
from src.application.services.container.container_action_service import ContainerActionService
from src.application.services.container.container_info_service import ContainerInfoService
from src.presentation.dependencies import get_auth_service, get_container_action_service, get_container_info_service, get_current_user
from src.presentation.schemas import UserCreateModel, TokenModel, UserResponseModel, ContainerInfoModel, ContainerActionRequest, CloneAndRunRequest
from src.domain.entities import User
from src.domain.exceptions import AuthenticationException, UserAlreadyExistsException, InvalidTokenException, ContainerNotFoundException, DockerAPIException
from typing import List
from datetime import timedelta
from config.config import settings

router = APIRouter()

# Маршрут для регистрации пользователя
@router.post("/auth/signup", response_model=dict)
async def signup(user_data: UserCreateModel, auth_service: AuthService = Depends(get_auth_service)):
    try:
        await auth_service.create_user(user_data.username, user_data.password)
        return {"message": "User created successfully"}
    except UserAlreadyExistsException as e:
        raise HTTPException(status_code=400, detail=str(e))

# Маршрут для получения токена доступа
@router.post("/auth/token", response_model=TokenModel)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        user = await auth_service.authenticate_user(form_data.username, form_data.password)
        access_token = auth_service.create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except AuthenticationException as e:
        raise HTTPException(status_code=401, detail=str(e))

# Получение информации о текущем пользователе
@router.get("/auth/users/me", response_model=UserResponseModel)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return UserResponseModel(username=current_user.username)

# Получение списка контейнеров
@router.get("/containers/", response_model=List[ContainerInfoModel])
async def list_containers(
    current_user: User = Depends(get_current_user),
    container_info_service: ContainerInfoService = Depends(get_container_info_service)
):
    try:
        containers = await container_info_service.list_containers()
        return [ContainerInfoModel(**container.__dict__) for container in containers]
    except DockerAPIException as e:
        raise HTTPException(status_code=500, detail=str(e))

# Запуск контейнера
@router.post("/containers/start/", response_model=dict)
async def start_container(
    request: ContainerActionRequest,
    current_user: User = Depends(get_current_user),
    container_action_service: ContainerActionService = Depends(get_container_action_service)
):
    try:
        await container_action_service.start_container(request.container_id)
        return {"message": f"Container {request.container_id} started"}
    except ContainerNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DockerAPIException as e:
        raise HTTPException(status_code=500, detail=str(e))

# Остановка контейнера
@router.post("/containers/stop/", response_model=dict)
async def stop_container(
    request: ContainerActionRequest,
    current_user: User = Depends(get_current_user),
    container_action_service: ContainerActionService = Depends(get_container_action_service)
):
    try:
        await container_action_service.stop_container(request.container_id)
        return {"message": f"Container {request.container_id} stopped"}
    except ContainerNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DockerAPIException as e:
        raise HTTPException(status_code=500, detail=str(e))

# Перезапуск контейнера
@router.post("/containers/restart/", response_model=dict)
async def restart_container(
    request: ContainerActionRequest,
    current_user: User = Depends(get_current_user),
    container_action_service: ContainerActionService = Depends(get_container_action_service)
):
    try:
        await container_action_service.restart_container(request.container_id)
        return {"message": f"Container {request.container_id} restarted"}
    except ContainerNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DockerAPIException as e:
        raise HTTPException(status_code=500, detail=str(e))

# Получение информации о конкретном контейнере
@router.get("/containers/{container_id}/", response_model=ContainerInfoModel)
async def get_container_info(
    container_id: str,
    current_user: User = Depends(get_current_user),
    container_info_service: ContainerInfoService = Depends(get_container_info_service)
):
    try:
        container = await container_info_service.get_container_info(container_id)
        if container is None:
            raise HTTPException(status_code=404, detail="Container not found")
        return ContainerInfoModel(**container.__dict__)
    except DockerAPIException as e:
        raise HTTPException(status_code=500, detail=str(e))


# Удаление контейнера
@router.delete("/containers/delete/", response_model=dict)
async def delete_container(
    request: ContainerActionRequest,
    force: bool = False,
    current_user: User = Depends(get_current_user),
    container_action_service: ContainerActionService = Depends(get_container_action_service)
):
    try:
        await container_action_service.delete_container(request.container_id, force)
        return {"message": f"Container {request.container_id} deleted"}
    except ContainerNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DockerAPIException as e:
        raise HTTPException(status_code=500, detail=str(e))

# Клонирование и запуск контейнера из репозитория
@router.post("/containers/clone_and_run/", response_model=dict)
async def clone_and_run_container(
    request: CloneAndRunRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    container_action_service: ContainerActionService = Depends(get_container_action_service)
):
    background_tasks.add_task(container_action_service.clone_and_run_container, request.github_url, request.dockerfile_dir)
    return {"message": "Task added to background"}

@router.get("/containers/{container_id}/stats", response_model=dict)
async def get_container_stats(
    container_id: str,
    current_user: User = Depends(get_current_user),
    container_info_service: ContainerInfoService = Depends(get_container_info_service)
):
    try:
        stats = await container_info_service.get_container_stats(container_id)
        return {
            "cpu_usage": stats.get("cpu_usage", 0),
            "system_cpu_usage": stats.get("system_cpu_usage", 0),
            "memory_usage": stats.get("memory_usage", 0),
            "memory_limit": stats.get("memory_limit", 0),
            "network_io": stats.get("network_io", {}),
        }
    except ContainerNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DockerAPIException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

