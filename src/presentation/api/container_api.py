import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from src.application.services.container.container_action_service import (
    ContainerActionService,
)
from src.application.services.container.container_info_service import (
    ContainerInfoService,
)
from src.domain.exceptions import ContainerNotFoundException
from src.presentation.dependencies import (
    get_container_action_service,
    get_container_info_service,
    get_current_user,
)
from src.presentation.schemas import (
    ContainerInfoModel,
    ContainerActionRequest,
    CloneAndRunRequest,
)
from typing import List, Dict, Any

router = APIRouter(
    prefix="/containers",
    tags=["Containers"],
    dependencies=[Depends(get_current_user)],  # All endpoints are secured
)

logger = logging.getLogger(__name__)


@router.get(
    "/",
    response_model=List[ContainerInfoModel],
    summary="Get a list of containers",
    description="Returns a list of all containers available on the system.",
)
async def list_containers(
    container_info_service: ContainerInfoService = Depends(get_container_info_service),
) -> List[ContainerInfoModel]:
    """
    Retrieve a list of all Docker containers on the system.

    Args:
        container_info_service (ContainerInfoService): Service to fetch container information.

    Returns:
        List[ContainerInfoModel]: List of containers with detailed information.

    Raises:
        HTTPException: If there is an error communicating with the Docker API.
    """
    try:
        containers = await container_info_service.list_containers()
        return [ContainerInfoModel(**container.__dict__) for container in containers]
    except Exception as exc:
        logger.error(f"Error listing containers: {exc}")
        raise HTTPException(
            status_code=502, detail="Error communicating with Docker API"
        )


@router.post(
    "/start/",
    response_model=dict,
    summary="Start a container",
    description="Starts a container by the specified ID.",
)
async def start_container(
    request: ContainerActionRequest,
    container_action_service: ContainerActionService = Depends(
        get_container_action_service
    ),
) -> Dict[str, str]:
    """
    Start a specific Docker container by its ID.

    Args:
        request (ContainerActionRequest): Request containing the container ID to start.
        container_action_service (ContainerActionService): Service to perform container actions.

    Returns:
        Dict[str, str]: Message confirming the container has started.

    Raises:
        HTTPException: If the container is not found.
    """
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
    container_action_service: ContainerActionService = Depends(
        get_container_action_service
    ),
) -> Dict[str, str]:
    """
    Stop a specific Docker container by its ID.

    Args:
        request (ContainerActionRequest): Request containing the container ID to stop.
        container_action_service (ContainerActionService): Service to perform container actions.

    Returns:
        Dict[str, str]: Message confirming the container has stopped.

    Raises:
        HTTPException: If the container is not found.
    """
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
    container_action_service: ContainerActionService = Depends(
        get_container_action_service
    ),
) -> Dict[str, str]:
    """
    Restart a specific Docker container by its ID.

    Args:
        request (ContainerActionRequest): Request containing the container ID to restart.
        container_action_service (ContainerActionService): Service to perform container actions.

    Returns:
        Dict[str, str]: Message confirming the container has restarted.

    Raises:
        HTTPException: If the container is not found.
    """
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
    container_action_service: ContainerActionService = Depends(
        get_container_action_service
    ),
) -> Dict[str, str]:
    """
    Delete a specific Docker container by its ID.

    Args:
        request (ContainerActionRequest): Request containing the container ID to delete.
        force (bool): Whether to forcibly remove the container.
        container_action_service (ContainerActionService): Service to perform container actions.

    Returns:
        Dict[str, str]: Message confirming the container has been deleted.

    Raises:
        HTTPException: If the container is not found.
    """
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
    container_action_service: ContainerActionService = Depends(
        get_container_action_service
    ),
) -> Dict[str, str]:
    """
    Clone a GitHub repository, build a Docker image, and run a container.

    Args:
        request (CloneAndRunRequest): Request containing GitHub URL and Dockerfile directory.
        background_tasks (BackgroundTasks): Background task manager to handle asynchronous tasks.
        container_action_service (ContainerActionService): Service to perform container actions.

    Returns:
        Dict[str, str]: Message confirming the container cloning and starting process.
    """
    background_tasks.add_task(
        container_action_service.clone_and_run_container,
        request.github_url,
        request.dockerfile_dir,
    )
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
    """
    Retrieve resource usage statistics for a specific Docker container.

    Args:
        container_id (str): ID of the container to retrieve statistics for.
        container_info_service (ContainerInfoService): Service to fetch container statistics.

    Returns:
        Dict[str, Any]: Dictionary containing resource usage statistics.

    Raises:
        HTTPException: If the container is not found.
    """
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
    """
    Retrieve detailed information about a specific Docker container.

    Args:
        container_id (str): ID of the container to retrieve information for.
        container_info_service (ContainerInfoService): Service to fetch container information.

    Returns:
        ContainerInfoModel: Detailed information about the container.

    Raises:
        HTTPException: If the container is not found.
    """
    try:
        container = await container_info_service.get_container_info(container_id)
        return ContainerInfoModel(**container.__dict__)
    except ContainerNotFoundException:
        raise HTTPException(status_code=404, detail="Container not found")
