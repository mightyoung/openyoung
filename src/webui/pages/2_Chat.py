"""
Chat Page - 对话页面
支持流式输出、会话历史
"""

import asyncio
import json
import uuid

import streamlit as st

# 页面配置
st.set_page_config(page_title="Chat", page_icon="💬", layout="wide")

# 导入服务
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from webui.services.api_client import APIClient
from webui.services.session_service import session_service
from webui.utils.config import config


def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.title(f"{config.PAGE_ICON} OpenYoung")
        st.divider()
        st.page_link("app.py", label="🏠 Home")
        st.page_link("pages/1_Agents.py", label="🤖 Agents")

        st.divider()
        st.subheader("💬 Sessions")

        # 新建会话按钮
        if st.button("➕ New Chat", use_container_width=True):
            # 创建新会话
            session_id = str(uuid.uuid4())
            agent_name = st.session_state.get("target_agent_name", "default")
            session_service.create_local_session(session_id, agent_name)
            st.session_state.current_session_id = session_id
            st.session_state.messages = []
            st.rerun()

        # 会话列表
        sessions = session_service.list_local_sessions()
        if sessions:
            st.write("Recent Sessions:")
            for session in sessions[-5:][::-1]:  # 最近5个
                session_id = session["session_id"]
                is_active = session_id == st.session_state.get("current_session_id")

                label = f"📝 {session.get('agent_name', 'Unknown')[:20]}"
                if is_active:
                    st.markdown(f"**{label}** (active)")
                else:
                    if st.button(label, key=f"session_{session_id}"):
                        st.session_state.current_session_id = session_id
                        st.session_state.messages = session_service.get_messages(session_id)
                        st.rerun()


def main():
    """主函数"""
    st.title("💬 Chat")

    render_sidebar()

    # 初始化会话状态
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "current_session_id" not in st.session_state:
        # 创建默认会话
        session_id = str(uuid.uuid4())
        agent_name = st.session_state.get("target_agent_name", "default")
        session_service.create_local_session(session_id, agent_name)
        st.session_state.current_session_id = session_id

    # 当前 Agent 信息
    current_agent = st.session_state.get("target_agent_name", "default")
    st.caption(f"Chatting with: **{current_agent}**")

    # 聊天历史显示
    chat_container = st.container()

    with chat_container:
        for msg in st.session_state.messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            with st.chat_message(role):
                st.markdown(content)

    # 输入区域
    if prompt := st.chat_input("Type your message..."):
        # 添加用户消息
        user_message = {"role": "user", "content": prompt}
        st.session_state.messages.append(user_message)
        session_service.add_message(st.session_state.current_session_id, "user", prompt)

        with st.chat_message("user"):
            st.markdown(prompt)

        # 调用 API 获取响应
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""

            # 显示加载状态
            with st.spinner("Thinking..."):
                try:
                    client = APIClient(config.API_BASE_URL, config.API_KEY)

                    # 调用 API (这里使用简化实现)
                    # 实际应该使用流式 API
                    response = await_client_chat(
                        client, st.session_state.current_session_id, prompt
                    )

                    # 流式显示响应
                    for chunk in response:
                        full_response += chunk
                        placeholder.markdown(full_response + "▌")

                    placeholder.markdown(full_response)

                    # 保存响应
                    assistant_message = {"role": "assistant", "content": full_response}
                    st.session_state.messages.append(assistant_message)
                    session_service.add_message(
                        st.session_state.current_session_id, "assistant", full_response
                    )

                    client.close()

                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    placeholder.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

        st.rerun()


async def await_client_chat(client: APIClient, session_id: str, message: str) -> list:
    """调用 API 并返回响应块"""
    try:
        # 尝试发送消息
        result = await client.send_message(session_id, message)
        response_text = result.get("response", "")

        # 模拟流式输出
        chunks = []
        for i in range(0, len(response_text), 10):
            chunks.append(response_text[i : i + 10])

        return chunks if chunks else ["No response"]
    except Exception as e:
        # 如果 API 不可用，返回模拟响应
        return [f"Echo: {message} (API error: {str(e)})"]


if __name__ == "__main__":
    main()
