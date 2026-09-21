from __future__ import annotations

import asyncio

from libraries.observability.metrics import MetricsCollector, get_metrics, timed


class TestMetricsCollector:
    def test_increment(self) -> None:
        collector = MetricsCollector()
        collector.increment("test_counter")
        collector.increment("test_counter")
        assert collector.get_counter("test_counter") == 2

    def test_record_time(self) -> None:
        collector = MetricsCollector()
        collector.record_time("test_timer", 10.0)
        collector.record_time("test_timer", 20.0)
        stats = collector.get_timer_stats("test_timer")
        assert stats["count"] == 2
        assert stats["avg_ms"] == 15.0
        assert stats["min_ms"] == 10.0
        assert stats["max_ms"] == 20.0

    def test_empty_timer_stats(self) -> None:
        collector = MetricsCollector()
        stats = collector.get_timer_stats("nonexistent")
        assert stats["count"] == 0
        assert stats["avg_ms"] == 0.0

    def test_reset(self) -> None:
        collector = MetricsCollector()
        collector.increment("counter")
        collector.record_time("timer", 5.0)
        collector.reset()
        assert collector.get_counter("counter") == 0
        assert collector.get_timer_stats("timer")["count"] == 0


class TestTimedDecorator:
    def test_records_execution_time_sync(self) -> None:
        collector = get_metrics()
        collector.reset()

        @timed("test_func_sync")
        def sample_func() -> str:
            return "done"

        result = sample_func()
        assert result == "done"
        stats = collector.get_timer_stats("test_func_sync")
        assert stats["count"] == 1
        assert stats["avg_ms"] >= 0

    def test_records_execution_time_async(self) -> None:
        collector = get_metrics()
        collector.reset()

        @timed("test_func_async")
        async def sample_func() -> str:
            return "async_done"

        result = asyncio.get_event_loop().run_until_complete(sample_func())
        assert result == "async_done"
        stats = collector.get_timer_stats("test_func_async")
        assert stats["count"] == 1
        assert stats["avg_ms"] >= 0

    def test_async_timed_decorator_preserves_exception(self) -> None:
        collector = get_metrics()
        collector.reset()

        @timed("test_func_exc")
        async def failing_func() -> None:
            raise ValueError("test error")

        try:
            asyncio.get_event_loop().run_until_complete(failing_func())
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert str(e) == "test error"

        stats = collector.get_timer_stats("test_func_exc")
        assert stats["count"] == 1
