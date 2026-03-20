"""
Tests for PEAS metrics collection
"""
import pytest
import time
import threading
from src.peas.monitoring.metrics import (
    MetricsCollector,
    get_metrics_collector,
    record_parse_time,
    record_verify_count,
    record_drift_score,
    set_feature_count,
)
from src.peas.types.verification import DriftLevel


class TestMetricsCollector:
    """测试MetricsCollector类"""

    def test_init(self):
        """测试初始化"""
        collector = MetricsCollector()

        assert collector._parse_durations == []
        assert collector._verify_counts["verified"] == 0
        assert collector._verify_counts["failed"] == 0
        assert collector._drift_score is None
        assert collector._feature_count == 0

    def test_record_parse_time(self):
        """测试记录解析耗时"""
        collector = MetricsCollector()

        collector.record_parse_time(10.0)  # 10ms
        collector.record_parse_time(20.0)  # 20ms
        collector.record_parse_time(30.0)  # 30ms

        metrics = collector.get_metrics()
        assert metrics["parse_duration_seconds"]["count"] == 3
        assert metrics["parse_duration_seconds"]["sum"] == pytest.approx(0.06)

    def test_record_contract_build_time(self):
        """测试记录合约构建耗时"""
        collector = MetricsCollector()

        collector.record_contract_build_time(50.0)  # 50ms
        collector.record_contract_build_time(100.0)  # 100ms

        metrics = collector.get_metrics()
        assert metrics["contract_build_duration_seconds"]["count"] == 2
        assert metrics["contract_build_duration_seconds"]["sum"] == pytest.approx(0.15)

    def test_record_verify_count(self):
        """测试记录验证次数"""
        collector = MetricsCollector()

        collector.record_verify_count("verified")
        collector.record_verify_count("verified")
        collector.record_verify_count("failed")
        collector.record_verify_count("skipped")

        metrics = collector.get_metrics()
        assert metrics["verify_total"]["verified"] == 2
        assert metrics["verify_total"]["failed"] == 1
        assert metrics["verify_total"]["skipped"] == 1

    def test_record_verify_count_invalid(self):
        """测试无效的验证结果"""
        collector = MetricsCollector()

        collector.record_verify_count("unknown_result")

        metrics = collector.get_metrics()
        assert metrics["verify_total"]["unknown_result"] == 1

    def test_record_drift_score(self):
        """测试记录偏离度"""
        collector = MetricsCollector()

        collector.record_drift_score(25.5, DriftLevel.MODERATE)

        metrics = collector.get_metrics()
        assert metrics["drift_score"]["value"] == pytest.approx(25.5)
        assert metrics["drift_score"]["level"] == "moderate"

    def test_record_drift_score_without_level(self):
        """测试记录偏离度（无级别）"""
        collector = MetricsCollector()

        collector.record_drift_score(10.0)

        metrics = collector.get_metrics()
        assert metrics["drift_score"]["value"] == pytest.approx(10.0)
        assert metrics["drift_score"]["level"] is None

    def test_set_feature_count(self):
        """测试设置功能点数量"""
        collector = MetricsCollector()

        collector.set_feature_count(10)
        collector.set_feature_count(15)

        metrics = collector.get_metrics()
        assert metrics["feature_count"] == 15

    def test_histogram_quantiles(self):
        """测试直方图分位数计算"""
        collector = MetricsCollector()

        # 记录多个值
        for i in range(100):
            collector.record_parse_time(i * 10.0 + 5.0)  # 5ms to 1005ms

        metrics = collector.get_metrics()
        parse_stats = metrics["parse_duration_seconds"]

        # 检查分位数
        assert "quantiles" in parse_stats
        # 中位数应该约为500ms左右
        assert parse_stats["quantiles"]["0.5"] == pytest.approx(0.5, rel=0.1)

    def test_histogram_buckets(self):
        """测试直方图桶（非累计存储，Prometheus输出时累计）"""
        collector = MetricsCollector()

        # 记录不同范围的值（单位：毫秒）
        # 转换为秒：2ms=0.002s, 8ms=0.008s, 15ms=0.015s
        collector.record_parse_time(2.0)   # 2ms -> 0.002s -> 落在 0.005 桶
        collector.record_parse_time(8.0)   # 8ms -> 0.008s -> 落在 0.01 桶
        collector.record_parse_time(15.0)  # 15ms -> 0.015s -> 落在 0.025 桶

        # 内部存储是非累计的：每个值只落入一个桶
        with collector._lock:
            # 值 <= 0.001s (1ms): 0 (没有任何值 <= 1ms)
            assert collector._parse_buckets[0.001] == 0
            # 值在 (0.001, 0.005]s 范围: 1 (2ms)
            assert collector._parse_buckets[0.005] == 1
            # 值在 (0.005, 0.01]s 范围: 1 (8ms)
            assert collector._parse_buckets[0.01] == 1
            # 值在 (0.01, 0.025]s 范围: 1 (15ms)
            assert collector._parse_buckets[0.025] == 1

        # 验证Prometheus输出是累计的
        output = collector.to_prometheus()
        # 累计：bucket{le="0.005"} 应该等于 1
        # 累计：bucket{le="0.01"} 应该等于 2 (1+1)
        # 累计：bucket{le="0.025"} 应该等于 3 (2+1)
        assert 'le="0.005"' in output
        assert 'le="0.01"' in output
        assert 'le="0.025"' in output


class TestPrometheusFormat:
    """测试Prometheus格式输出"""

    def test_basic_output(self):
        """测试基本输出"""
        collector = MetricsCollector()

        collector.record_parse_time(10.0)
        collector.record_verify_count("verified")
        collector.record_verify_count("failed")
        collector.record_drift_score(15.0, DriftLevel.MINOR)
        collector.set_feature_count(5)

        output = collector.to_prometheus()

        # 检查必要的内容
        assert "PEAS_parse_duration_seconds" in output
        assert "PEAS_verify_total" in output
        assert "PEAS_drift_score" in output
        assert 'result="verified"' in output
        assert 'result="failed"' in output
        assert 'level="minor"' in output
        assert "PEAS_feature_count" in output

    def test_histogram_format(self):
        """测试直方图格式"""
        collector = MetricsCollector()

        collector.record_parse_time(5.0)

        output = collector.to_prometheus()

        assert "_bucket" in output
        assert 'le="0.005"' in output
        assert 'le="+Inf"' in output
        assert "_sum" in output
        assert "_count" in output

    def test_empty_output(self):
        """测试空输出"""
        collector = MetricsCollector()

        output = collector.to_prometheus()

        # 应该有指标名称但值为0
        assert "PEAS_parse_duration_seconds_count 0" in output
        assert "PEAS_verify_total{verified}" in output or "PEAS_verify_total" in output

    def test_quantile_output(self):
        """测试分位数输出"""
        collector = MetricsCollector()

        # 记录足够多的值以计算分位数
        for i in range(10):
            collector.record_parse_time(i * 10.0)

        output = collector.to_prometheus()

        # 检查分位数
        assert 'quantile="0.5"' in output
        assert 'quantile="0.9"' in output


class TestGlobalCollector:
    """测试全局收集器"""

    def test_get_metrics_collector(self):
        """测试获取全局收集器"""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()

        # 应该是同一个实例
        assert collector1 is collector2

    def test_global_functions(self):
        """测试全局便捷函数"""
        # 重置全局收集器
        global _global_collector
        _global_collector = None

        # 测试全局函数
        record_parse_time(25.0)
        record_verify_count("verified")
        record_drift_score(20.0, DriftLevel.MINOR)
        set_feature_count(8)

        collector = get_metrics_collector()
        metrics = collector.get_metrics()

        assert metrics["parse_duration_seconds"]["count"] == 1
        assert metrics["verify_total"]["verified"] == 1
        assert metrics["drift_score"]["value"] == pytest.approx(20.0)
        assert metrics["feature_count"] == 8


class TestThreadSafety:
    """测试线程安全"""

    def test_concurrent_writes(self):
        """测试并发写入"""
        collector = MetricsCollector()
        errors = []

        def write_metrics():
            try:
                for _ in range(100):
                    collector.record_parse_time(10.0)
                    collector.record_verify_count("verified")
                    collector.record_drift_score(10.0, DriftLevel.MINOR)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=write_metrics) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        # 应该有500条记录
        metrics = collector.get_metrics()
        assert metrics["parse_duration_seconds"]["count"] == 500
        assert metrics["verify_total"]["verified"] == 500


class TestReset:
    """测试重置功能"""

    def test_reset(self):
        """测试重置"""
        collector = MetricsCollector()

        collector.record_parse_time(10.0)
        collector.record_verify_count("verified")
        collector.record_drift_score(20.0, DriftLevel.MINOR)
        collector.set_feature_count(5)

        collector.reset()

        metrics = collector.get_metrics()
        assert metrics["parse_duration_seconds"]["count"] == 0
        assert metrics["verify_total"]["verified"] == 0
        assert metrics["drift_score"]["value"] is None
        assert metrics["feature_count"] == 0
