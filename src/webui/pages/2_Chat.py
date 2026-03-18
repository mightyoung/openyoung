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

        # 调用 API 获取响应 - 真实流式输出
        with st.chat_message("assistant"):
            full_response = ""

            try:
                import asyncio

                client = APIClient(config.API_BASE_URL, config.API_KEY)

                # 使用SSE流式API
                response_placeholder = st.empty()

                async def stream_and_display():
                    """异步流式处理函数"""
                    nonlocal full_response

                    with st.spinner("Thinking..."):
                        async for event in client.stream_chat(
                            st.session_state.current_session_id, prompt
                        ):
                            event_type = event.get("event", "")
                            event_data = event.get("data", {})

                            if event_type == "chunk":
                                content = event_data.get("content", "")
                                full_response += content
                                response_placeholder.markdown(full_response + "▌")
                            elif event_type == "done":
                                response_placeholder.markdown(full_response)
                                # 保存响应
                                st.session_state.messages.append(
                                    {"role": "assistant", "content": full_response}
                                )
                                session_service.add_message(
                                    st.session_state.current_session_id, "assistant", full_response
                                )
                            elif event_type == "error":
                                error_msg = event_data.get("error", "Unknown error")
                                response_placeholder.error(f"Error: {error_msg}")
                                st.session_state.messages.append(
                                    {"role": "assistant", "content": f"Error: {error_msg}"}
                                )

                    await client.close()

                # 运行异步函数
                asyncio.run(stream_and_display())

            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

        st.rerun()


if __name__ == "__main__":
    main()
