import logging
import os
from typing import Optional, List
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import asyncio
from src.domain.repositories import ContainerRepository
from src.domain.entities import Container
from src.domain.exceptions import ContainerNotFoundException, DockerAPIException
from src.infrastructure.docker_helper import DockerHelper
from src.infrastructure.git_helper import GitHelper

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
        self.scheduler = BackgroundScheduler()
        self._scheduler_initialized=False
    def _initialize_scheduler(self):
        """
        Инициализация APScheduler для автономного выполнения задач.
        """
        if not self._scheduler_initialized:  # Проверяем, был ли уже запущен планировщик
            try:
                self.scheduler.add_job(
                    lambda: asyncio.run(self.monitor_resources()),
                    trigger=IntervalTrigger(minutes=1),
                    id="monitor_resources",
                    name="Мониторинг ресурсов контейнеров каждую минуту",
                    replace_existing=True,
                )
                self.scheduler.add_job(
                    lambda: asyncio.run(self._restart_all_containers()),
                    trigger=IntervalTrigger(minutes=10),
                    id="restart_containers",
                    name="Перезапуск всех контейнеров каждые 10 минут",
                    replace_existing=True,
                )
                self.scheduler.add_job(
                    lambda: asyncio.run(self._log_container_status()),
                    trigger=CronTrigger(hour=0, minute=1),
                    id="log_container_status",
                    name="Логирование состояния контейнеров каждый день в 00:01",
                    replace_existing=True,
                )
                self.scheduler.start()
                self._scheduler_initialized = True
                logger.info("APScheduler инициализирован и запущен.")
            except Exception as e:
                logger.error(f"Ошибка при инициализации APScheduler: {e}")
        else:
            logger.info("APScheduler уже инициализирован.")

    async def monitor_resources(self):
        """
        Мониторинг потребления ресурсов всеми контейнерами.
        """
        try:
            containers = await self.list_containers()
            logger.info("Запуск мониторинга ресурсов контейнеров...")

            for container in containers:
                stats = await self.get_container_stats(container.name)
                if stats:
                    cpu_percentage = (
                        (stats["cpu_usage"] / stats["system_cpu_usage"]) * 100
                        if stats["system_cpu_usage"] > 0 else 0
                    )
                    memory_percentage = (
                        (stats["memory_usage"] / stats["memory_limit"]) * 100
                        if stats["memory_limit"] > 0 else 0
                    )
                    logger.info(
                        f"Контейнер: {container.name} | CPU: {cpu_percentage:.2f}% | "
                        f"Memory: {memory_percentage:.2f}% | Network I/O: {stats['network_io']}"
                    )
                else:
                    logger.warning(f"Не удалось получить статистику для контейнера {container.name}")

            logger.info("Мониторинг ресурсов завершен.")
        except Exception as e:
            logger.error(f"Ошибка при мониторинге ресурсов контейнеров: {e}")

    async def get_container_stats(self, container_name: str) -> Optional[dict]:
        """
        Получение статистики потребления ресурсов для указанного контейнера.
        """
        try:
            container = self.docker_helper.get_container_by_name(container_name)
            if not container:
                raise ContainerNotFoundException(f"Контейнер {container_name} не найден")

            stats = container.stats(stream=False)
            cpu_usage = stats["cpu_stats"]["cpu_usage"]["total_usage"]
            system_cpu_usage = stats["cpu_stats"]["system_cpu_usage"]
            memory_usage = stats["memory_stats"]["usage"]
            memory_limit = stats["memory_stats"]["limit"]

            return {
                "cpu_usage": cpu_usage,
                "system_cpu_usage": system_cpu_usage,
                "memory_usage": memory_usage,
                "memory_limit": memory_limit,
                "network_io": stats["networks"],
            }
        except Exception as e:
            logger.error(f"Ошибка при получении статистики для контейнера {container_name}: {str(e)}")
            return None

    async def _restart_all_containers(self):
        """
        Перезапуск всех контейнеров, которые находятся в статусе 'running'.
        """
        try:
            containers = await self.list_containers()
            for container in containers:
                if container.status == "running":
                    logger.info(f"Перезапуск контейнера: {container.name}")
                    await self.restart_container(container.name)
        except Exception as e:
            logger.error(f"Ошибка при перезапуске контейнеров: {str(e)}")

    async def _log_container_status(self):
        """
        Логирование состояния всех контейнеров.
        """
        try:
            containers = await self.list_containers()
            for container in containers:
                logger.info(
                    f"Контейнер {container.name} - Статус: {container.status}, Образ: {container.image}"
                )
        except Exception as e:
            logger.error(f"Ошибка при логировании статусов контейнеров: {str(e)}")

    def shutdown_scheduler(self):
        """
        Корректная остановка APScheduler.
        """
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("APScheduler остановлен.")
            else:
                logger.warning("Попытка остановить планировщик, который уже остановлен или не запущен.")
        except Exception as e:
            logger.error(f"Ошибка при остановке APScheduler: {e}")

    async def list_containers(self) -> List[Container]:
        """
        Список всех контейнеров.
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
        container = self.docker_helper.get_container_by_name(container_name)
        if not container:
            raise ContainerNotFoundException(f"Container {container_name} not found")
        container.start()

    async def stop_container(self, container_name: str) -> None:
        container = self.docker_helper.get_container_by_name(container_name)
        if not container:
            raise ContainerNotFoundException(f"Container {container_name} not found")
        container.stop()

    async def restart_container(self, container_name: str) -> None:
        container = self.docker_helper.get_container_by_name(container_name)
        if not container:
            raise ContainerNotFoundException(f"Container {container_name} not found")
        container.restart()

    async def get_container_info(self, container_name: str) -> Optional[Container]:
        container = self.docker_helper.get_container_by_name(container_name)
        if not container:
            raise ContainerNotFoundException(f"Container {container_name} не найден")
        return Container(
            id=container.id,
            name=container.name,
            status=container.status,
            image=container.image.tags[0] if container.image.tags else "No tag available"
        )

    async def delete_container(self, container_name: str, force: bool = False) -> None:
        container = self.docker_helper.get_container_by_name(container_name)
        if not container:
            raise ContainerNotFoundException(f"Container {container_name} не найден")
        container.remove(force=force)

    async def clone_and_run_container(self, github_url: str, dockerfile_dir: str) -> None:
        repo_dir = f"./repos/{os.path.basename(github_url.rstrip('/').replace('.git', ''))}"
        try:
            self.git_helper.ensure_directory_exists('./repos')
            self.git_helper.clone_or_pull_repo(github_url, repo_dir)
            image_tag = self.docker_helper.build_container(repo_dir, dockerfile_dir)
            self.docker_helper.run_container(image_tag)
        except Exception as e:
            logger.error(f"Error in clone and run: {str(e)}")
            raise DockerAPIException(str(e))
