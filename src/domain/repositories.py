from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.entities import User, Container


class UserRepository(ABC):
    """
    Абстрактный класс для репозитория пользователей.

    Определяет интерфейс для операций, связанных с пользователями,
    таких как поиск пользователя по имени и создание нового пользователя.
    """

    @abstractmethod
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Получение пользователя по имени.

        Args:
            username (str): Имя пользователя для поиска.

        Returns:
            Optional[User]: Объект пользователя, если он существует, иначе None.
        """
        pass

    @abstractmethod
    async def create_user(self, user: User) -> None:
        """
        Создание нового пользователя в системе.

        Args:
            user (User): Объект пользователя для создания.
        """
        pass


class ContainerRepository(ABC):
    """
    Абстрактный класс для репозитория Docker-контейнеров.

    Определяет интерфейс для операций с контейнерами, таких как
    запуск, остановка, перезапуск, удаление и клонирование контейнеров.
    """

    @abstractmethod
    async def list_containers(self) -> List[Container]:
        """
        Получение списка всех доступных контейнеров.

        Returns:
            List[Container]: Список всех контейнеров.
        """
        pass

    @abstractmethod
    async def start_container(self, container_name: str) -> None:
        """
        Запуск контейнера.

        Args:
            container_name (str): Имя контейнера для запуска.
        """
        pass

    @abstractmethod
    async def stop_container(self, container_name: str) -> None:
        """
        Остановка контейнера.

        Args:
            container_name (str): Имя контейнера для остановки.
        """
        pass

    @abstractmethod
    async def restart_container(self, container_name: str) -> None:
        """
        Перезапуск контейнера.

        Args:
            container_name (str): Имя контейнера для перезапуска.
        """
        pass

    @abstractmethod
    async def get_container_info(self, container_name: str) -> Optional[Container]:
        """
        Получение информации о контейнере.

        Args:
            container_name (str): Имя контейнера для получения информации.

        Returns:
            Optional[Container]: Объект контейнера, если он существует, иначе None.
        """
        pass

    @abstractmethod
    async def delete_container(self, container_name: str, force: bool = False) -> None:
        """
        Удаление контейнера.

        Args:
            container_name (str): Имя контейнера для удаления.
            force (bool): Принудительное удаление контейнера. По умолчанию False.
        """
        pass

    @abstractmethod
    async def clone_and_run_container(self, github_url: str, dockerfile_dir: str) -> None:
        """
        Клонирование и запуск контейнера из указанного репозитория.

        Args:
            github_url (str): URL-адрес репозитория GitHub.
            dockerfile_dir (str): Директория, содержащая Dockerfile.
        """
        pass
