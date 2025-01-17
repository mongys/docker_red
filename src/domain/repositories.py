from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.entities import User, Container


class UserRepository(ABC):
    @abstractmethod
    async def get_user_by_username(self, username: str) -> Optional[User]:
        pass

    @abstractmethod
    async def create_user(self, user: User) -> None:
        pass


class ContainerRepository(ABC):
    @abstractmethod
    async def list_containers(self) -> List[Container]:
        pass

    @abstractmethod
    async def start_container(self, container_id: str) -> None:
        pass

    @abstractmethod
    async def stop_container(self, container_id: str) -> None:
        pass

    @abstractmethod
    async def restart_container(self, container_id: str) -> None:
        pass

    @abstractmethod
    async def get_container_info(self, container_id: str) -> Optional[Container]:
        pass

    @abstractmethod
    async def delete_container(self, container_id: str, force: bool = False) -> None:
        pass

    @abstractmethod
    async def clone_and_run_container(
        self, github_url: str, dockerfile_dir: str
    ) -> None:
        pass

    @abstractmethod
    async def get_container_info(self, container_id: str) -> Optional[Container]:
        """Fetch detailed information about a specific container."""
        pass
