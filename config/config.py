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

    @property
    def db_driver(self):
        return self._settings.DB_DRIVER

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

    @property
    def database_dsn(self):
        """
        Генерация строки DSN для подключения к базе данных
        """
        return "{}://{}:{}@{}:{}/{}".format(
            self.db_driver,
            self.db_user,
            self.db_password,
            self.db_host,
            self.db_port,
            self.db_name
        )

    @property
    def docker_api_version(self):
        return self._settings.DOCKER_API_VERSION

settings = AppSettings()
