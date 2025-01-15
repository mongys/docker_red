import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from src.application.services.container.container_action_service import ContainerActionService
from src.application.services.container.container_info_service import ContainerInfoService
from src.domain.exceptions import ContainerNotFoundException, DockerAPIException
from src.presentation.dependencies import get_container_action_service, get_container_info_service, get_current_user
from src.presentation.schemas import ContainerInfoModel, ContainerActionRequest, CloneAndRunRequest
from typing import List, Dict, Any

router = APIRouter(
    prefix="/containers",
    tags=["Containers"],
    dependencies=[Depends(get_current_user)]  # Все эндпоинты защищены
)

logger = logging.getLogger(__name__)


@router.get(
    "/",
    response_model=List[ContainerInfoModel],
    summary="Get a list of containers",
    description="Returns a list of all containers available on the system.",
)
async def list_containers(
    container_info_service: ContainerInfoService = Depends(get_container_info_service)
) -> List[ContainerInfoModel]:
    try:
        containers = await container_info_service.list_containers()
        return [ContainerInfoModel(**container.__dict__) for container in containers]
    except Exception as exc:
        logger.error(f"Error listing containers: {exc}")
        raise HTTPException(status_code=502, detail="Error communicating with Docker API")


@router.post(
    "/start/",
    response_model=dict,
    summary="Start a container",
    description="Starts a container by the specified ID.",
)
async def start_container(
    request: ContainerActionRequest,
    container_action_service: ContainerActionService = Depends(get_container_action_service),
) -> Dict[str, str]:
    try:
        await container_action_service.start_container(request.container_id)
        return {"message": f"Container {request.container_id} started"}
    except ContainerNotFoundException:
        raise HTTPException(status_code=404, detail="Container not found")


@router.post(
    "/stop/",
    response_model=dict,
    summary="Stop a container",
    description="Stops a container by the specified ID.",
)
async def stop_container(
    request: ContainerActionRequest,
    container_action_service: ContainerActionService = Depends(get_container_action_service),
) -> Dict[str, str]:
    try:
        await container_action_service.stop_container(request.container_id)
        return {"message": f"Container {request.container_id} stopped"}
    except ContainerNotFoundException:
        raise HTTPException(status_code=404, detail="Container not found")


@router.post(
    "/restart/",
    response_model=dict,
    summary="Restart a container",
    description="Restarts a container by the specified ID.",
)
async def restart_container(
    request: ContainerActionRequest,
    container_action_service: ContainerActionService = Depends(get_container_action_service),
) -> Dict[str, str]:
    try:
        await container_action_service.restart_container(request.container_id)
        return {"message": f"Container {request.container_id} restarted"}
    except ContainerNotFoundException:
        raise HTTPException(status_code=404, detail="Container not found")


@router.delete(
    "/delete/",
    response_model=dict,
    summary="Delete a container",
    description="Deletes a container by the specified ID. Use 'force=True' to forcibly remove the container.",
)
async def delete_container(
    request: ContainerActionRequest,
    force: bool = False,
    container_action_service: ContainerActionService = Depends(get_container_action_service),
) -> Dict[str, str]:
    try:
        await container_action_service.delete_container(request.container_id, force)
        return {"message": f"Container {request.container_id} deleted"}
    except ContainerNotFoundException:
        raise HTTPException(status_code=404, detail="Container not found")


@router.post(
    "/clone_and_run/",
    response_model=dict,
    summary="Clone and run a container",
    description="Clones a repository, builds a Docker image, and runs a container.",
)
async def clone_and_run_container(
    request: CloneAndRunRequest,
    background_tasks: BackgroundTasks,
    container_action_service: ContainerActionService = Depends(get_container_action_service),
) -> Dict[str, str]:
    background_tasks.add_task(container_action_service.clone_and_run_container, request.github_url, request.dockerfile_dir)
    return {"message": "Container successfully cloned and started"}


@router.get(
    "/{container_id}/stats",
    response_model=dict,
    summary="Get container statistics",
    description="Returns resource usage statistics for the specified container.",
)
async def get_container_stats(
    container_id: str,
    container_info_service: ContainerInfoService = Depends(get_container_info_service),
) -> Dict[str, Any]:
    try:
        stats = await container_info_service.get_container_stats(container_id)
        return {
            "cpu_usage": stats.get("cpu_usage_percent", 0),
            "memory_usage": stats.get("memory_usage", "0 B"),
            "memory_limit": stats.get("memory_limit", "0 B"),
            "network_io": stats.get("network_io", {}),
        }
    except ContainerNotFoundException:
        raise HTTPException(status_code=404, detail="Container not found")


@router.get(
    "/{container_id}",
    response_model=ContainerInfoModel,
    summary="Get container information",
    description="Retrieve detailed information about a specific Docker container.",
)
async def get_container_info(
    container_id: str,
    container_info_service: ContainerInfoService = Depends(get_container_info_service),
) -> ContainerInfoModel:
    try:
        container = await container_info_service.get_container_info(container_id)
        return ContainerInfoModel(**container.__dict__)
    except ContainerNotFoundException:
        raise HTTPException(status_code=404, detail="Container not found")
