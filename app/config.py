from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "HomeTypeMap API"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/hometypemap"
    admin_api_key: str = "dev-admin-key"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
