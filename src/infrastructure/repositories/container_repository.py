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

    def __init__(self, db_pool):
        self.docker_helper = DockerHelper()
        self.git_helper = GitHelper()
        self.db_pool = db_pool

    async def list_containers(self) -> List[Container]:
        try:
            containers = self.docker_helper.list_containers()
            container_list = []
            for c in containers:
                is_in_db = await self.is_container_in_db(c.id)
                if not is_in_db:
                    continue  # Пропускаем контейнер, если его нет в БД

                name = getattr(c, 'name', "No name")
                status = getattr(c, 'status', "unknown")
                image = c.image.tags[0] if c.image.tags else "No tag available"
                
                container = Container(
                    id=c.id,
                    name=name,
                    status=status,
                    image=image,
                    is_in_db=is_in_db
                )
                logger.debug(f"Container created: {container}")
                container_list.append(container)
            return container_list
        except DockerAPIException as e:
            logger.error(f"Docker API error: {str(e)}")
            raise DockerAPIException(str(e))


    async def start_container(self, container_id: str) -> None:
        if not await self.is_container_in_db(container_id):
            raise Exception(f"Container {container_id} not found in database")
        container = self.docker_helper.get_container_by_id(container_id)
        if not container:
            raise ContainerNotFoundException(f"Container {container_id} not found")
        container.start()

    
    async def stop_container(self, container_id: str) -> None:
        if not await self.is_container_in_db(container_id):
            raise Exception(f"Container {container_id} not found in database")
        container = self.docker_helper.get_container_by_id(container_id)
        if not container:
            raise ContainerNotFoundException(f"Container {container_id} not found")
        container.stop()


    async def restart_container(self, container_id: str) -> None:
        if not await self.is_container_in_db(container_id):
            raise Exception(f"Container {container_id} not found in database")
        container = self.docker_helper.get_container_by_id(container_id)
        if not container:
            raise ContainerNotFoundException(f"Container {container_id} not found")
        container.restart()



    async def get_container_info(self, container_id: str) -> Optional[Container]:
        container = self.docker_helper.get_container_by_id(container_id)
        if not container:
            raise ContainerNotFoundException(f"Container {container_id} не найден")
        is_in_db = await self.is_container_in_db(container_id)
        container_info = Container(
            id=container.id,
            name=container.name,
            status=container.status,
            image=container.image.tags[0] if container.image.tags else "No tag available",
            is_in_db=is_in_db
        )
        logger.debug(f"Container info retrieved: {container_info}")
        return container_info

    async def delete_container(self, container_id: str, force: bool = False) -> None:
        if not await self.is_container_in_db(container_id):
            raise Exception(f"Container {container_id} not found in database")
        container = self.docker_helper.get_container_by_id(container_id)
        if not container:
            raise ContainerNotFoundException(f"Container {container_id} not found")
        container.remove(force=force)
        await self.delete_container_from_db(container_id)

    async def clone_and_run_container(self, github_url: str, dockerfile_dir: str) -> None:
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
                image=image_tag,
                is_in_db=True 
            )
            await self.save_container_to_db(new_container)
            logger.info(f"Container {container.id} saved to DB")
        except Exception as e:
            logger.error(f"Error in clone and run: {str(e)}")
            raise DockerAPIException(str(e))

            
    async def get_container_stats(self, container_id: str) -> Optional[dict]:
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
        async with self.db_pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO containers (id, name, image)
                VALUES ($1, $2, $3)
                """,
                container.id, container.name, container.image
            )

    async def is_container_in_db(self, container_id: str) -> bool:
        async with self.db_pool.acquire() as connection:
            row = await connection.fetchrow(
                "SELECT id FROM containers WHERE id = $1", container_id
            )
            return row is not None

    async def delete_container_from_db(self, container_id: str):
        async with self.db_pool.acquire() as connection:
            await connection.execute(
                "DELETE FROM containers WHERE id = $1", container_id
            )
