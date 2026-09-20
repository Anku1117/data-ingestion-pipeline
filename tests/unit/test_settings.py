from __future__ import annotations

from libraries.configuration.settings import Settings


class TestSettings:
    def test_default_values(self) -> None:
        settings = Settings(
            _env_file=None,
        )
        assert settings.env == "development"
        assert settings.debug is False
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8000
        assert settings.postgres_host == "localhost"
        assert settings.postgres_port == 5432
        assert settings.postgres_db == "dip"

    def test_postgres_dsn(self) -> None:
        settings = Settings(_env_file=None)
        dsn = settings.postgres_dsn
        assert dsn.startswith("postgresql://")
        assert "dip" in dsn
        assert "5432" in dsn

    def test_elasticsearch_url(self) -> None:
        settings = Settings(_env_file=None)
        url = settings.elasticsearch_url
        assert url == "http://localhost:9200"

    def test_redis_url(self) -> None:
        settings = Settings(_env_file=None)
        url = settings.redis_url
        assert url == "redis://localhost:6379/0"

    def test_is_production(self) -> None:
        settings = Settings(_env_file=None, env="production")
        assert settings.is_production is True

        settings = Settings(_env_file=None, env="development")
        assert settings.is_production is False
