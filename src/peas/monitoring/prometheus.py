"""
Prometheus metrics endpoint for PEAS

Provides a lightweight Prometheus metrics exporter with PEAS-specific metrics.
"""

from typing import Dict, List, Optional


class PrometheusMetrics:
    """Prometheus metrics exporter

    A simple, standalone metrics exporter that outputs metrics in Prometheus format.

    Example:
        >>> metrics = PrometheusMetrics()
        >>> metrics.increment("peas_parse_total")
        >>> metrics.gauge("peas_drift_score", 42.5)
        >>> metrics.histogram("peas_parse_duration_seconds", 0.123)
        >>> print(metrics.to_prometheus_format())
    """

    def __init__(self):
        """Initialize the Prometheus metrics exporter"""
        self._metrics: Dict[str, float] = {}
        self._counters: Dict[str, int] = {}
        self._histograms: Dict[str, List[float]] = {}
        self._histogram_buckets: Dict[str, Dict[str, int]] = {}

    def increment(self, name: str, value: int = 1) -> None:
        """Increment a counter metric

        Args:
            name: Metric name (will be prefixed with peas_ if not already)
            value: Value to increment by (default: 1)
        """
        prefixed_name = self._prefix_name(name)
        self._counters[prefixed_name] = self._counters.get(prefixed_name, 0) + value

    def gauge(self, name: str, value: float) -> None:
        """Set a gauge metric value

        Args:
            name: Metric name (will be prefixed with peas_ if not already)
            value: The gauge value
        """
        prefixed_name = self._prefix_name(name)
        self._metrics[prefixed_name] = value

    def histogram(self, name: str, value: float, buckets: Optional[List[float]] = None) -> None:
        """Record a histogram value

        Args:
            name: Metric name (will be prefixed with peas_ if not already)
            value: The value to record
            buckets: Optional custom bucket boundaries (default: standard Prometheus buckets)
        """
        prefixed_name = self._prefix_name(name)

        if prefixed_name not in self._histograms:
            self._histograms[prefixed_name] = []
            # Standard Prometheus histogram buckets
            self._histogram_buckets[prefixed_name] = {
                "0.005": 0,
                "0.01": 0,
                "0.025": 0,
                "0.05": 0,
                "0.1": 0,
                "0.25": 0,
                "0.5": 0,
                "1.0": 0,
                "2.5": 0,
                "5.0": 0,
                "10.0": 0,
                "+Inf": 0,
            }

        self._histograms[prefixed_name].append(value)

        # Update bucket counts (cumulative)
        if buckets is None:
            buckets = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]

        cumulative = 0
        for bucket_le in sorted(buckets):
            if value <= bucket_le:
                cumulative += 1
                self._histogram_buckets[prefixed_name][str(bucket_le)] += 1

        # Always increment +Inf bucket
        self._histogram_buckets[prefixed_name]["+Inf"] += 1

    def _prefix_name(self, name: str) -> str:
        """Add peas_ prefix if not present

        Args:
            name: The metric name

        Returns:
            str: Prefixed metric name
        """
        if not name.startswith("peas_"):
            return f"peas_{name}"
        return name

    def to_prometheus_format(self) -> str:
        """Export metrics in Prometheus text format

        Returns:
            str: Metrics in Prometheus exposition format
        """
        lines: List[str] = []

        # Counters
        for name, value in sorted(self._counters.items()):
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")

        if self._counters:
            lines.append("")

        # Gauges
        for name, value in sorted(self._metrics.items()):
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")

        if self._metrics:
            lines.append("")

        # Histograms
        for name, values in sorted(self._histograms.items()):
            lines.append(f"# TYPE {name} histogram")

            # Bucket values (cumulative)
            buckets = self._histogram_buckets.get(name, {})
            for le, count in sorted(
                buckets.items(), key=lambda x: float(x[0]) if x[0] != "+Inf" else float("inf")
            ):
                lines.append(f'{name}_bucket{{le="{le}"}} {count}')

            # Sum, count, avg
            lines.append(f"{name}_sum {sum(values)}")
            lines.append(f"{name}_count {len(values)}")

            avg = sum(values) / len(values) if values else 0
            lines.append(f"{name}_avg {avg}")

        return "\n".join(lines)


# Global metrics instance
_global_metrics: Optional[PrometheusMetrics] = None


def get_prometheus_metrics() -> PrometheusMetrics:
    """Get the global PrometheusMetrics instance

    Returns:
        PrometheusMetrics: The global metrics instance
    """
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = PrometheusMetrics()
    return _global_metrics


# Convenience functions for PEAS-specific metrics
def record_parse_duration(duration_seconds: float) -> None:
    """Record parsing duration

    Args:
        duration_seconds: Parse duration in seconds
    """
    get_prometheus_metrics().histogram("parse_duration_seconds", duration_seconds)


def increment_parse_total() -> None:
    """Increment the total parse counter"""
    get_prometheus_metrics().increment("parse_total")


def set_drift_score(score: float) -> None:
    """Set the current drift score

    Args:
        score: Drift score (0-100)
    """
    get_prometheus_metrics().gauge("drift_score", score)


def increment_features_verified() -> None:
    """Increment the verified features counter"""
    get_prometheus_metrics().increment("features_verified_total")


def increment_features_failed() -> None:
    """Increment the failed features counter"""
    get_prometheus_metrics().increment("features_failed_total")


def set_feature_count(count: int) -> None:
    """Set the current feature count

    Args:
        count: Number of features
    """
    get_prometheus_metrics().gauge("feature_count", count)
