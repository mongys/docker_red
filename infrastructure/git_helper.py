import git
import os
import logging
from domain.exceptions import DockerAPIException

logger = logging.getLogger(__name__)

class GitHelper:
    """
    Вспомогательный класс для работы с Git репозиториями, включающий методы для клонирования
    или обновления репозитория и создания необходимых директорий.
    """

    @staticmethod
    def clone_or_pull_repo(github_url: str, repo_dir: str):
        """
        Клонирует репозиторий из GitHub или обновляет его, если он уже существует.

        Если директория `repo_dir` существует, выполняется команда `git pull` для обновления репозитория.
        В противном случае репозиторий клонируется с указанного URL.

        Args:
            github_url (str): URL GitHub репозитория для клонирования.
            repo_dir (str): Локальная директория для клонирования или обновления репозитория.

        Raises:
            DockerAPIException: Если возникает ошибка при клонировании или обновлении репозитория.
        """
        try:
            if os.path.exists(repo_dir):
                repo = git.Repo(repo_dir)
                repo.remotes.origin.pull()
                logger.info(f"Repo at {repo_dir} updated successfully.")
            else:
                git.Repo.clone_from(github_url, repo_dir)
                logger.info(f"Repo at {repo_dir} cloned successfully.")
        except git.exc.GitError as e:
            logger.error(f"Git error during cloning or pulling repo: {str(e)}")
            raise DockerAPIException(str(e))

    @staticmethod
    def ensure_directory_exists(path: str):
        """
        Создает директорию, если она не существует.

        Args:
            path (str): Путь к создаваемой директории.

        Raises:
            OSError: Если возникает ошибка при создании директории.
        """
        try:
            os.makedirs(path, exist_ok=True)
            logger.info(f"Directory {path} created successfully.")
        except OSError as e:
            logger.error(f"Error creating directory {path}: {str(e)}")
            raise
