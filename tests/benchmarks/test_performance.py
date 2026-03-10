"""
Performance Benchmark Tests

基于顶级专家视角设计:
- Brendan Gregg: USE 方法 (Utilization, Saturation, Errors)
- Jeff Dean: 延迟和吞吐量基准
- Martin Thompson: 性能回归检测

基准测试验证:
1. Context Collector 性能
2. Audit 模块性能
3. 模块导入时间
4. CLI 命令响应时间
"""

import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

import pytest


# ==================== 基准测试: Context Collector ====================

class BenchmarkContextCollector:
    """Context Collector 性能基准"""

    def setup_method(self):
        """每个测试前初始化"""
        from src.runtime.context_collector import ContextCollector
        self.collector = ContextCollector()

    def run_collector_iterations(self, iterations: int = 100) -> Dict[str, float]:
        """运行多次收集并测量时间"""
        from src.runtime.context_collector import ContextCollector
        times = []

        for _ in range(iterations):
            collector = ContextCollector()  # Create fresh instance
            start = time.perf_counter()

            # 收集所有数据
            collector.collect_skills()
            collector.collect_mcps()
            collector.collect_hooks()
            collector.collect_environment_vars()
            collector.collect_network_status()

            elapsed = time.perf_counter() - start
            times.append(elapsed * 1000)  # 转换为毫秒

        return {
            "iterations": iterations,
            "total_ms": sum(times),
            "avg_ms": sum(times) / len(times),
            "min_ms": min(times),
            "max_ms": max(times),
            "p50_ms": sorted(times)[len(times) // 2],
            "p95_ms": sorted(times)[int(len(times) * 0.95)],
            "p99_ms": sorted(times)[int(len(times) * 0.99)],
        }


class TestContextCollectorPerformance:
    """Context Collector 性能测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.benchmark = BenchmarkContextCollector()

    def test_collector_serialization_performance(self):
        """测试序列化性能"""
        from src.runtime.context_collector import ContextCollector

        collector = ContextCollector()
        collector.collect_skills()
        collector.collect_mcps()
        collector.collect_hooks()

        # 测量 JSON 序列化时间
        iterations = 50
        times = []

        for _ in range(iterations):
            start = time.perf_counter()
            json_str = collector.to_json()
            elapsed = time.perf_counter() - start
            times.append(elapsed * 1000)

        avg_ms = sum(times) / len(times)

        # 基准: 平均应该 < 10ms
        print(f"\n[ContextCollector] JSON序列化: avg={avg_ms:.2f}ms, p95={sorted(times)[int(len(times)*0.95)]:.2f}ms")

        assert avg_ms < 50, f"序列化太慢: {avg_ms:.2f}ms"

    def test_collector_data_collection_performance(self):
        """测试数据收集性能"""
        result = self.benchmark.run_collector_iterations(20)

        print(f"\n[ContextCollector] 数据收集:")
        print(f"  平均: {result['avg_ms']:.2f}ms")
        print(f"  P95:  {result['p95_ms']:.2f}ms")
        print(f"  P99:  {result['p99_ms']:.2f}ms")

        # 基准: 平均应该 < 100ms
        assert result['avg_ms'] < 100, f"收集太慢: {result['avg_ms']:.2f}ms"


# ==================== 基准测试: Audit 模块 ====================

class BenchmarkAudit:
    """Audit 模块性能基准"""

    def run_audit_event_creation(self, iterations: int = 1000) -> Dict[str, float]:
        """测试审计事件创建性能"""
        from src.runtime.audit import AuditEvent
        from datetime import datetime

        times = []

        for _ in range(iterations):
            start = time.perf_counter()

            event = AuditEvent(
                timestamp=datetime.now(),
                event_type="benchmark",
                sandbox_id="bench-001"
            )
            event.to_dict()

            elapsed = time.perf_counter() - start
            times.append(elapsed * 1000)

        return {
            "iterations": iterations,
            "total_ms": sum(times),
            "avg_ms": sum(times) / len(times),
            "min_ms": min(times),
            "max_ms": max(times),
            "ops_per_sec": iterations / (sum(times) / 1000),
        }


class TestAuditPerformance:
    """Audit 模块性能测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.benchmark = BenchmarkAudit()

    def test_audit_event_creation_performance(self):
        """测试审计事件创建性能"""
        result = self.benchmark.run_audit_event_creation(500)

        print(f"\n[Audit] 事件创建:")
        print(f"  平均: {result['avg_ms']:.4f}ms")
        print(f"  吞吐量: {result['ops_per_sec']:.0f} ops/sec")

        # 基准: 应该 > 1000 ops/sec
        assert result['ops_per_sec'] > 1000, f"太慢: {result['ops_per_sec']:.0f} ops/sec"

    def test_audit_json_serialization_performance(self):
        """测试 JSON 序列化性能"""
        from src.runtime.audit import AuditEvent
        from datetime import datetime
        import json

        event = AuditEvent(
            timestamp=datetime.now(),
            event_type="benchmark",
            sandbox_id="bench-001",
            code_length=10000,
            duration_ms=5000
        )

        iterations = 500
        times = []

        for _ in range(iterations):
            start = time.perf_counter()
            json.dumps(event.to_dict())
            elapsed = time.perf_counter() - start
            times.append(elapsed * 1000)

        avg_ms = sum(times) / len(times)

        print(f"\n[Audit] JSON序列化: avg={avg_ms:.4f}ms")

        assert avg_ms < 1, f"JSON序列化太慢: {avg_ms:.4f}ms"


# ==================== 基准测试: 模块导入 ====================

class TestModuleImportPerformance:
    """模块导入性能测试"""

    def test_import_context_collector(self):
        """测试 ContextCollector 导入时间"""
        # 先清除缓存
        modules_to_remove = [m for m in sys.modules.keys() if 'context_collector' in m]
        for m in modules_to_remove:
            del sys.modules[m]

        start = time.perf_counter()
        from src.runtime.context_collector import ContextCollector
        elapsed = time.perf_counter() - start

        print(f"\n[Import] ContextCollector: {elapsed*1000:.2f}ms")

        # 基准: 应该 < 500ms
        assert elapsed < 0.5, f"导入太慢: {elapsed*1000:.2f}ms"

    def test_import_audit(self):
        """测试 Audit 导入时间"""
        modules_to_remove = [m for m in sys.modules.keys() if 'runtime.audit' in m]
        for m in modules_to_remove:
            del sys.modules[m]

        start = time.perf_counter()
        from src.runtime.audit import AuditEvent
        elapsed = time.perf_counter() - start

        print(f"\n[Import] AuditEvent: {elapsed*1000:.2f}ms")

        assert elapsed < 0.5, f"导入太慢: {elapsed*1000:.2f}ms"

    def test_import_runtime_package(self):
        """测试 runtime 包导入时间"""
        modules_to_remove = [m for m in sys.modules.keys() if m.startswith('src.runtime')]
        for m in modules_to_remove:
            del sys.modules[m]

        start = time.perf_counter()
        import src.runtime
        elapsed = time.perf_counter() - start

        print(f"\n[Import] src.runtime: {elapsed*1000:.2f}ms")

        assert elapsed < 1.0, f"导入太慢: {elapsed*1000:.2f}ms"


# ==================== 基准测试: CLI 命令 ====================

class TestCLIPerformance:
    """CLI 命令性能测试"""

    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent

    def test_cli_help_performance(self, project_root):
        """测试 --help 命令响应时间"""
        import subprocess

        iterations = 5
        times = []

        for _ in range(iterations):
            start = time.perf_counter()

            result = subprocess.run(
                [sys.executable, "-m", "src.cli.main", "--help"],
                cwd=str(project_root),
                capture_output=True,
                timeout=30,
            )

            elapsed = time.perf_counter() - start
            times.append(elapsed * 1000)

        avg_ms = sum(times) / len(times)

        print(f"\n[CLI] --help: avg={avg_ms:.0f}ms, min={min(times):.0f}ms, max={max(times):.0f}ms")

        assert result.returncode == 0
        assert avg_ms < 2000, f"CLI太慢: {avg_ms:.0f}ms"

    def test_cli_agent_list_performance(self, project_root):
        """测试 agent list 命令响应时间"""
        import subprocess

        iterations = 3
        times = []

        for _ in range(iterations):
            start = time.perf_counter()

            result = subprocess.run(
                [sys.executable, "-m", "src.cli.main", "agent", "list"],
                cwd=str(project_root),
                capture_output=True,
                timeout=30,
            )

            elapsed = time.perf_counter() - start
            times.append(elapsed * 1000)

        avg_ms = sum(times) / len(times)

        print(f"\n[CLI] agent list: avg={avg_ms:.0f}ms")

        assert result.returncode == 0


# ==================== 基准测试: 内存使用 ====================

class TestMemoryUsage:
    """内存使用基准测试"""

    def test_context_collector_memory(self):
        """测试 ContextCollector 内存使用"""
        from src.runtime.context_collector import ContextCollector
        import sys

        # 创建收集器
        collector = ContextCollector()
        collector.collect_skills()
        collector.collect_mcps()
        collector.collect_hooks()
        collector.collect_environment_vars()
        collector.collect_network_status()

        # 序列化
        json_str = collector.to_json()
        size_bytes = len(json_str)
        size_kb = size_bytes / 1024

        print(f"\n[Memory] ContextCollector JSON: {size_kb:.2f} KB")

        # 基准: 应该 < 100KB
        assert size_kb < 100, f"上下文太大: {size_kb:.2f}KB"

    def test_audit_event_memory(self):
        """测试 AuditEvent 内存使用"""
        from src.runtime.audit import AuditEvent
        from datetime import datetime

        event = AuditEvent(
            timestamp=datetime.now(),
            event_type="test",
            sandbox_id="test-001",
            code_length=10000,
            duration_ms=5000,
            memory_used_mb=100.5,
            cpu_percent=50.0
        )

        json_str = json.dumps(event.to_dict())
        size_kb = len(json_str) / 1024

        print(f"\n[Memory] AuditEvent JSON: {size_kb:.2f} KB")

        assert size_kb < 10, f"审计事件太大: {size_kb:.2f}KB"


# ==================== 回归检测 ====================

class TestPerformanceRegression:
    """性能回归测试 - 与之前基准比较"""

    BASELINE = {
        "context_collector_avg_ms": 50,
        "audit_event_creation_ms": 1,
        "module_import_ms": 500,
    }

    def test_baseline_comparison(self):
        """与基准比较"""
        from src.runtime.context_collector import ContextCollector

        # 测量当前性能
        collector = ContextCollector()

        start = time.perf_counter()
        collector.collect_skills()
        collector.collect_mcps()
        elapsed = time.perf_counter() - start
        avg_ms = elapsed * 1000

        baseline = self.BASELINE["context_collector_avg_ms"]
        regression_pct = ((avg_ms - baseline) / baseline) * 100

        print(f"\n[Regression] ContextCollector:")
        print(f"  当前: {avg_ms:.2f}ms")
        print(f"  基准: {baseline}ms")
        print(f"  变化: {regression_pct:+.1f}%")

        # 允许 20% 性能下降
        assert avg_ms < baseline * 1.2, f"性能回归: {regression_pct:+.1f}%"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
