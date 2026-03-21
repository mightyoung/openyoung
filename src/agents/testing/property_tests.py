"""
Property-Based Test Strategies - 使用 Hypothesis

为 Agent 系统创建属性测试策略
注意: 需要安装 hypothesis 才能运行完整的属性测试
"""

HYPOTHESIS_AVAILABLE = False

try:
    import hypothesis.strategies as st

    HYPOTHESIS_AVAILABLE = True
except ImportError:
    # 仅提供策略，不提供测试
    import warnings

    warnings.warn("Hypothesis not installed. Install with: pip install hypothesis")
    st = None


# ====================
# 策略定义 (当 hypothesis 可用时)
# ====================

if HYPOTHESIS_AVAILABLE:

    @st.composite
    def message_strategy(draw):
        """消息策略"""
        role = draw(st.sampled_from(["user", "assistant", "system"]))
        content = draw(st.text(min_size=0, max_size=1000))
        return {"role": role, "content": content}

    @st.composite
    def messages_strategy(draw):
        """消息列表策略"""
        count = draw(st.integers(min_value=0, max_value=10))
        return draw(st.lists(message_strategy(), min_size=count, max_size=count))

    @st.composite
    def agent_config_strategy(draw):
        """Agent 配置策略"""
        return {
            "name": draw(st.text(min_size=1, max_size=50)),
            "model": draw(st.sampled_from(["gpt-4", "gpt-3.5-turbo", "claude-3"])),
            "max_tokens": draw(st.integers(min_value=100, max_value=4000)),
            "temperature": draw(st.floats(min_value=0.0, max_value=2.0)),
        }
else:
    # 回退策略
    def message_strategy():
        """回退消息策略"""
        return {"role": "user", "content": "test message"}

    def messages_strategy():
        """回退消息列表策略"""
        return [{"role": "user", "content": "test"}]

    def agent_config_strategy():
        """回退配置策略"""
        return {"name": "test", "model": "gpt-4", "max_tokens": 1000, "temperature": 0.7}


__all__ = [
    "message_strategy",
    "messages_strategy",
    "agent_config_strategy",
    "HYPOTHESIS_AVAILABLE",
]
