from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from src.application.services.auth.auth_service import AuthService
from src.application.services.container.container_action_service import ContainerActionService
from src.application.services.container.container_info_service import ContainerInfoService
from src.presentation.dependencies import get_auth_service, get_container_action_service, get_container_info_service, get_current_user
from src.presentation.schemas import (
    UserCreateModel, TokenModel, UserResponseModel, ContainerInfoModel,
    ContainerActionRequest, CloneAndRunRequest
)
from src.domain.entities import User
from src.domain.exceptions import (
    AuthenticationException, UserAlreadyExistsException, InvalidTokenException,
    ContainerNotFoundException, DockerAPIException
)
from typing import List
from datetime import timedelta
from config.config import settings

router = APIRouter()

# Маршрут для регистрации пользователя
@router.post(
    "/auth/signup",
    response_model=dict,
    summary="Регистрация нового пользователя",
    description="Создаёт нового пользователя в системе. Возвращает сообщение об успешной регистрации.",
    tags=["Аутентификация"],
    responses={
        200: {"description": "Пользователь успешно создан."},
        400: {"description": "Пользователь с таким именем уже существует."},
    }
)
async def signup(user_data: UserCreateModel, auth_service: AuthService = Depends(get_auth_service)):
    try:
        await auth_service.create_user(user_data.username, user_data.password)
        return {"message": "User created successfully"}
    except UserAlreadyExistsException as e:
        raise HTTPException(status_code=400, detail=str(e))

# Маршрут для получения токена доступа
@router.post(
    "/auth/token",
    response_model=TokenModel,
    summary="Получение токена доступа",
    description="Аутентифицирует пользователя и возвращает токен доступа.",
    tags=["Аутентификация"],
    responses={
        200: {"description": "Токен успешно выдан."},
        401: {"description": "Ошибка аутентификации."},
    }
)
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
@router.get(
    "/auth/users/me",
    response_model=UserResponseModel,
    summary="Получить информацию о текущем пользователе",
    description="Возвращает информацию о текущем аутентифицированном пользователе.",
    tags=["Аутентификация"]
)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return UserResponseModel(username=current_user.username)

# Получение списка контейнеров
@router.get(
    "/containers/",
    response_model=List[ContainerInfoModel],
    summary="Получить список контейнеров",
    description="Возвращает список всех контейнеров, доступных в системе.",
    tags=["Контейнеры"],
    responses={
        200: {"description": "Список контейнеров успешно получен."},
        502: {"description": "Ошибка взаимодействия с Docker API."},
    }
)
async def list_containers(
    current_user: User = Depends(get_current_user),
    container_info_service: ContainerInfoService = Depends(get_container_info_service)
):
    try:
        containers = await container_info_service.list_containers()
        return [ContainerInfoModel(**container.__dict__) for container in containers]
    except DockerAPIException as e:
        raise HTTPException(status_code=502, detail="Error communicating with Docker API")

# Запуск контейнера
@router.post(
    "/containers/start/",
    response_model=dict,
    summary="Запустить контейнер",
    description="Запускает контейнер по указанному ID.",
    tags=["Контейнеры"],
    responses={
        200: {"description": "Контейнер успешно запущен."},
        409: {"description": "Контейнер не принадлежит базе данных."},
    }
)
async def start_container(
    request: ContainerActionRequest,
    current_user: User = Depends(get_current_user),
    container_action_service: ContainerActionService = Depends(get_container_action_service)
):
    try:
        await container_action_service.start_container(request.container_id)
        return {"message": f"Container {request.container_id} started"}
    except Exception as e:
        raise HTTPException(status_code=409, detail="Container does not belong to db")

# Остановка контейнера
@router.post(
    "/containers/stop/",
    response_model=dict,
    summary="Остановить контейнер",
    description="Останавливает контейнер по указанному ID.",
    tags=["Контейнеры"],
    responses={
        200: {"description": "Контейнер успешно остановлен."},
        409: {"description": "Контейнер не принадлежит базе данных."},
    }
)
async def stop_container(
    request: ContainerActionRequest,
    current_user: User = Depends(get_current_user),
    container_action_service: ContainerActionService = Depends(get_container_action_service)
):
    try:
        await container_action_service.stop_container(request.container_id)
        return {"message": f"Container {request.container_id} stopped"}
    except Exception as e:
        raise HTTPException(status_code=409, detail="Container does not belong to db")

# Перезапуск контейнера
@router.post(
    "/containers/restart/",
    response_model=dict,
    summary="Перезапустить контейнер",
    description="Перезапускает контейнер по указанному ID.",
    tags=["Контейнеры"],
    responses={
        200: {"description": "Контейнер успешно перезапущен."},
        409: {"description": "Контейнер не принадлежит базе данных."},
    }
)
async def restart_container(
    request: ContainerActionRequest,
    current_user: User = Depends(get_current_user),
    container_action_service: ContainerActionService = Depends(get_container_action_service)
):
    try:
        await container_action_service.restart_container(request.container_id)
        return {"message": f"Container {request.container_id} restarted"}
    except Exception as e:
        raise HTTPException(status_code=409, detail="Container does not belong to db")

# Удаление контейнера
@router.delete(
    "/containers/delete/",
    response_model=dict,
    summary="Удалить контейнер",
    description="Удаляет контейнер по указанному ID.",
    tags=["Контейнеры"],
    responses={
        200: {"description": "Контейнер успешно удалён."},
        409: {"description": "Контейнер не принадлежит базе данных."},
    }
)
async def delete_container(
    request: ContainerActionRequest,
    force: bool = False,
    current_user: User = Depends(get_current_user),
    container_action_service: ContainerActionService = Depends(get_container_action_service)
):
    try:
        await container_action_service.delete_container(request.container_id, force)
        return {"message": f"Container {request.container_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=409, detail="Container does not belong to db")

# Клонирование и запуск контейнера
@router.post(
    "/containers/clone_and_run/",
    response_model=dict,
    summary="Клонировать и запустить контейнер",
    description="Клонирует репозиторий, создаёт Docker-образ и запускает контейнер.",
    tags=["Контейнеры"],
    responses={
        200: {"description": "Контейнер успешно клонирован и запущен."},
        500: {"description": "Ошибка в процессе клонирования и запуска."},
    }
)
async def clone_and_run_container(
    request: CloneAndRunRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    container_action_service: ContainerActionService = Depends(get_container_action_service)
):
    background_tasks.add_task(container_action_service.clone_and_run_container, request.github_url, request.dockerfile_dir)
    return {"message": "Task added to background"}

# Получение статистики контейнера
@router.get(
    "/containers/{container_id}/stats",
    response_model=dict,
    summary="Получить статистику контейнера",
    description="Возвращает статистику использования ресурсов для указанного контейнера.",
    tags=["Контейнеры"],
    responses={
        200: {"description": "Статистика успешно получена."},
        404: {"description": "Контейнер не найден."},
        502: {"description": "Ошибка взаимодействия с Docker API."},
    }
)
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
    except ContainerNotFoundException:
        raise HTTPException(status_code=404, detail="Container not found")
    except DockerAPIException:
        raise HTTPException(status_code=404, detail="Container not running")
