from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="REDOS",
    settings_files=['settings.toml'],
)
