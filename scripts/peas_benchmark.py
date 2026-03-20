#!/usr/bin/env python3
"""
PEAS Performance Regression Detection Script

性能回归检测脚本:
1. 运行基准测试并收集性能数据
2. 与存储的基准数据对比
3. 检测性能回归并生成报告

Usage:
    python scripts/peas_benchmark.py --run          # 运行基准测试
    python scripts/peas_benchmark.py --compare      # 与基准对比
    python scripts/peas_benchmark.py --update        # 更新基准数据
    python scripts/peas_benchmark.py --report        # 生成完整报告
"""
import argparse
import json
import os
import sys
import time
import statistics
from pathlib import Path
from datetime import datetime
from typing import Any, Callable

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.peas.understanding.markdown_parser import MarkdownParser
from src.peas.verification.drift_detector import DriftDetector
from src.peas.contract.builder import ContractBuilder
from src.peas.types import (
    Priority,
    VerificationStatus,
    FeatureStatus,
    ExecutionContract,
)


# ============================================================================
# Configuration
# ============================================================================

BENCHMARK_DIR = Path(__file__).parent.parent / "tests" / "peas"
BASELINE_FILE = BENCHMARK_DIR / "benchmark_baseline.json"
REPORT_FILE = Path(__file__).parent.parent / "docs" / "benchmark_report.md"

# Performance thresholds (ms)
THRESHOLDS = {
    "parser_small": 500,
    "parser_medium": 500,
    "parser_large": 1000,
    "detector_10": 50,
    "detector_100": 100,
    "detector_1000": 500,
    "builder_small": 100,
    "builder_medium": 200,
    "builder_large": 500,
    "pipeline_small": 1000,
    "pipeline_medium": 2000,
}


# ============================================================================
# Test Data
# ============================================================================

SAMPLE_DOCUMENT_SMALL = """# 用户管理系统

## 功能需求

- [feature] 用户注册功能
- [feature] 用户登录功能
- [feature] 密码重置功能

## 验收标准

Given 用户访问注册页面
When 填写有效信息并提交
Then 注册成功，显示欢迎信息
"""

SAMPLE_DOCUMENT_MEDIUM = """# 电商平台后端API

## 用户模块

### 用户注册 (MUST)
- [feature] 邮箱注册功能
- [feature] 手机号注册功能
- [must] 发送注册验证码

### 用户登录 (MUST)
- [feature] 账号密码登录
- [feature] 短信验证码登录
- [must] JWT token生成

## 商品模块

### 商品列表 (MUST)
- [feature] 分页查询
- [feature] 关键词搜索
- [must] 库存状态过滤

## 订单模块

### 下单功能 (MUST)
- [must] 创建订单
- [must] 库存扣减
- [should] 优惠计算

## 验收标准

Given 用户选择商品并加入购物车
When 完成支付
Then 订单创建成功，库存扣减
"""

SAMPLE_DOCUMENT_LARGE = """# 大型企业管理系统

""" + "\n\n".join([
    f"""## 模块{i}

### 功能{i}.1 (MUST)
- [feature] 核心业务功能{i}.1.1
- [must] 必选功能{i}.1.2

### 功能{i}.2 (SHOULD)
- [feature] 重要功能{i}.2.1

"""
    for i in range(1, 20)
])


# ============================================================================
# Benchmark Utilities
# ============================================================================

def measure(func: Callable[[], Any], warmup: int = 5, iterations: int = 100) -> dict:
    """执行性能测量"""
    # Warmup
    for _ in range(warmup):
        func()

    # Actual measurement
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        result = func()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to ms

    return {
        "mean_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0,
        "min_ms": min(times),
        "max_ms": max(times),
        "iterations": iterations,
        "warmup": warmup,
    }


def create_statuses(count: int) -> list[FeatureStatus]:
    """创建状态列表"""
    statuses = []
    for i in range(count):
        status_value = [VerificationStatus.VERIFIED, VerificationStatus.FAILED, VerificationStatus.SKIPPED][i % 3]
        statuses.append(FeatureStatus(
            req_id=f"REQ-{i:03d}",
            status=status_value,
            notes=f"Status {i}"
        ))
    return statuses


def create_contract(requirement_count: int) -> ExecutionContract:
    """创建合约"""
    requirements = []
    for i in range(requirement_count):
        priority = [Priority.MUST, Priority.SHOULD, Priority.COULD][i % 3]
        requirements.append(
            type("ContractRequirement", (), {
                "req_id": f"REQ-{i:03d}",
                "description": f"功能点{i}",
                "priority": priority,
            })()
        )
    return ExecutionContract.create(
        requirements=requirements,
        version="1.0",
        metadata={"test": True}
    )


# ============================================================================
# Benchmarks
# ============================================================================

def run_parser_benchmarks() -> dict:
    """运行Parser基准测试"""
    parser = MarkdownParser()
    results = {}

    # Small document
    results["parser_small"] = measure(
        lambda: parser.parse(SAMPLE_DOCUMENT_SMALL),
        warmup=10, iterations=100
    )

    # Medium document
    results["parser_medium"] = measure(
        lambda: parser.parse(SAMPLE_DOCUMENT_MEDIUM),
        warmup=5, iterations=50
    )

    # Large document
    results["parser_large"] = measure(
        lambda: parser.parse(SAMPLE_DOCUMENT_LARGE),
        warmup=3, iterations=20
    )

    return results


def run_detector_benchmarks() -> dict:
    """运行DriftDetector基准测试"""
    detector = DriftDetector()
    results = {}

    # Empty
    results["detector_0"] = measure(
        lambda: detector.detect([], None),
        warmup=20, iterations=500
    )

    # 10 features
    statuses_10 = create_statuses(10)
    results["detector_10"] = measure(
        lambda: detector.detect(statuses_10, None),
        warmup=20, iterations=500
    )

    # 100 features
    statuses_100 = create_statuses(100)
    results["detector_100"] = measure(
        lambda: detector.detect(statuses_100, None),
        warmup=10, iterations=200
    )

    # 1000 features
    statuses_1000 = create_statuses(1000)
    results["detector_1000"] = measure(
        lambda: detector.detect(statuses_1000, None),
        warmup=5, iterations=50
    )

    # With contract
    contract = create_contract(100)
    results["detector_contract"] = measure(
        lambda: detector.detect(statuses_100, contract),
        warmup=10, iterations=100
    )

    return results


def run_builder_benchmarks() -> dict:
    """运行ContractBuilder基准测试"""
    builder = ContractBuilder()
    parser = MarkdownParser()
    results = {}

    # Small doc
    doc_small = parser.parse(SAMPLE_DOCUMENT_SMALL)
    results["builder_small"] = measure(
        lambda: builder.build(doc_small),
        warmup=10, iterations=100
    )

    # Medium doc
    doc_medium = parser.parse(SAMPLE_DOCUMENT_MEDIUM)
    results["builder_medium"] = measure(
        lambda: builder.build(doc_medium),
        warmup=5, iterations=50
    )

    # Large doc
    doc_large = parser.parse(SAMPLE_DOCUMENT_LARGE)
    results["builder_large"] = measure(
        lambda: builder.build(doc_large),
        warmup=3, iterations=20
    )

    return results


def run_pipeline_benchmarks() -> dict:
    """运行端到端流程基准测试"""
    parser = MarkdownParser()
    builder = ContractBuilder()
    detector = DriftDetector()
    results = {}

    # Small pipeline
    def pipeline_small():
        doc = parser.parse(SAMPLE_DOCUMENT_SMALL)
        contract = builder.build(doc)
        statuses = [
            FeatureStatus(req_id=fp.id, status=VerificationStatus.VERIFIED, evidence=["test"], notes="ok")
            for fp in doc.feature_points
        ]
        return detector.detect(statuses, contract)

    results["pipeline_small"] = measure(pipeline_small, warmup=5, iterations=50)

    # Medium pipeline
    def pipeline_medium():
        doc = parser.parse(SAMPLE_DOCUMENT_MEDIUM)
        contract = builder.build(doc)
        statuses = [
            FeatureStatus(req_id=fp.id, status=VerificationStatus.VERIFIED, evidence=["test"], notes="ok")
            for fp in doc.feature_points
        ]
        return detector.detect(statuses, contract)

    results["pipeline_medium"] = measure(pipeline_medium, warmup=3, iterations=20)

    return results


# ============================================================================
# Main Functions
# ============================================================================

def run_all_benchmarks() -> dict:
    """运行所有基准测试"""
    print("Running PEAS Performance Benchmarks...")
    print("=" * 60)

    results = {
        "timestamp": datetime.now().isoformat(),
        "parser": run_parser_benchmarks(),
        "detector": run_detector_benchmarks(),
        "builder": run_builder_benchmarks(),
        "pipeline": run_pipeline_benchmarks(),
    }

    print("\nBenchmarks completed!")
    return results


def compare_with_baseline(current: dict, baseline: dict) -> dict:
    """与基准数据对比"""
    regressions = []
    improvements = []

    # Flatten current results for comparison
    flat_current = {}
    for category, data in current.items():
        if category == "timestamp":
            continue
        for key, value in data.items():
            flat_current[key] = value

    # Compare each key
    for key, value in flat_current.items():
        if key in baseline:
            base_mean = baseline[key]["mean_ms"]
            current_mean = value["mean_ms"]
            threshold = baseline[key].get("threshold_ms", THRESHOLDS.get(key, 100))

            diff_pct = ((current_mean - base_mean) / base_mean * 100) if base_mean > 0 else 0

            if current_mean > threshold:
                regressions.append({
                    "test": key,
                    "baseline_ms": base_mean,
                    "current_ms": current_mean,
                    "threshold_ms": threshold,
                    "diff_pct": diff_pct,
                })
            elif diff_pct < -10:  # 10% improvement
                improvements.append({
                    "test": key,
                    "baseline_ms": base_mean,
                    "current_ms": current_mean,
                    "diff_pct": diff_pct,
                })

    return {
        "regressions": regressions,
        "improvements": improvements,
    }


def save_baseline(results: dict):
    """保存基准数据"""
    baseline = {}
    for category, data in results.items():
        if category == "timestamp":
            continue
        for key, value in data.items():
            # Keys are already in format like "parser_small"
            baseline[key] = {
                "mean_ms": value["mean_ms"],
                "threshold_ms": THRESHOLDS.get(key, 100),
                "timestamp": results["timestamp"],
            }

    with open(BASELINE_FILE, "w") as f:
        json.dump(baseline, f, indent=2)

    print(f"Baseline saved to {BASELINE_FILE}")


def load_baseline() -> dict:
    """加载基准数据"""
    if not BASELINE_FILE.exists():
        return {}

    with open(BASELINE_FILE, "r") as f:
        return json.load(f)


def generate_report(current: dict, comparison: dict = None):
    """生成基准测试报告"""
    lines = [
        "# PEAS Performance Benchmark Report",
        "",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        "",
        f"- Timestamp: {current.get('timestamp', 'N/A')}",
        "",
        "## Parser Performance",
        "",
    ]

    for key, value in current.get("parser", {}).items():
        threshold = THRESHOLDS.get(f"parser_{key}", 500)
        status = "✅ PASS" if value["mean_ms"] <= threshold else "❌ FAIL"
        lines.append(f"- **{key}**: {value['mean_ms']:.2f}ms (threshold: {threshold}ms) {status}")

    lines.extend(["", "## DriftDetector Performance", ""])
    for key, value in current.get("detector", {}).items():
        threshold = THRESHOLDS.get(f"detector_{key}", 100)
        status = "✅ PASS" if value["mean_ms"] <= threshold else "❌ FAIL"
        lines.append(f"- **{key}**: {value['mean_ms']:.2f}ms (threshold: {threshold}ms) {status}")

    lines.extend(["", "## ContractBuilder Performance", ""])
    for key, value in current.get("builder", {}).items():
        threshold = THRESHOLDS.get(f"builder_{key}", 100)
        status = "✅ PASS" if value["mean_ms"] <= threshold else "❌ FAIL"
        lines.append(f"- **{key}**: {value['mean_ms']:.2f}ms (threshold: {threshold}ms) {status}")

    lines.extend(["", "## End-to-End Pipeline", ""])
    for key, value in current.get("pipeline", {}).items():
        threshold = THRESHOLDS.get(f"pipeline_{key}", 1000)
        status = "✅ PASS" if value["mean_ms"] <= threshold else "❌ FAIL"
        lines.append(f"- **{key}**: {value['mean_ms']:.2f}ms (threshold: {threshold}ms) {status}")

    if comparison:
        lines.extend(["", "## Regression Analysis", ""])

        if comparison["regressions"]:
            lines.append("### ⚠️ Regressions Detected")
            for reg in comparison["regressions"]:
                lines.append(
                    f"- **{reg['test']}**: {reg['current_ms']:.2f}ms "
                    f"(baseline: {reg['baseline_ms']:.2f}ms, +{reg['diff_pct']:.1f}%)"
                )
        else:
            lines.append("### ✅ No Regressions Detected")

        if comparison["improvements"]:
            lines.append("")
            lines.append("### 🚀 Performance Improvements")
            for imp in comparison["improvements"]:
                lines.append(
                    f"- **{imp['test']}**: {imp['current_ms']:.2f}ms "
                    f"(baseline: {imp['baseline_ms']:.2f}ms, {imp['diff_pct']:.1f}%)"
                )

    # Ensure directory exists
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(REPORT_FILE, "w") as f:
        f.write("\n".join(lines))

    print(f"\nReport saved to {REPORT_FILE}")

    # Also print to console
    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    print("\n".join(lines))


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="PEAS Performance Benchmark")
    parser.add_argument("--run", action="store_true", help="Run benchmarks")
    parser.add_argument("--compare", action="store_true", help="Compare with baseline")
    parser.add_argument("--update", action="store_true", help="Update baseline")
    parser.add_argument("--report", action="store_true", help="Generate report")

    args = parser.parse_args()

    if args.run:
        results = run_all_benchmarks()
        generate_report(results)

    elif args.compare:
        baseline = load_baseline()
        if not baseline:
            print("No baseline found. Run --run first.")
            return

        results = run_all_benchmarks()
        comparison = compare_with_baseline(results, baseline)
        generate_report(results, comparison)

        if comparison["regressions"]:
            print("\n⚠️ WARNING: Performance regressions detected!")
            sys.exit(1)

    elif args.update:
        results = run_all_benchmarks()
        save_baseline(results)
        print("Baseline updated!")

    elif args.report:
        baseline = load_baseline()
        if baseline:
            results = run_all_benchmarks()
            comparison = compare_with_baseline(results, baseline)
            generate_report(results, comparison)
        else:
            results = run_all_benchmarks()
            generate_report(results)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
