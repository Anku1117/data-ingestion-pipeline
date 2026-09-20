from __future__ import annotations

from libraries.configuration.settings import get_settings
from libraries.logging.logging import get_logger
from libraries.search.base import SearchBackend

logger = get_logger(__name__)

_search: SearchBackend | None = None


def get_search() -> SearchBackend:
    global _search
    if _search is not None:
        return _search

    settings = get_settings()
    backend = getattr(settings, "search_backend", "memory")

    if backend == "elasticsearch":
        try:
            from libraries.search.elasticsearch_search import ElasticsearchSearchBackend

            _search = ElasticsearchSearchBackend(es_url=settings.elasticsearch_url)
            logger.info("Using ElasticsearchSearchBackend")
        except ImportError:
            logger.warning("elasticsearch package not installed, falling back to memory")
            from libraries.search.memory_search import MemorySearchBackend

            _search = MemorySearchBackend()
    else:
        from libraries.search.memory_search import MemorySearchBackend

        _search = MemorySearchBackend()
        logger.info("Using MemorySearchBackend (development mode)")

    return _search


def reset_search() -> None:
    global _search
    _search = None
