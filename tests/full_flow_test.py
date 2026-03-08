"""
OpenYoung 全流程测试 - 最终版
使用 .env 中的真实 API Keys
"""

import asyncio
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from src.agents.young_agent import YoungAgent
from src.core.types import AgentConfig, AgentMode
from src.flow.parallel import ParallelFlow
from src.flow.sequential import SequentialFlow
from src.llm.client_adapter import LLMClient
from src.memory.auto_memory import AutoMemory
from src.retriever.unified import Skill, UnifiedSkillRetriever


async def test_llm_providers(client: LLMClient, results: list):
    """测试 LLM Provider"""
    print("\n" + "=" * 40)
    print("Test 1: LLM Provider 测试")
    print("=" * 40)

    messages = [
        {"role": "system", "content": "你是一个简洁的AI助手。"},
        {"role": "user", "content": "1+1等于几？"},
    ]

    print(f"\n测试默认模型 ({client.model})...")
    try:
        response = await client.chat(messages, model=client.model, max_tokens=100)
        # 兼容旧格式: {"choices": [{"message": {"content": ...}}]}
        if "choices" in response:
            content = response["choices"][0]["message"].get("content", "")
        else:
            content = str(response)
        print(f"  ✅ 响应: {content[:80]}...")
        results.append(
            {"test": "LLM/default", "status": "PASS", "detail": content[:50]}
        )
    except Exception as e:
        print(f"  ❌ 错误: {str(e)[:80]}")
        results.append(
            {"test": "LLM/default", "status": "FAIL", "detail": str(e)[:50]}
        )


async def test_young_agent(client: LLMClient, results: list):
    """测试 YoungAgent"""
    print("\n" + "=" * 40)
    print("Test 2: YoungAgent 测试")
    print("=" * 40)

    config = AgentConfig(
        name="test_agent",
        mode=AgentMode.PRIMARY,
        model="deepseek-chat",
        temperature=0.7,
    )

    agent = YoungAgent(config)

    print("\n测试 Agent 运行...")
    try:
        result = await agent.run("你好，请介绍一下你自己")
        print(f"  结果: {result[:100]}...")
        results.append(
            {
                "test": "YoungAgent/run",
                "status": "PASS",
                "detail": "Basic execution works",
            }
        )
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        results.append(
            {"test": "YoungAgent/run", "status": "FAIL", "detail": str(e)[:50]}
        )


async def test_memory(results: list):
    """测试 Memory 功能"""
    print("\n" + "=" * 40)
    print("Test 3: Memory 测试")
    print("=" * 40)

    try:
        memory = AutoMemory(max_memories=10, importance_threshold=0.5)

        print("\n存储记忆...")
        await memory.add_memory("用户询问了数学问题", {"type": "math"})
        await memory.add_memory("用户询问了编程问题", {"type": "code"})
        print("  ✅ 记忆存储成功")

        print("\n检索记忆...")
        results_mem = await memory.get_relevant_memories("编程")
        print(f"  找到 {len(results_mem)} 条相关记忆")

        results.append(
            {
                "test": "Memory",
                "status": "PASS",
                "detail": f"Stored and retrieved {len(results_mem)} memories",
            }
        )
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        results.append({"test": "Memory", "status": "FAIL", "detail": str(e)[:50]})


async def test_skill_retriever(results: list):
    """测试 Skill Retriever"""
    print("\n" + "=" * 40)
    print("Test 4: Skill Retriever 测试")
    print("=" * 40)

    try:
        retriever = UnifiedSkillRetriever()

        print("\n注册 Skills...")
        retriever.register_skill(
            Skill("code_writer", "编写代码技能", ["code", "programming"])
        )
        retriever.register_skill(Skill("text_writer", "写作技能", ["writing", "text"]))

        print("\n检索 Skill...")
        found = retriever.retrieve_by_keyword("code")
        print(f"  找到: {[s.name for s in found]}")

        results.append(
            {
                "test": "SkillRetriever",
                "status": "PASS",
                "detail": f"Found {len(found)} skills",
            }
        )
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        results.append(
            {"test": "SkillRetriever", "status": "FAIL", "detail": str(e)[:50]}
        )


async def test_flow(results: list):
    """测试 Flow 编排"""
    print("\n" + "=" * 40)
    print("Test 5: Flow 编排测试")
    print("=" * 40)

    try:
        print("\n测试 Sequential Flow...")
        flow = SequentialFlow(steps=["步骤1", "步骤2"])
        print(f"  Flow 名称: {flow.name}")
        print(f"  Flow 描述: {flow.description}")

        print("\n测试 Parallel Flow...")
        pflow = ParallelFlow(max_concurrent=3)
        print(f"  Flow 名称: {pflow.name}")
        print(f"  Flow 描述: {pflow.description}")

        results.append(
            {
                "test": "Flow",
                "status": "PASS",
                "detail": "Sequential and Parallel flows initialized",
            }
        )
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        results.append({"test": "Flow", "status": "FAIL", "detail": str(e)[:50]})


async def main():
    """主函数"""
    print("=" * 60)
    print("OpenYoung 全流程测试")
    print(f"时间: {datetime.now().isoformat()}")
    print("=" * 60)

    results = []
    client = LLMClient()

    print("模型:", client.model)

    # 运行所有测试
    await test_llm_providers(client, results)
    await test_young_agent(client, results)
    await test_memory(results)
    await test_skill_retriever(results)
    await test_flow(results)

    await client.close()

    # 打印结果摘要
    print("\n" + "=" * 60)
    print("测试结果摘要")
    print("=" * 60)

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")

    print(f"\n总计: {len(results)} 测试")
    print(f"  ✅ 通过: {passed}")
    print(f"  ❌ 失败: {failed}")

    if failed > 0:
        print("\n失败详情:")
        for r in results:
            if r["status"] == "FAIL":
                print(f"  - {r['test']}: {r['detail']}")

    print("\n详细结果:")
    for r in results:
        icon = "✅" if r["status"] == "PASS" else "❌"
        print(f"  {icon} {r['test']}: {r['detail'][:50]}")


if __name__ == "__main__":
    asyncio.run(main())
