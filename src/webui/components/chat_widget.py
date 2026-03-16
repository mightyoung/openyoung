"""
Chat Widget - 聊天组件
"""

from typing import Dict, List

import streamlit as st


def render_message(message: Dict[str, str], key: str = None):
    """渲染单条消息"""
    role = message.get("role", "user")
    content = message.get("content", "")

    with st.chat_message(role):
        st.markdown(content)


def render_message_list(messages: List[Dict[str, str]]):
    """渲染消息列表"""
    for i, message in enumerate(messages):
        render_message(message, key=f"msg_{i}")


def render_typing_indicator():
    """渲染打字指示器"""
    return st.empty()


def render_error(message: str):
    """渲染错误消息"""
    st.error(message)


def render_success(message: str):
    """渲染成功消息"""
    st.success(message)
