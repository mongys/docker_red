import docker
import logging
import os
from docker.errors import DockerException, APIError, NotFound, BuildError
from config.config import settings
from src.domain.exceptions import DockerAPIException

logger = logging.getLogger(__name__)

class DockerHelper:
    """
    A helper class to interact with the Docker API using the docker Python SDK.
    """

    def __init__(self):
        """
        Initializes the Docker client with the specified API version from the settings.
        """
        self.client = docker.from_env(version=settings.docker_api_version)

    def list_containers(self):
        """
        Lists all Docker containers, including stopped ones.

        Returns:
            List: A list of container objects.
        
        Raises:
            DockerAPIException: If there is an error listing the containers.
        """
        try:
            return self.client.containers.list(all=True)
        except DockerException as e:
            logger.error(f"Error listing containers: {str(e)}")
            raise DockerAPIException(str(e))

    def get_container_by_id(self, container_id: str):
        """
        Retrieves a Docker container by its ID.

        Args:
            container_id (str): The ID of the container to retrieve.

        Returns:
            Container: The container object if found, or None if not found.

        Raises:
            DockerAPIException: If there is an API error.
        """
        try:
            return self.client.containers.get(container_id)
        except NotFound:
            return None
        except APIError as e:
            logger.error(f"Error getting container {container_id}: {str(e)}")
            raise DockerAPIException(str(e))

    def build_container(self, repo_dir: str, dockerfile_dir: str) -> str:
        """
        Builds a Docker image from a specified directory.

        Args:
            repo_dir (str): The root directory of the repository.
            dockerfile_dir (str): The directory containing the Dockerfile.

        Returns:
            str: The tag of the built Docker image.

        Raises:
            DockerAPIException: If there is an error during the image build.
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
        Runs a Docker container based on a specified image tag.

        Args:
            image_tag (str): The tag of the image to use for the container.

        Returns:
            Container: The started container object.

        Raises:
            DockerAPIException: If there is an error running the container.
        """
        try:
            container = self.client.containers.run(image=image_tag, detach=True, tty=True, stdin_open=True)
            logger.info(f"Container {container.id} started successfully")
            return container
        except APIError as e:
            logger.error(f"Docker API error: {str(e)}")
            raise DockerAPIException(str(e))
