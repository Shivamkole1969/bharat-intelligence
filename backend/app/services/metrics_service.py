"""
Bharat Market Intelligence Agent — Metrics & Monitoring Service

Prometheus-compatible metrics collection for:
- API request latency and counts
- LLM usage (tokens, cost, latency per provider)
- Ingestion pipeline stats
- Cache hit/miss rates
- System health indicators

Exposes /metrics endpoint in Prometheus text format.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Thread-safe in-memory metrics collector.

    In production, replace with prometheus_client library.
    This implementation provides the same interface without the dependency.
    """

    def __init__(self):
        self._lock = Lock()
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._start_time = time.time()

    def inc_counter(self, name: str, value: float = 1.0, labels: dict | None = None):
        """Increment a counter metric."""
        key = self._make_key(name, labels)
        with self._lock:
            self._counters[key] += value

    def set_gauge(self, name: str, value: float, labels: dict | None = None):
        """Set a gauge metric to a specific value."""
        key = self._make_key(name, labels)
        with self._lock:
            self._gauges[key] = value

    def observe_histogram(self, name: str, value: float, labels: dict | None = None):
        """Record a value in a histogram."""
        key = self._make_key(name, labels)
        with self._lock:
            self._histograms[key].append(value)
            # Keep only last 1000 observations to prevent memory leak
            if len(self._histograms[key]) > 1000:
                self._histograms[key] = self._histograms[key][-500:]

    def get_all(self) -> dict[str, Any]:
        """Get all metrics as a dictionary."""
        with self._lock:
            result = {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {},
                "uptime_seconds": round(time.time() - self._start_time, 1),
            }

            for key, values in self._histograms.items():
                if values:
                    sorted_vals = sorted(values)
                    count = len(sorted_vals)
                    result["histograms"][key] = {
                        "count": count,
                        "sum": round(sum(sorted_vals), 3),
                        "avg": round(sum(sorted_vals) / count, 3),
                        "min": round(sorted_vals[0], 3),
                        "max": round(sorted_vals[-1], 3),
                        "p50": round(sorted_vals[count // 2], 3),
                        "p95": round(sorted_vals[int(count * 0.95)], 3) if count >= 20 else None,
                        "p99": round(sorted_vals[int(count * 0.99)], 3) if count >= 100 else None,
                    }

            return result

    def to_prometheus(self) -> str:
        """Export metrics in Prometheus text exposition format."""
        lines = []
        lines.append(f"# Bharat Market Intelligence Agent Metrics")
        lines.append(f"# Generated at {datetime.now(timezone.utc).isoformat()}")
        lines.append("")

        with self._lock:
            # Uptime
            lines.append("# HELP bharat_uptime_seconds Time since server start")
            lines.append("# TYPE bharat_uptime_seconds gauge")
            lines.append(f"bharat_uptime_seconds {time.time() - self._start_time:.1f}")
            lines.append("")

            # Counters
            for key, value in sorted(self._counters.items()):
                safe_key = key.replace(".", "_").replace("-", "_")
                lines.append(f"# TYPE {safe_key} counter")
                lines.append(f"{safe_key} {value}")

            lines.append("")

            # Gauges
            for key, value in sorted(self._gauges.items()):
                safe_key = key.replace(".", "_").replace("-", "_")
                lines.append(f"# TYPE {safe_key} gauge")
                lines.append(f"{safe_key} {value}")

            lines.append("")

            # Histograms (as summary)
            for key, values in sorted(self._histograms.items()):
                if not values:
                    continue
                safe_key = key.replace(".", "_").replace("-", "_")
                sorted_vals = sorted(values)
                count = len(sorted_vals)
                total = sum(sorted_vals)

                lines.append(f"# TYPE {safe_key} summary")
                lines.append(f'{safe_key}{{quantile="0.5"}} {sorted_vals[count // 2]:.3f}')
                if count >= 20:
                    lines.append(f'{safe_key}{{quantile="0.95"}} {sorted_vals[int(count * 0.95)]:.3f}')
                if count >= 100:
                    lines.append(f'{safe_key}{{quantile="0.99"}} {sorted_vals[int(count * 0.99)]:.3f}')
                lines.append(f"{safe_key}_sum {total:.3f}")
                lines.append(f"{safe_key}_count {count}")

        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _make_key(name: str, labels: dict | None = None) -> str:
        if not labels:
            return name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"


# Global singleton
metrics = MetricsCollector()


# ============================================================
# Pre-defined Metric Helpers
# ============================================================
def record_api_request(method: str, path: str, status: int, duration_ms: float):
    """Record an API request metric."""
    metrics.inc_counter("bharat_api_requests_total", labels={"method": method, "path": path, "status": str(status)})
    metrics.observe_histogram("bharat_api_latency_ms", duration_ms, labels={"path": path})


def record_llm_call(provider: str, model: str, input_tokens: int, output_tokens: int, latency_ms: float, success: bool):
    """Record an LLM API call."""
    status = "success" if success else "error"
    metrics.inc_counter("bharat_llm_calls_total", labels={"provider": provider, "status": status})
    metrics.inc_counter("bharat_llm_input_tokens_total", value=input_tokens, labels={"provider": provider})
    metrics.inc_counter("bharat_llm_output_tokens_total", value=output_tokens, labels={"provider": provider})
    metrics.observe_histogram("bharat_llm_latency_ms", latency_ms, labels={"provider": provider, "model": model})


def record_ingestion(source: str, documents: int, duration_s: float):
    """Record an ingestion pipeline run."""
    metrics.inc_counter("bharat_ingestion_runs_total", labels={"source": source})
    metrics.inc_counter("bharat_ingestion_documents_total", value=documents, labels={"source": source})
    metrics.observe_histogram("bharat_ingestion_duration_seconds", duration_s, labels={"source": source})


def record_cache_hit(cache_type: str, hit: bool):
    """Record a cache hit or miss."""
    result = "hit" if hit else "miss"
    metrics.inc_counter("bharat_cache_total", labels={"type": cache_type, "result": result})


def record_embedding_batch(count: int, duration_ms: float):
    """Record an embedding batch operation."""
    metrics.inc_counter("bharat_embeddings_total", value=count)
    metrics.observe_histogram("bharat_embedding_batch_ms", duration_ms)
