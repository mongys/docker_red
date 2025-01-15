from dynaconf import Dynaconf


class AppSettings:
    def __init__(self):
        self._settings = Dynaconf(
            envvar_prefix="REDOS",
            settings_files=["config\settings.toml"],
        )

    def __getitem__(self, key: str):
        """
        Позволяет доступ к настройкам через квадратные скобки.
        Args:
            key (str): Имя настройки.
        Returns:
            Any: Значение настройки.
        Raises:
            KeyError: Если настройка не найдена.
        """
        if key in self._settings:
            return self._settings[key]
        raise KeyError(f"Setting '{key}' not found.")

    @property
    def secret_key(self) -> str:
        return self._settings.security.SECRET_KEY

    @property
    def algorithm(self) -> str:
        return self._settings.security.ALGORITHM

    @property
    def access_token_expire_minutes(self) -> int:
        return self._settings.security.ACCESS_TOKEN_EXPIRE_MINUTES

    @property
    def refresh_token_expire_days(self) -> int:
        return self._settings.security.REFRESH_TOKEN_EXPIRE_DAYS

    @property
    def database_dsn(self) -> str:
        """
        Генерирует строку подключения к базе данных (DSN).
        Returns:
            str: DSN строки для базы данных.
        """
        db = self._settings.database
        return f"{db.DRIVER}://{db.USER}:{db.PASSWORD}@{db.HOST}:{db.PORT}/{db.NAME}"

    @property
    def docker_api_version(self) -> str:
        return self._settings.docker.API_VERSION


# Экземпляр настроек
settings = AppSettings()
