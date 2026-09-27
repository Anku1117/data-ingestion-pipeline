from __future__ import annotations

from libraries.logging.logging import get_logger
from libraries.observability.metrics import get_metrics

logger = get_logger(__name__)


def generate_prometheus_metrics() -> str:
    """Generate Prometheus-compatible text format metrics."""
    metrics = get_metrics()
    lines: list[str] = []

    for name, value in metrics._counters.items():
        safe_name = name.replace(".", "_").replace("-", "_")
        lines.append(f"# HELP dip_{safe_name} Counter: {name}")
        lines.append(f"# TYPE dip_{safe_name} counter")
        lines.append(f"dip_{safe_name} {value}")

    for name in metrics._timers:
        stats = metrics.get_timer_stats(name)
        safe_name = name.replace(".", "_").replace("-", "_")
        lines.append(f"# HELP dip_{safe_name}_seconds Timer: {name}")
        lines.append(f"# TYPE dip_{safe_name}_seconds summary")
        lines.append(f'dip_{safe_name}_seconds{{quantile="count"}} {stats["count"]}')
        lines.append(f'dip_{safe_name}_seconds{{quantile="avg"}} {stats["avg_ms"] / 1000:.6f}')
        lines.append(f'dip_{safe_name}_seconds{{quantile="min"}} {stats["min_ms"] / 1000:.6f}')
        lines.append(f'dip_{safe_name}_seconds{{quantile="max"}} {stats["max_ms"] / 1000:.6f}')

    return "\n".join(lines) + "\n"
