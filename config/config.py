from dynaconf import Dynaconf


class AppSettings:
    def __init__(self):
        self._settings = Dynaconf(
            envvar_prefix="REDOS",
            settings_files=["config\settings.toml"],
        )

    def __getitem__(self, key: str):
        """
        Allows access to settings using square brackets.

        Args:
            key (str): The name of the setting.

        Returns:
            Any: The value of the setting.

        Raises:
            KeyError: If the setting is not found.
        """
        if key in self._settings:
            return self._settings[key]
        raise KeyError(f"Setting '{key}' not found.")

    @property
    def secret_key(self) -> str:
        """
        Retrieves the secret key used for security purposes.

        Returns:
            str: The secret key.
        """
        return self._settings.security.SECRET_KEY

    @property
    def algorithm(self) -> str:
        """
        Retrieves the algorithm used for cryptographic operations.

        Returns:
            str: The algorithm.
        """
        return self._settings.security.ALGORITHM

    @property
    def access_token_expire_minutes(self) -> int:
        """
        Retrieves the expiration time for access tokens in minutes.

        Returns:
            int: The expiration time in minutes.
        """
        return self._settings.security.ACCESS_TOKEN_EXPIRE_MINUTES

    @property
    def refresh_token_expire_days(self) -> int:
        """
        Retrieves the expiration time for refresh tokens in days.

        Returns:
            int: The expiration time in days.
        """
        return self._settings.security.REFRESH_TOKEN_EXPIRE_DAYS

    @property
    def database_dsn(self) -> str:
        """
        Generates a Data Source Name (DSN) string for the database connection.

        Returns:
            str: The DSN string for the database.
        """
        db = self._settings.database
        return f"{db.DRIVER}://{db.USER}:{db.PASSWORD}@{db.HOST}:{db.PORT}/{db.NAME}"

    @property
    def docker_api_version(self) -> str:
        """
        Retrieves the Docker API version to be used.

        Returns:
            str: The Docker API version.
        """
        return self._settings.docker.API_VERSION


# Instance of settings
settings = AppSettings()
