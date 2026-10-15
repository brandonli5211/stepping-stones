"""App settings, read from environment variables or backend/.env.

Anything that changes between laptops (database password, ports) lives here,
never hard-coded in the rest of the code.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://stepping:stepping@localhost:5432/stepping_stones"
    frontend_origin: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
