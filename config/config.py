from dynaconf import Dynaconf

class AppSettings:
    def __init__(self):
        self._settings = Dynaconf(
            envvar_prefix="REDOS",
            settings_files=["settings.toml"],
        )

    @property
    def secret_key(self):
        return self._settings.SECRET_KEY

    @property
    def algorithm(self):
        return self._settings.ALGORITHM

    @property
    def access_token_expire_minutes(self):
        return self._settings.ACCESS_TOKEN_EXPIRE_MINUTES

    # Настройки базы данных
    @property
    def db_host(self):
        return self._settings.DB_HOST

    @property
    def db_port(self):
        return self._settings.DB_PORT

    @property
    def db_name(self):
        return self._settings.DB_NAME

    @property
    def db_user(self):
        return self._settings.DB_USER

    @property
    def db_password(self):
        return self._settings.DB_PASSWORD

    # Настройки Docker
    @property
    def docker_api_version(self):
        return self._settings.DOCKER_API_VERSION

# Создаем единственный экземпляр настроек для всего приложения
settings = AppSettings()
