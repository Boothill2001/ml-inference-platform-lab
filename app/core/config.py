from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ml-inference-platform-lab"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 2
    model_registry_path: str = "models/model_registry.json"
    canary_percentage: int = 10
    log_level: str = "INFO"
    log_format: str = "json"
    metrics_enabled: bool = True
    drift_threshold: float = 0.3

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()

