from src.domain.repositories import ContainerRepository
from src.domain.entities import Container

class ContainerInfoService:
    def __init__(self, container_repo: ContainerRepository):
        self.container_repo = container_repo

    async def get_container_info(self, container_name: str) -> Container:
        return await self.container_repo.get_container_info(container_name)

    async def list_containers(self):
        return await self.container_repo.list_containers()
