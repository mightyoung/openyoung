#!/usr/bin/env python3
"""
自动化 Skill 触发评估工具
自动测试 Skill 是否正确触发，生成对比报告
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

TRIGGER_EVAL_QUERIES = [
    # 应该触发的查询
    {"query": "从 GitHub 导入 anthropics/claude-code 作为本地 agent", "should_trigger": True},
    {"query": "帮我从 GitHub 上拉取 ruvnet/claude-flow 并配置成本地 agent", "should_trigger": True},
    {"query": "import github https://github.com/affaan-m/everything-claude-code as my-agent", "should_trigger": True},
    {"query": "克隆一个 GitHub 仓库作为我的开发助手", "should_trigger": True},
    {"query": "把 GitHub 上的 Claude Code 项目下到本地", "should_trigger": True},
    {"query": "从 github 拉取 agent 模板到本地项目", "should_trigger": True},
    {"query": "我想要一个类似 claude-code 的 agent 配置", "should_trigger": True},
    {"query": "将 GitHub 仓库配置成 OpenYoung 可用的 agent", "should_trigger": True},
    {"query": "下载并配置 GitHub 上的 AI agent 项目", "should_trigger": True},
    {"query": "从 GitHub 克隆 agent 配置到本地 packages 目录", "should_trigger": True},

    # 不应该触发的查询
    {"query": "帮我写一个 Python 排序函数", "should_trigger": False},
    {"query": "分析这段代码的质量", "should_trigger": False},
    {"query": "创建一个 React 组件", "should_trigger": False},
    {"query": "修复这个 bug", "should_trigger": False},
    {"query": "帮我写一篇博客文章", "should_trigger": False},
    {"query": "从网上爬取一些数据", "should_trigger": False},
    {"query": "优化一下这个函数的性能", "should_trigger": False},
    {"query": "给我讲讲什么是机器学习", "should_trigger": False},
    {"query": "翻译这段英文到中文", "should_trigger": False},
    {"query": "帮我整理一下这个项目的文件结构", "should_trigger": False},
]


def load_skill_description() -> str:
    """加载 Skill 描述"""
    skill_file = Path("packages/skill-github-import/skill.yaml")
    if not skill_file.exists():
        skill_file = Path("skills/github-import/skill.yaml")

    if skill_file.exists():
        import yaml
        with open(skill_file) as f:
            config = yaml.safe_load(f)
            return config.get("description", "")
    return ""


def check_trigger_by_keywords(query: str, description: str) -> bool:
    """
    基于关键词匹配判断是否应该触发
    模拟 Claude 的触发逻辑
    """
    query_lower = query.lower()

    # 核心触发词 - 必须包含这些词之一
    core_keywords = [
        "github", "git", "导入", "克隆", "clone", "拉取", "下载",
        "import", "类似", "想要"
    ]

    # 相关词 - 与核心词配合使用
    related_keywords = [
        "agent", "配置", "模板", "项目", "本地", "仓库", "code", "一个"
    ]

    # 检查是否包含核心触发词
    has_core = any(kw in query_lower for kw in core_keywords)

    # 检查是否包含相关词
    has_related = any(kw in query_lower for kw in related_keywords)

    # 触发条件: 包含核心词 + (包含相关词 或 包含"从...到"结构)
    from_to_pattern = "从" in query_lower and "到" in query_lower
    has_project_ref = "项目" in query_lower or "本地" in query_lower

    return has_core and (has_related or from_to_pattern or has_project_ref)


def run_evaluation() -> Dict[str, Any]:
    """运行评估"""
    description = load_skill_description()

    results = {
        "total": len(TRIGGER_EVAL_QUERIES),
        "passed": 0,
        "failed": 0,
        "true_positives": 0,  # 应该触发且确实触发
        "true_negatives": 0,  # 不应该触发且确实不触发
        "false_positives": 0,  # 不应该触发但触发了
        "false_negatives": 0,  # 应该触发但没触发
        "queries": []
    }

    for item in TRIGGER_EVAL_QUERIES:
        query = item["query"]
        expected = item["should_trigger"]

        # 使用关键词匹配判断
        predicted = check_trigger_by_keywords(query, description)

        # 记录结果
        query_result = {
            "query": query,
            "expected": expected,
            "predicted": predicted,
            "correct": expected == predicted
        }

        if expected == predicted:
            results["passed"] += 1
            if expected:
                results["true_positives"] += 1
            else:
                results["true_negatives"] += 1
        else:
            results["failed"] += 1
            if expected and not predicted:
                results["false_negatives"] += 1
            else:
                results["false_positives"] += 1

        results["queries"].append(query_result)

    # 计算指标
    results["precision"] = results["true_positives"] / (results["true_positives"] + results["false_positives"]) if (results["true_positives"] + results["false_positives"]) > 0 else 0
    results["recall"] = results["true_positives"] / (results["true_positives"] + results["false_negatives"]) if (results["true_positives"] + results["false_negatives"]) > 0 else 0
    results["f1"] = 2 * results["precision"] * results["recall"] / (results["precision"] + results["recall"]) if (results["precision"] + results["recall"]) > 0 else 0
    results["accuracy"] = results["passed"] / results["total"]

    return results


def print_report(results: Dict[str, Any]):
    """打印评估报告"""
    print("\n" + "="*60)
    print("Skill 触发评估报告")
    print("="*60)

    print("\n📊 总体结果:")
    print(f"   总查询数: {results['total']}")
    print(f"   通过: {results['passed']} ✅")
    print(f"   失败: {results['failed']} ❌")

    print("\n📈 详细指标:")
    print(f"   准确率 (Accuracy): {results['accuracy']*100:.1f}%")
    print(f"   精确率 (Precision): {results['precision']*100:.1f}%")
    print(f"   召回率 (Recall): {results['recall']*100:.1f}%")
    print(f"   F1 分数: {results['f1']*100:.1f}%")

    print("\n🔍 混淆矩阵:")
    print(f"   真正例 (TP): {results['true_positives']}")
    print(f"   真反例 (TN): {results['true_negatives']}")
    print(f"   假正例 (FP): {results['false_positives']}")
    print(f"   假反例 (FN): {results['false_negatives']}")

    print("\n❌ 失败案例:")
    failed_queries = [q for q in results["queries"] if not q["correct"]]
    if failed_queries:
        for q in failed_queries:
            expected = "触发" if q["expected"] else "不触发"
            predicted = "触发" if q["predicted"] else "不触发"
            print(f"   - {q['query'][:50]}...")
            print(f"     期望: {expected}, 预测: {predicted}")
    else:
        print("   无")

    print("\n" + "="*60)


def main():
    print("🔄 正在评估 Skill 触发逻辑...")
    results = run_evaluation()
    print_report(results)

    # 保存报告
    output_file = Path("github-import-workspace/trigger_eval_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n📄 报告已保存到: {output_file}")


if __name__ == "__main__":
    main()
