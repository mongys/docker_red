from src.domain.repositories import ContainerRepository


class ContainerActionService:
    def __init__(self, container_repo: ContainerRepository):
        self.container_repo = container_repo

    async def start_container(self, container_id: str):
        await self.container_repo.start_container(container_id)

    async def stop_container(self, container_id: str):
        await self.container_repo.stop_container(container_id)

    async def restart_container(self, container_id: str):
        await self.container_repo.restart_container(container_id)

    async def delete_container(self, container_id: str, force: bool = False):
        await self.container_repo.delete_container(container_id, force)

    async def clone_and_run_container(self, github_url: str, dockerfile_dir: str):
        await self.container_repo.clone_and_run_container(github_url, dockerfile_dir)
