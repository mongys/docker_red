import logging
import os
from typing import Optional, List
from src.domain.repositories import ContainerRepository
from src.domain.entities import Container
from src.domain.exceptions import ContainerNotFoundException, DockerAPIException
from src.infrastructure.docker_helper import DockerHelper
from src.infrastructure.git_helper import GitHelper

logger = logging.getLogger(__name__)


class DockerContainerRepository(ContainerRepository):
    """
    A repository for managing Docker containers and interacting with the database and Docker API.
    """

    def __init__(self, db_pool):
        """
        Initializes the DockerContainerRepository with a database connection pool and helpers.

        Args:
            db_pool: A database connection pool for interacting with the database.
        """
        self.docker_helper = DockerHelper()
        self.git_helper = GitHelper()
        self.db_pool = db_pool

    async def list_containers(self) -> List[Container]:
        """
        Lists all Docker containers present in the database.

        Returns:
            List[Container]: A list of container entities found in both Docker and the database.

        Raises:
            DockerAPIException: If there is an error with the Docker API.
        """
        try:
            containers = self.docker_helper.list_containers()
            container_list = []
            for c in containers:
                is_in_db = await self.is_container_in_db(c.id)
                if not is_in_db:
                    continue

                name = getattr(c, 'name', "No name")
                status = getattr(c, 'status', "unknown")
                image = c.image.tags[0] if c.image.tags else "No tag available"

                container = Container(
                    id=c.id,
                    name=name,
                    status=status,
                    image=image
                )
                logger.debug(f"Container created: {container}")
                container_list.append(container)
            return container_list
        except DockerAPIException as e:
            logger.error(f"Docker API error: {str(e)}")
            raise DockerAPIException(str(e))

    async def start_container(self, container_id: str) -> None:
        """
        Starts a container by its ID.

        Args:
            container_id (str): The ID of the container to start.

        Raises:
            ContainerNotFoundException: If the container is not found in the database or Docker.
        """
        if not await self.is_container_in_db(container_id):
            logger.error(f"Container {container_id} not found in database")
            raise ContainerNotFoundException(f"Container {container_id} not found in the database")
        
        container = self.docker_helper.get_container_by_id(container_id)
        if not container:
            logger.error(f"Container {container_id} not found in Docker")
            raise ContainerNotFoundException(f"Container {container_id} not found in Docker")

        try:
            container.start()
            logger.info(f"Container {container_id} started successfully")
        except Exception as e:
            logger.error(f"Failed to start container {container_id}: {str(e)}")
            raise DockerAPIException(f"Error starting container {container_id}: {str(e)}")


    async def stop_container(self, container_id: str) -> None:
        """
        Stops a container by its ID.

        Args:
            container_id (str): The ID of the container to stop.

        Raises:
            ContainerNotFoundException: If the container is not found in the database or Docker.
            DockerAPIException: If an error occurs while stopping the container.
        """
        # Проверка, есть ли контейнер в базе данных
        if not await self.is_container_in_db(container_id):
            logger.error(f"Container {container_id} not found in database")
            raise ContainerNotFoundException(f"Container {container_id} not found in the database")

        # Проверка, есть ли контейнер в Docker
        container = self.docker_helper.get_container_by_id(container_id)
        if not container:
            logger.error(f"Container {container_id} not found in Docker")
            raise ContainerNotFoundException(f"Container {container_id} not found in Docker")

        # Попытка остановить контейнер
        try:
            container.stop()
            logger.info(f"Container {container_id} stopped successfully")
        except Exception as e:
            logger.error(f"Failed to stop container {container_id}: {str(e)}")
            raise DockerAPIException(f"Error stopping container {container_id}: {str(e)}")


    async def restart_container(self, container_id: str) -> None:
        """
        Restarts a container by its ID.

        Args:
            container_id (str): The ID of the container to restart.

        Raises:
            Exception: If the container is not found in the database.
            ContainerNotFoundException: If the container is not found in Docker.
        """
        if not await self.is_container_in_db(container_id):
            raise Exception(f"Container {container_id} not found in database")
        container = self.docker_helper.get_container_by_id(container_id)
        if not container:
            raise ContainerNotFoundException(f"Container {container_id} not found")
        container.restart()

    async def get_container_info(self, container_id: str) -> Optional[Container]:
        """
        Retrieves information about a container by its ID.

        Args:
            container_id (str): The ID of the container to retrieve information for.

        Returns:
            Optional[Container]: The container entity if found.

        Raises:
            ContainerNotFoundException: If the container is not found in the database or Docker.
        """
        is_in_db = await self.is_container_in_db(container_id)
        if not is_in_db:
            raise ContainerNotFoundException(f"Container {container_id} not found in the database")

        container = self.docker_helper.get_container_by_id(container_id)
        if not container:
            raise ContainerNotFoundException(f"Container {container_id} not found in Docker")

        container_info = Container(
            id=container.id,
            name=container.name,
            status=container.status,
            image=container.image.tags[0] if container.image.tags else "No tag available"
        )
        logger.debug(f"Container info retrieved: {container_info}")
        return container_info

    async def delete_container(self, container_id: str, force: bool = False) -> None:
        """
        Deletes a container by its ID.

        Args:
            container_id (str): The ID of the container to delete.
            force (bool): Whether to force delete the container.

        Raises:
            ContainerNotFoundException: If the container is not found in the database or Docker.
            DockerAPIException: If an error occurs during stopping or removing the container.
        """
        if not await self.is_container_in_db(container_id):
            raise ContainerNotFoundException(f"Container {container_id} not found in the database")

        container = self.docker_helper.get_container_by_id(container_id)
        if not container:
            raise ContainerNotFoundException(f"Container {container_id} not found in Docker")

        if container.status == 'running':
            try:
                container.stop()
                logger.info(f"Container {container_id} stopped successfully before deletion")
            except Exception as e:
                logger.error(f"Failed to stop container {container_id}: {str(e)}")
                raise DockerAPIException(f"Error stopping container {container_id}: {str(e)}")

        try:
            container.remove(force=force)
            logger.info(f"Container {container_id} removed successfully")
        except Exception as e:
            logger.error(f"Failed to remove container {container_id}: {str(e)}")
            raise DockerAPIException(f"Error removing container {container_id}: {str(e)}")

        await self.delete_container_from_db(container_id)
        logger.info(f"Container {container_id} deleted from the database")

    async def clone_and_run_container(self, github_url: str, dockerfile_dir: str) -> None:
        """
        Clones a Git repository, builds a Docker image, and runs a container.

        Args:
            github_url (str): The URL of the GitHub repository to clone.
            dockerfile_dir (str): The directory containing the Dockerfile.

        Raises:
            DockerAPIException: If an error occurs during the process.
        """
        repo_dir = f"./repos/{os.path.basename(github_url.rstrip('/').replace('.git', ''))}"
        try:
            self.git_helper.ensure_directory_exists('./repos')
            self.git_helper.clone_or_pull_repo(github_url, repo_dir)
            image_tag = self.docker_helper.build_container(repo_dir, dockerfile_dir)
            container = self.docker_helper.run_container(image_tag)

            new_container = Container(
                id=container.id,
                name=container.name,
                status=container.status,
                image=image_tag
            )
            await self.save_container_to_db(new_container)
            logger.info(f"Container {container.id} saved to DB")
        except Exception as e:
            logger.error(f"Error in clone and run: {str(e)}")
            raise DockerAPIException(str(e))

    async def get_container_stats(self, container_id: str) -> Optional[dict]:
        """
        Retrieves statistics for a container by its ID.

        Args:
            container_id (str): The ID of the container.

        Returns:
            Optional[dict]: A dictionary containing CPU usage, memory usage, and network I/O statistics.

        Raises:
            DockerAPIException: If an error occurs during retrieving statistics.
        """
        try:
            container = self.docker_helper.get_container_by_id(container_id)
            if not container:
                raise ContainerNotFoundException(f"Container with ID {container_id} not found")

            stats = container.stats(stream=False)

            cpu_stats = stats.get("cpu_stats", {})
            memory_stats = stats.get("memory_stats", {})
            networks = stats.get("networks", {})

            cpu_usage = cpu_stats.get("cpu_usage", {}).get("total_usage", 0)
            system_cpu_usage = cpu_stats.get("system_cpu_usage", 0)
            cpu_percentage = (
                (cpu_usage / system_cpu_usage) * 100 if system_cpu_usage > 0 else "No data available"
            )

            memory_usage = memory_stats.get("usage", 0)
            memory_limit = memory_stats.get("limit", 0)

            def format_memory(bytes_value):
                for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                    if bytes_value < 1024.0:
                        return f"{bytes_value:.2f} {unit}"
                    bytes_value /= 1024.0

            memory_usage_formatted = format_memory(memory_usage)
            memory_limit_formatted = format_memory(memory_limit)

            def format_bytes(bytes_value):
                for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                    if bytes_value < 1024.0:
                        return f"{bytes_value:.2f} {unit}"
                    bytes_value /= 1024.0

            network_io = {
                "received": {
                    "bytes": format_bytes(sum(interface.get("rx_bytes", 0) for interface in networks.values())),
                    "packets": sum(interface.get("rx_packets", 0) for interface in networks.values())
                },
                "transmitted": {
                    "bytes": format_bytes(sum(interface.get("tx_bytes", 0) for interface in networks.values())),
                    "packets": sum(interface.get("tx_packets", 0) for interface in networks.values())
                }
            }

            return {
                "cpu_usage_percent": round(cpu_percentage, 2),
                "memory_usage": memory_usage_formatted,
                "memory_limit": memory_limit_formatted,
                "network_io": network_io
            }

        except KeyError as e:
            logger.error(f"Missing key in stats for container {container_id}: {str(e)}")
            raise DockerAPIException(f"Missing key in Docker stats: {str(e)}")
        except Exception as e:
            logger.error(f"Error retrieving stats for container {container_id}: {str(e)}")
            raise DockerAPIException(str(e))

    async def save_container_to_db(self, container: Container):
        """
        Saves a container entity to the database.

        Args:
            container (Container): The container entity to save.
        """
        async with self.db_pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO containers (id, name, image)
                VALUES ($1, $2, $3)
                """,
                container.id, container.name, container.image
            )

    async def is_container_in_db(self, container_id: str) -> bool:
        """
        Checks if a container exists in the database.

        Args:
            container_id (str): The ID of the container to check.

        Returns:
            bool: True if the container exists in the database, False otherwise.
        """
        async with self.db_pool.acquire() as connection:
            row = await connection.fetchrow(
                "SELECT id FROM containers WHERE id = $1", container_id
            )
            return row is not None

    async def delete_container_from_db(self, container_id: str):
        """
        Deletes a container entry from the database.

        Args:
            container_id (str): The ID of the container to delete.
        """
        async with self.db_pool.acquire() as connection:
            await connection.execute(
                "DELETE FROM containers WHERE id = $1", container_id
            )
