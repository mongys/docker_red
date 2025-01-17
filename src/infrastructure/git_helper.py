import git
import os
import logging
from src.domain.exceptions import DockerAPIException

logger = logging.getLogger(__name__)


class GitHelper:
    """
    A helper class for managing Git repositories.
    """

    @staticmethod
    def clone_or_pull_repo(github_url: str, repo_dir: str):
        """
        Clones a Git repository from the given GitHub URL if it does not exist locally.
        If the repository already exists, it pulls the latest changes.

        Args:
            github_url (str): The URL of the GitHub repository.
            repo_dir (str): The local directory where the repository will be cloned or updated.

        Raises:
            DockerAPIException: If a Git error occurs during cloning or pulling.
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
        Ensures that a directory exists at the given path. If it does not exist, creates it.

        Args:
            path (str): The path to the directory to be created or checked.

        Raises:
            OSError: If there is an error creating the directory.
        """
        try:
            os.makedirs(path, exist_ok=True)
            logger.info(f"Directory {path} created successfully.")
        except OSError as e:
            logger.error(f"Error creating directory {path}: {str(e)}")
            raise
