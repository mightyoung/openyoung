"""
Sessions Page - 会话管理页面
显示所有持久会话，支持暂停/恢复
"""

import asyncio
from datetime import datetime

import streamlit as st

# 页面配置
st.set_page_config(page_title="Sessions", page_icon="📋", layout="wide")

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
        st.page_link("pages/2_Chat.py", label="💬 Chat")
        st.page_link("pages/4_Dashboard.py", label="📊 Dashboard")
        st.page_link("pages/5_Settings.py", label="⚙️ Settings")


def format_datetime(dt_str: str) -> str:
    """格式化日期时间"""
    if not dt_str:
        return "—"
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return dt_str


def render_session_card(session: dict):
    """渲染会话卡片"""
    with st.container():
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

        with col1:
            st.subheader(session.get("agent_name", "Unknown"))
            st.caption(f"ID: {session.get('session_id', '')[:20]}...")

        with col2:
            # 状态徽章
            status = session.get("status", "idle")
            if status == "running":
                st.success("🟢 Running")
            elif status == "suspended":
                st.warning("🟡 Suspended")
            else:
                st.info("⚪ Idle")

        with col3:
            # 消息数
            msg_count = len(session.get("messages", []))
            st.metric("Messages", msg_count)

        with col4:
            # 操作按钮
            col_btn1, col_btn2 = st.columns(2)

            with col_btn1:
                if st.button("📝", key=f"view_{session.get('session_id')}", help="View"):
                    st.session_state.view_session_id = session.get("session_id")
                    st.switch_page("2_💬_Chat.py")

            with col_btn2:
                if st.button("🗑️", key=f"del_{session.get('session_id')}", help="Delete"):
                    session_service.delete_local_session(session.get("session_id"))
                    st.rerun()

        # 时间信息
        col_time1, col_time2 = st.columns(2)
        with col_time1:
            st.caption(f"Created: {format_datetime(session.get('created_at'))}")
        with col_time2:
            st.caption(f"Updated: {format_datetime(session.get('updated_at'))}")

        st.divider()


async def load_remote_sessions() -> list:
    """加载远程会话"""
    client = APIClient(config.API_BASE_URL, config.API_KEY)
    try:
        sessions = await client.list_sessions()
        await client.close()
        return sessions
    except Exception as e:
        await client.close()
        return []


def main():
    """主函数"""
    st.title("📋 Sessions")

    render_sidebar()

    # 操作栏
    col1, col2 = st.columns([3, 1])

    with col1:
        st.write("管理您的对话会话")

    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()

    # 标签页: 本地会话 | 远程会话
    tab1, tab2 = st.tabs(["💻 Local Sessions", "☁️ Remote Sessions"])

    with tab1:
        # 本地会话
        local_sessions = session_service.list_local_sessions()

        if not local_sessions:
            st.info("No local sessions")
            st.caption("对话将在本地缓存，直到页面刷新")
        else:
            st.write(f"**{len(local_sessions)}** local sessions")

            for session in local_sessions:
                render_session_card(session)

    with tab2:
        # 远程会话
        with st.spinner("Loading remote sessions..."):
            remote_sessions = asyncio.run(load_remote_sessions())

        if not remote_sessions:
            st.info("No remote sessions or API not available")
            st.caption("确保 API 服务器正在运行")
        else:
            st.write(f"**{len(remote_sessions)}** remote sessions")

            for session in remote_sessions:
                render_session_card(
                    {
                        "session_id": session.get("session_id", ""),
                        "agent_name": session.get("agent_name", "Unknown"),
                        "status": session.get("status", "idle"),
                        "messages": [],
                        "created_at": session.get("created_at"),
                        "updated_at": session.get("updated_at"),
                    }
                )

    # 清空所有会话
    st.markdown("---")
    if st.button("🗑️ Clear All Local Sessions", type="primary"):
        session_service.clear()
        st.success("All local sessions cleared")
        st.rerun()


if __name__ == "__main__":
    main()
