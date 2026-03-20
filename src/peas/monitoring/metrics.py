"""
MetricsCollector - PEAS性能指标收集器

提供Prometheus格式的指标暴露。
"""
import time
import threading
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum

from ..types.verification import DriftLevel


class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


@dataclass
class HistogramBucket:
    """直方图桶"""
    le: float
    count: int = 0


class MetricsCollector:
    """PEAS性能指标收集器

    收集和暴露PEAS性能指标，支持Prometheus格式输出。

    指标:
    - parse_duration_seconds: 解析耗时分布 (histogram)
    - verify_total: 验证总数（按结果分）(counter)
    - drift_score: 偏离度分数 (gauge)
    - feature_count: feature points数量 (gauge)
    - contract_build_duration_seconds: 合约构建耗时 (histogram)
    """

    # 预定义的直方图桶 (秒)
    DEFAULT_BUCKETS = [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]

    def __init__(self):
        """初始化指标收集器"""
        # 解析耗时直方图
        self._parse_durations: list[float] = []
        self._parse_buckets: dict[float, int] = {b: 0 for b in self.DEFAULT_BUCKETS}

        # 合约构建耗时直方图
        self._contract_durations: list[float] = []
        self._contract_buckets: dict[float, int] = {b: 0 for b in self.DEFAULT_BUCKETS}

        # 验证计数器
        self._verify_counts: dict[str, int] = {
            "verified": 0,
            "failed": 0,
            "skipped": 0,
            "pending": 0,
        }

        # 偏离度 (最新值)
        self._drift_score: Optional[float] = None
        self._drift_level: Optional[str] = None

        # 功能点数量
        self._feature_count: int = 0

        # 线程安全锁
        self._lock = threading.Lock()

    def record_parse_time(self, duration_ms: float) -> None:
        """记录解析耗时

        Args:
            duration_ms: 解析耗时（毫秒）
        """
        duration_s = duration_ms / 1000.0

        with self._lock:
            self._parse_durations.append(duration_s)
            # 更新桶计数 - 找到第一个 >= duration 的桶并递增
            # Prometheus直方图是累计的：bucket{le="X"} 包含所有 <= X 的值
            sorted_buckets = sorted(self._parse_buckets.keys())
            for bucket_le in sorted_buckets:
                if duration_s <= bucket_le:
                    self._parse_buckets[bucket_le] += 1
                    break  # 只递增第一个满足条件的桶
            else:
                # 如果没有找到满足的桶，递增 +Inf 桶（最后一个）
                self._parse_buckets[sorted_buckets[-1]] += 1

    def record_contract_build_time(self, duration_ms: float) -> None:
        """记录合约构建耗时

        Args:
            duration_ms: 合约构建耗时（毫秒）
        """
        duration_s = duration_ms / 1000.0

        with self._lock:
            self._contract_durations.append(duration_s)
            # 更新桶计数 - 找到第一个 >= duration 的桶并递增
            sorted_buckets = sorted(self._contract_buckets.keys())
            for bucket_le in sorted_buckets:
                if duration_s <= bucket_le:
                    self._contract_buckets[bucket_le] += 1
                    break
            else:
                self._contract_buckets[sorted_buckets[-1]] += 1

    def record_verify_count(self, result: str) -> None:
        """记录验证次数

        Args:
            result: 验证结果 ("verified", "failed", "skipped", "pending")
        """
        with self._lock:
            if result in self._verify_counts:
                self._verify_counts[result] += 1
            else:
                self._verify_counts[result] = 1

    def record_drift_score(self, score: float, level: DriftLevel = None) -> None:
        """记录偏离度

        Args:
            score: 偏离分数 (0-100)
            level: 偏离级别
        """
        with self._lock:
            self._drift_score = score
            if level:
                self._drift_level = level.name.lower()

    def set_feature_count(self, count: int) -> None:
        """设置功能点数量

        Args:
            count: 功能点数量
        """
        with self._lock:
            self._feature_count = count

    def get_metrics(self) -> dict:
        """获取所有指标

        Returns:
            dict: 包含所有指标的字典
        """
        with self._lock:
            return {
                "parse_duration_seconds": self._get_histogram_stats(self._parse_durations),
                "contract_build_duration_seconds": self._get_histogram_stats(self._contract_durations),
                "verify_total": dict(self._verify_counts),
                "drift_score": {
                    "value": self._drift_score,
                    "level": self._drift_level,
                },
                "feature_count": self._feature_count,
            }

    def _get_histogram_stats(self, durations: list[float]) -> dict:
        """获取直方图统计信息

        Args:
            durations: 时长列表

        Returns:
            dict: 统计信息
        """
        if not durations:
            return {
                "count": 0,
                "sum": 0.0,
                "mean": 0.0,
                "min": 0.0,
                "max": 0.0,
                "buckets": {},
            }

        sorted_durations = sorted(durations)
        n = len(sorted_durations)

        # 计算分位数
        quantiles = {}
        for q in [0.5, 0.75, 0.9, 0.95, 0.99]:
            idx = int(n * q)
            if idx >= n:
                idx = n - 1
            quantiles[str(q)] = sorted_durations[idx]

        return {
            "count": n,
            "sum": sum(durations),
            "mean": sum(durations) / n,
            "min": sorted_durations[0],
            "max": sorted_durations[-1],
            "quantiles": quantiles,
        }

    def to_prometheus(self) -> str:
        """生成Prometheus格式的指标输出

        Returns:
            str: Prometheus格式的指标
        """
        lines = []
        lines.append("# HELP PEAS_parse_duration_seconds HTML parsing duration in seconds")
        lines.append("# TYPE PEAS_parse_duration_seconds histogram")

        # 直方图指标 - parse_duration
        with self._lock:
            parse_stats = self._get_histogram_stats(self._parse_durations)

            # 桶
            cumulative = 0
            sorted_buckets = sorted(self._parse_buckets.keys())
            for le in sorted_buckets:
                cumulative += self._parse_buckets[le]
                lines.append(f'PEAS_parse_duration_seconds_bucket{{le="{le}"}} {cumulative}')

            # +Inf bucket
            total_count = len(self._parse_durations)
            lines.append(f'PEAS_parse_duration_seconds_bucket{{le="+Inf"}} {total_count}')

            # sum, count, mean
            lines.append(f'PEAS_parse_duration_seconds_sum {parse_stats["sum"]:.6f}')
            lines.append(f'PEAS_parse_duration_seconds_count {parse_stats["count"]}')

            # 分位数
            if parse_stats.get("quantiles"):
                lines.append("# HELP PEAS_parse_duration_seconds quantile")
                lines.append("# TYPE PEAS_parse_duration_seconds gauge")
                for q, val in parse_stats["quantiles"].items():
                    lines.append(f'PEAS_parse_duration_seconds{{quantile="{q}"}} {val:.6f}')

        lines.append("")

        # 合约构建耗时
        lines.append("# HELP PEAS_contract_build_duration_seconds Contract build duration in seconds")
        lines.append("# TYPE PEAS_contract_build_duration_seconds histogram")

        with self._lock:
            contract_stats = self._get_histogram_stats(self._contract_durations)

            cumulative = 0
            sorted_buckets = sorted(self._contract_buckets.keys())
            for le in sorted_buckets:
                cumulative += self._contract_buckets[le]
                lines.append(f'PEAS_contract_build_duration_seconds_bucket{{le="{le}"}} {cumulative}')

            total_count = len(self._contract_durations)
            lines.append(f'PEAS_contract_build_duration_seconds_bucket{{le="+Inf"}} {total_count}')

            lines.append(f'PEAS_contract_build_duration_seconds_sum {contract_stats["sum"]:.6f}')
            lines.append(f'PEAS_contract_build_duration_seconds_count {contract_stats["count"]}')

        lines.append("")

        # 验证计数器
        lines.append("# HELP PEAS_verify_total Total verification counts by result")
        lines.append("# TYPE PEAS_verify_total counter")

        with self._lock:
            for result, count in self._verify_counts.items():
                lines.append(f'PEAS_verify_total{{result="{result}"}} {count}')

        lines.append("")

        # 偏离度
        lines.append("# HELP PEAS_drift_score Current drift score (0-100)")
        lines.append("# TYPE PEAS_drift_score gauge")

        with self._lock:
            if self._drift_score is not None:
                lines.append(f'PEAS_drift_score {self._drift_score:.2f}')
                if self._drift_level:
                    lines.append(f'PEAS_drift_score_level{{level="{self._drift_level}"}} 1')

        lines.append("")

        # 功能点数量
        lines.append("# HELP PEAS_feature_count Number of feature points")
        lines.append("# TYPE PEAS_feature_count gauge")

        with self._lock:
            lines.append(f"PEAS_feature_count {self._feature_count}")

        return "\n".join(lines)

    def reset(self) -> None:
        """重置所有指标"""
        with self._lock:
            self._parse_durations.clear()
            self._parse_buckets = {b: 0 for b in self.DEFAULT_BUCKETS}
            self._contract_durations.clear()
            self._contract_buckets = {b: 0 for b in self.DEFAULT_BUCKETS}
            self._verify_counts = {
                "verified": 0,
                "failed": 0,
                "skipped": 0,
                "pending": 0,
            }
            self._drift_score = None
            self._drift_level = None
            self._feature_count = 0


# 全局指标收集器实例
_global_collector: Optional[MetricsCollector] = None
_collector_lock = threading.Lock()


def get_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器实例

    Returns:
        MetricsCollector: 全局指标收集器
    """
    global _global_collector

    if _global_collector is None:
        with _collector_lock:
            if _global_collector is None:
                _global_collector = MetricsCollector()

    return _global_collector


def create_metrics_server(host: str = "0.0.0.0", port: int = 8080) -> "MetricsHTTPServer":
    """创建简单的HTTP服务器暴露metrics

    Args:
        host: 监听地址
        port: 监听端口

    Returns:
        MetricsHTTPServer: HTTP服务器实例
    """
    return MetricsHTTPServer(host, port)


class MetricsHTTPServer:
    """简单的HTTP服务器暴露metrics端点"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        """初始化HTTP服务器

        Args:
            host: 监听地址
            port: 监听端口
        """
        self.host = host
        self.port = port
        self._server = None
        self._collector = get_metrics_collector()

    def start(self, blocking: bool = True) -> None:
        """启动HTTP服务器

        Args:
            blocking: 是否阻塞运行
        """
        import http.server
        import socketserver

        collector = self._collector

        class MetricsHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/metrics":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; version=0.0.4")
                    self.end_headers()
                    self.wfile.write(collector.to_prometheus().encode())
                elif self.path == "/health":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(b"OK")
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, format, *args):
                # 抑制日志输出
                pass

        class ReusableTCPServer(socketserver.TCPServer):
            allow_reuse_address = True

        self._server = ReusableTCPServer((self.host, self.port), MetricsHandler)

        if blocking:
            print(f"Metrics server starting on {self.host}:{self.port}")
            print("Endpoints: /metrics (Prometheus), /health")
            try:
                self._server.serve_forever()
            except KeyboardInterrupt:
                print("\nShutting down metrics server...")
                self._server.shutdown()
        else:
            import threading
            thread = threading.Thread(target=self._server.serve_forever, daemon=True)
            thread.start()

    def stop(self) -> None:
        """停止HTTP服务器"""
        if self._server:
            self._server.shutdown()
            self._server = None


# 便捷函数
def record_parse_time(duration_ms: float) -> None:
    """记录解析耗时（全局）"""
    get_metrics_collector().record_parse_time(duration_ms)


def record_contract_build_time(duration_ms: float) -> None:
    """记录合约构建耗时（全局）"""
    get_metrics_collector().record_contract_build_time(duration_ms)


def record_verify_count(result: str) -> None:
    """记录验证次数（全局）"""
    get_metrics_collector().record_verify_count(result)


def record_drift_score(score: float, level: DriftLevel = None) -> None:
    """记录偏离度（全局）"""
    get_metrics_collector().record_drift_score(score, level)


def set_feature_count(count: int) -> None:
    """设置功能点数量（全局）"""
    get_metrics_collector().set_feature_count(count)
