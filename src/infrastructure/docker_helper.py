import docker
import logging
import os
from docker.errors import DockerException, APIError, NotFound, BuildError
from config.config import settings
from src.domain.exceptions import DockerAPIException

logger = logging.getLogger(__name__)

class DockerHelper:
    """
    Вспомогательный класс для управления Docker-контейнерами и образами.

    Этот класс предоставляет методы для работы с Docker API, включая список контейнеров,
    получение контейнеров по имени, создание образов из Dockerfile и запуск контейнеров.
    """

    def __init__(self):
        """
        Инициализация Docker клиента с версией API, заданной в конфигурации.
        """
        self.client = docker.from_env(version=settings.docker_api_version)

    def list_containers(self):
        """
        Получает список всех контейнеров, включая остановленные.

        Returns:
            list: Список объектов контейнеров Docker.

        Raises:
            DockerAPIException: Если возникла ошибка при получении списка контейнеров.
        """
        try:
            return self.client.containers.list(all=True)
        except DockerException as e:
            logger.error(f"Error listing containers: {str(e)}")
            raise DockerAPIException(str(e))

    def get_container_by_name(self, container_name: str):
        """
        Получает контейнер по имени.

        Args:
            container_name (str): Имя контейнера.

        Returns:
            container: Объект контейнера, если найден, иначе None.

        Raises:
            DockerAPIException: Если произошла ошибка при запросе контейнера.
        """
        try:
            return self.client.containers.get(container_name)
        except NotFound:
            return None
        except APIError as e:
            logger.error(f"Error getting container {container_name}: {str(e)}")
            raise DockerAPIException(str(e))

    def build_container(self, repo_dir: str, dockerfile_dir: str) -> str:
        """
        Создает Docker-образ из Dockerfile в указанной директории.

        Args:
            repo_dir (str): Директория репозитория.
            dockerfile_dir (str): Директория Dockerfile относительно корня репозитория.

        Returns:
            str: Тег созданного Docker-образа.

        Raises:
            DockerAPIException: Если возникла ошибка при создании Docker-образа.
        """
        build_path = os.path.join(repo_dir, dockerfile_dir) if dockerfile_dir else repo_dir
        image_tag = os.path.basename(repo_dir)
        try:
            image, _ = self.client.images.build(path=build_path, tag=image_tag)
            logger.info(f"Image {image_tag} built successfully.")
            return image_tag
        except BuildError as e:
            logger.error(f"Error building Docker image: {str(e)}")
            raise DockerAPIException(str(e))

    def run_container(self, image_tag: str):
        """
        Запускает контейнер из указанного образа.

        Args:
            image_tag (str): Тег Docker-образа для запуска контейнера.

        Returns:
            container: Запущенный контейнер.

        Raises:
            DockerAPIException: Если возникла ошибка при запуске контейнера.
        """
        try:
            container = self.client.containers.run(image=image_tag, detach=True)
            logger.info(f"Container {container.id} started successfully")
            return container
        except APIError as e:
            logger.error(f"Docker API error: {str(e)}")
            raise DockerAPIException(str(e))
