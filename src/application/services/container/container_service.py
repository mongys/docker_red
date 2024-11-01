from src.application.container_action_service import ContainerActionService
from src.application.container_info_service import ContainerInfoService
from src.domain.repositories import ContainerRepository

class ContainerService:
    def __init__(self, container_repo: ContainerRepository):
        self.action_service = ContainerActionService(container_repo)
        self.info_service = ContainerInfoService(container_repo)

    async def list_containers(self):
        return await self.info_service.list_containers()

    async def start_container(self, container_name: str):
        await self.action_service.start_container(container_name)

    async def stop_container(self, container_name: str):
        await self.action_service.stop_container(container_name)

    async def restart_container(self, container_name: str):
        await self.action_service.restart_container(container_name)

    async def delete_container(self, container_name: str, force: bool = False):
        await self.action_service.delete_container(container_name, force)

    async def get_container_info(self, container_name: str):
        return await self.info_service.get_container_info(container_name)

    async def clone_and_run_container(self, github_url: str, dockerfile_dir: str):
        await self.action_service.clone_and_run_container(github_url, dockerfile_dir)
