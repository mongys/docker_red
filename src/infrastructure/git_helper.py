import git
import os
import logging
from src.domain.exceptions import DockerAPIException

logger = logging.getLogger(__name__)

class GitHelper:

    @staticmethod
    def clone_or_pull_repo(github_url: str, repo_dir: str):
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
        try:
            os.makedirs(path, exist_ok=True)
            logger.info(f"Directory {path} created successfully.")
        except OSError as e:
            logger.error(f"Error creating directory {path}: {str(e)}")
            raise
