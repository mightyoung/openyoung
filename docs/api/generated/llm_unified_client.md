UnifiedLLMClient - 统一 LLM 客户端

整合所有 Provider，提供统一的接口

## Classes

### `UnifiedLLMClient`

统一 LLM 客户端

用法示例:
```python
client = UnifiedLLMClient()

# 普通聊天
response = await client.chat(
    model="gpt-4o",
    messages=[Message(role="user", content="Hello")]
)

# Thinking 模式
response = await client.chat_with_thinking(
    model="o1",
    messages=[Message(role="user", content="Solve this problem...")]
)

# 流式输出
async for chunk in client.stream_chat(
    model="gpt-4o",
    messages=[Message(role="user", content="Tell me a story")]
):
    print(chunk, end="")
```

**Methods:**
- `get_profile`
- `get_capabilities`

## Functions

### `create_client()`

创建统一客户端的便捷函数

### `get_profile()`

获取模型能力配置

### `get_capabilities()`

获取模型能力
