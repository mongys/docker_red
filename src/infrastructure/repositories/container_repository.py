import logging
import os
from typing import Optional, List
import asyncio
from src.domain.repositories import ContainerRepository
from src.domain.entities import Container
from src.domain.exceptions import ContainerNotFoundException, DockerAPIException
from src.infrastructure.docker_helper import DockerHelper
from src.infrastructure.git_helper import GitHelper

logger = logging.getLogger(__name__)


class DockerContainerRepository(ContainerRepository):

    def __init__(self):
        self.docker_helper = DockerHelper()
        self.git_helper = GitHelper()

    async def list_containers(self) -> List[Container]:
        try:
            containers = self.docker_helper.list_containers()
            return [
                Container(
                    id=c.id,
                    name=c.name,
                    status=c.status,
                    image=c.image.tags[0] if c.image.tags else "No tag available"
                )
                for c in containers
            ]
        except DockerAPIException as e:
            logger.error(f"Docker API error: {str(e)}")
            raise DockerAPIException(str(e))

    async def start_container(self, container_id: str) -> None:
        container = self.docker_helper.get_container_by_id(container_id)
        if not container:
            raise ContainerNotFoundException(f"Container {container_id} not found")
        container.start()

    async def stop_container(self, container_id: str) -> None:
        container = self.docker_helper.get_container_by_id(container_id)
        if not container:
            raise ContainerNotFoundException(f"Container {container_id} not found")
        container.stop()

    async def restart_container(self, container_id: str) -> None:
        container = self.docker_helper.get_container_by_id(container_id)
        if not container:
            raise ContainerNotFoundException(f"Container {container_id} not found")
        container.restart()

    async def get_container_info(self, container_id: str) -> Optional[Container]:
        container = self.docker_helper.get_container_by_id(container_id)
        if not container:
            raise ContainerNotFoundException(f"Container {container_id} не найден")
        return Container(
            id=container.id,
            name=container.name,
            status=container.status,
            image=container.image.tags[0] if container.image.tags else "No tag available"
        )

    async def delete_container(self, container_id: str, force: bool = False) -> None:
        container = self.docker_helper.get_container_by_id(container_id)
        if not container:
            raise ContainerNotFoundException(f"Container {container_id} не найден")
        container.remove(force=force)

    async def clone_and_run_container(self, github_url: str, dockerfile_dir: str) -> None:
        repo_dir = f"./repos/{os.path.basename(github_url.rstrip('/').replace('.git', ''))}"
        try:
            self.git_helper.ensure_directory_exists('./repos')
            self.git_helper.clone_or_pull_repo(github_url, repo_dir)
            image_tag = self.docker_helper.build_container(repo_dir, dockerfile_dir)
            self.docker_helper.run_container(image_tag)
        except Exception as e:
            logger.error(f"Error in clone and run: {str(e)}")
            raise DockerAPIException(str(e))
