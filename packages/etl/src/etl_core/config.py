from pydantic_settings import BaseSettings, SettingsConfigDict


class CoreSettings(BaseSettings):
    model_config = SettingsConfigDict(env_ignore_empty=True, extra="ignore")

    DB_QUERY_BIND_PARAMETERS_LIMIT: int = 32767
    MAX_DB_POOL_SIZE: int = 20
    IS_DEBUG: bool = False

    TARGET_DB_HOST: str = "localhost"
    TARGET_DB_USER: str = "postgres"
    TARGET_DB_PASSWORD: str = "postgres"
    TARGET_DB_PORT: int = 5432
    TARGET_DB_DEFAULT_DATABASE: str = "postgres"


core_settings = CoreSettings()
