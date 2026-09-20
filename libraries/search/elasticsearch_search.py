from __future__ import annotations

from typing import Any

from libraries.logging.logging import get_logger
from libraries.schemas.common import EventEnvelope
from libraries.search.base import SearchBackend

logger = get_logger(__name__)

INDEX_NAME = "dip-events"


class ElasticsearchSearchBackend(SearchBackend):
    """Elasticsearch search backend for production use."""

    def __init__(self, es_url: str = "http://localhost:9200") -> None:
        self._es_url = es_url
        self._client = None

    async def start(self) -> None:
        try:
            from elasticsearch import AsyncElasticsearch

            self._client = AsyncElasticsearch([self._es_url])

            exists = await self._client.indices.exists(index=INDEX_NAME)
            if not exists:
                mapping = {
                    "mappings": {
                        "properties": {
                            "event_id": {"type": "keyword"},
                            "event_type": {"type": "keyword"},
                            "source": {"type": "keyword"},
                            "producer": {"type": "keyword"},
                            "severity": {"type": "keyword"},
                            "timestamp": {"type": "date"},
                            "tenant_id": {"type": "keyword"},
                            "agent_id": {"type": "keyword"},
                            "run_id": {"type": "keyword"},
                            "trace_id": {"type": "keyword"},
                            "payload": {"type": "object", "enabled": True},
                            "metadata": {"type": "object", "enabled": True},
                        }
                    }
                }
                await self._client.indices.create(index=INDEX_NAME, body=mapping)
                logger.info("Created Elasticsearch index %s", INDEX_NAME)

            logger.info("ElasticsearchSearchBackend connected url=%s", self._es_url)
        except ImportError:
            logger.warning("elasticsearch package not installed")
            raise
        except Exception as e:
            logger.error("Failed to connect to Elasticsearch: %s", str(e))
            raise

    async def stop(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None

    async def index_event(self, event: EventEnvelope) -> None:
        if not self._client:
            return
        doc = event.model_dump(mode="json")
        await self._client.index(index=INDEX_NAME, id=event.event_id, body=doc)

    async def index_events(self, events: list[EventEnvelope]) -> int:
        if not self._client:
            return 0
        for event in events:
            await self.index_event(event)
        return len(events)

    async def get_event(self, event_id: str) -> dict[str, Any] | None:
        if not self._client:
            return None
        try:
            result = await self._client.get(index=INDEX_NAME, id=event_id)
            return result["_source"]
        except Exception:
            return None

    async def search_events(
        self,
        query: str | None = None,
        event_type: str | None = None,
        source: str | None = None,
        severity: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        agent_id: str | None = None,
        run_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        if not self._client:
            return {"total": 0, "events": [], "limit": limit, "offset": offset}

        must = []
        if query:
            must.append({"multi_match": {"query": query, "fields": ["*"]}})
        if event_type:
            must.append({"term": {"event_type": event_type}})
        if source:
            must.append({"term": {"source": source}})
        if severity:
            must.append({"term": {"severity": severity}})
        if agent_id:
            must.append({"term": {"agent_id": agent_id}})
        if run_id:
            must.append({"term": {"run_id": run_id}})
        if start_time or end_time:
            time_range: dict[str, str] = {}
            if start_time:
                time_range["gte"] = start_time
            if end_time:
                time_range["lte"] = end_time
            must.append({"range": {"timestamp": time_range}})

        body: dict[str, Any] = {
            "query": {"bool": {"must": must}} if must else {"match_all": {}},
            "from": offset,
            "size": limit,
            "sort": [{"timestamp": {"order": "desc"}}],
        }

        result = await self._client.search(index=INDEX_NAME, body=body)
        hits = result.get("hits", {})
        total = hits.get("total", {}).get("value", 0)
        events = [hit["_source"] for hit in hits.get("hits", [])]

        return {
            "total": total,
            "events": events,
            "limit": limit,
            "offset": offset,
        }

    async def delete_event(self, event_id: str) -> bool:
        if not self._client:
            return False
        try:
            await self._client.delete(index=INDEX_NAME, id=event_id)
            return True
        except Exception:
            return False

    async def health_check(self) -> bool:
        if not self._client:
            return False
        try:
            return await self._client.ping()
        except Exception:
            return False
