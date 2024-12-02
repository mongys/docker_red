import docker
import logging
import os
from docker.errors import DockerException, APIError, NotFound, BuildError
from config.config import settings
from src.domain.exceptions import DockerAPIException

logger = logging.getLogger(__name__)

class DockerHelper:

    def __init__(self):
        self.client = docker.from_env(version=settings.docker_api_version)

    def list_containers(self):
        try:
            return self.client.containers.list(all=True)
        except DockerException as e:
            logger.error(f"Error listing containers: {str(e)}")
            raise DockerAPIException(str(e))

    def get_container_by_id(self, container_id: str):
        try:
            return self.client.containers.get(container_id)
        except NotFound:
            return None
        except APIError as e:
            logger.error(f"Error getting container {container_id}: {str(e)}")
            raise DockerAPIException(str(e))


    def build_container(self, repo_dir: str, dockerfile_dir: str) -> str:
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
        try:
            container = self.client.containers.run(image=image_tag, detach=True, tty=True, stdin_open=True)
            logger.info(f"Container {container.id} started successfully")
            return container
        except APIError as e:
            logger.error(f"Docker API error: {str(e)}")
            raise DockerAPIException(str(e))
