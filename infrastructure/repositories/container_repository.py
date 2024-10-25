import logging
import os
from typing import Optional, List
from domain.repositories import ContainerRepository
from domain.entities import Container
from domain.exceptions import ContainerNotFoundException, DockerAPIException
from infrastructure.docker_helper import DockerHelper
from infrastructure.git_helper import GitHelper

logger = logging.getLogger(__name__)


class DockerContainerRepository(ContainerRepository):
    """
    Класс репозитория Docker-контейнеров, реализующий интерфейс ContainerRepository.

    Использует помощники DockerHelper и GitHelper для управления контейнерами и репозиториями Git.
    """

    def __init__(self):
        """Инициализация помощников Docker и Git для взаимодействия с контейнерами и репозиториями."""
        self.docker_helper = DockerHelper()
        self.git_helper = GitHelper()

    async def list_containers(self) -> List[Container]:
        """
        Получение списка всех Docker-контейнеров.

        Returns:
            List[Container]: Список объектов контейнеров.
        
        Raises:
            DockerAPIException: В случае ошибки взаимодействия с Docker API.
        """
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

    async def start_container(self, container_name: str) -> None:
        """
        Запуск контейнера по его имени.

        Args:
            container_name (str): Имя контейнера для запуска.
        
        Raises:
            ContainerNotFoundException: Если контейнер с указанным именем не найден.
        """
        container = self.docker_helper.get_container_by_name(container_name)
        if not container:
            raise ContainerNotFoundException(f"Container {container_name} not found")
        container.start()

    async def stop_container(self, container_name: str) -> None:
        """
        Остановка контейнера по его имени.

        Args:
            container_name (str): Имя контейнера для остановки.
        
        Raises:
            ContainerNotFoundException: Если контейнер с указанным именем не найден.
        """
        container = self.docker_helper.get_container_by_name(container_name)
        if not container:
            raise ContainerNotFoundException(f"Container {container_name} not found")
        container.stop()

    async def restart_container(self, container_name: str) -> None:
        """
        Перезапуск контейнера по его имени.

        Args:
            container_name (str): Имя контейнера для перезапуска.
        
        Raises:
            ContainerNotFoundException: Если контейнер с указанным именем не найден.
        """
        container = self.docker_helper.get_container_by_name(container_name)
        if not container:
            raise ContainerNotFoundException(f"Container {container_name} not found")
        container.restart()

    async def get_container_info(self, container_name: str) -> Optional[Container]:
        """
        Получение информации о контейнере по его имени.

        Args:
            container_name (str): Имя контейнера для получения информации.
        
        Returns:
            Optional[Container]: Объект контейнера, если он существует, иначе None.
        
        Raises:
            ContainerNotFoundException: Если контейнер с указанным именем не найден.
        """
        container = self.docker_helper.get_container_by_name(container_name)
        if not container:
            raise ContainerNotFoundException(f"Container {container_name} not found")
        return Container(
            id=container.id,
            name=container.name,
            status=container.status,
            image=container.image.tags[0] if container.image.tags else "No tag available"
        )

    async def delete_container(self, container_name: str, force: bool = False) -> None:
        """
        Удаление контейнера по его имени.

        Args:
            container_name (str): Имя контейнера для удаления.
            force (bool): Принудительное удаление контейнера. По умолчанию False.
        
        Raises:
            ContainerNotFoundException: Если контейнер с указанным именем не найден.
        """
        container = self.docker_helper.get_container_by_name(container_name)
        if not container:
            raise ContainerNotFoundException(f"Container {container_name} not found")
        container.remove(force=force)

    async def clone_and_run_container(self, github_url: str, dockerfile_dir: str) -> None:
        """
        Клонирование репозитория с GitHub и запуск контейнера на основе Dockerfile.

        Args:
            github_url (str): URL-адрес репозитория GitHub.
            dockerfile_dir (str): Директория, содержащая Dockerfile.
        
        Raises:
            DockerAPIException: Если возникает ошибка при клонировании репозитория или создании контейнера.
        """
        repo_dir = f"./repos/{os.path.basename(github_url.rstrip('/').replace('.git', ''))}"
        try:
            self.git_helper.ensure_directory_exists('./repos')
            self.git_helper.clone_or_pull_repo(github_url, repo_dir)
            image_tag = self.docker_helper.build_container(repo_dir, dockerfile_dir)
            self.docker_helper.run_container(image_tag)
        except Exception as e:
            logger.error(f"Error in clone and run: {str(e)}")
            raise DockerAPIException(str(e))
