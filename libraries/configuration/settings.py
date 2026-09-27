from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "DIP_", "env_file": ".env", "env_file_encoding": "utf-8"}

    env: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "dip"
    postgres_user: str = "dip"
    postgres_password: str = "dip_secret"

    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_events_topic: str = "dip-events"
    kafka_dlq_topic: str = "dip-dlq"
    kafka_consumer_group: str = "dip-processor"

    elasticsearch_host: str = "localhost"
    elasticsearch_port: int = 9200
    elasticsearch_scheme: str = "http"

    redis_host: str = "localhost"
    redis_port: int = 6379

    prometheus_port: int = 9090
    metrics_enabled: bool = True

    event_backend: str = "memory"
    search_backend: str = "memory"
    cache_backend: str = "memory"

    api_keys: str = ""
    cors_origins: str = "*"
    retention_days: int = 90

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def postgres_async_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def elasticsearch_url(self) -> str:
        return f"{self.elasticsearch_scheme}://{self.elasticsearch_host}:{self.elasticsearch_port}"

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    @property
    def is_production(self) -> bool:
        return self.env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
