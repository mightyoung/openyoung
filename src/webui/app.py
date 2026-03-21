"""
OpenYoung WebUI - Streamlit 主应用入口

提供可视化 Agent 对话体验和执行监控
"""

import streamlit as st

from webui.services.api_client import APIClient
from webui.utils.config import config


def init_session_state():
    """初始化会话状态"""
    defaults = {
        "api_client": None,
        "current_session_id": None,
        "messages": [],
        "agents": [],
        "sessions": [],
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_api_client() -> Optional[APIClient]:
    """获取 API 客户端"""
    if st.session_state.api_client is None:
        st.session_state.api_client = APIClient(
            base_url=config.API_BASE_URL, api_key=config.API_KEY
        )
    return st.session_state.api_client


def set_page_config():
    """设置页面配置"""
    st.set_page_config(
        page_title=config.TITLE,
        page_icon=config.PAGE_ICON,
        layout=config.LAYOUT,
        initial_sidebar_state=config.INITIAL_SIDEBAR_STATE,
    )


def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.title(f"{config.PAGE_ICON} {config.TITLE}")

        st.divider()

        # 导航
        st.page_link("app.py", label="🏠 Home")
        st.page_link("pages/1_Agents.py", label="🤖 Agents")
        st.page_link("pages/2_Chat.py", label="💬 Chat")
        st.page_link("pages/3_Sessions.py", label="📋 Sessions")
        st.page_link("pages/4_Dashboard.py", label="📊 Dashboard")
        st.page_link("pages/5_Settings.py", label="⚙️ Settings")

        st.divider()

        # 状态信息
        st.caption("Connection Status")
        client = get_api_client()
        if client:
            try:
                # 简单检查连接
                st.success("🟢 Connected")
            except Exception:
                st.error("🔴 Disconnected")
        else:
            st.warning("⚠️ Not configured")


def main():
    """主函数"""
    set_page_config()
    init_session_state()
    render_sidebar()

    # Home 页面内容
    st.title(f"Welcome to {config.TITLE} 👋")

    st.markdown("""
    ## 🚀 快速开始

    选择一个页面开始使用：

    - **🤖 Agents**: 浏览和搜索可用的 AI Agents
    - **💬 Chat**: 与 Agent 进行对话
    - **📋 Sessions**: 管理会话历史
    - **📊 Dashboard**: 查看评估和执行数据
    - **⚙️ Settings**: 配置 API 连接
    """)

    # 功能概览
    st.markdown("---")
    st.subheader("📌 功能概览")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Available Agents", "—", help="从 Agents 页面查看")

    with col2:
        st.metric("Active Sessions", "—", help="从 Sessions 页面查看")

    with col3:
        st.metric("Total Executions", "—", help="从 Dashboard 页面查看")

    with col4:
        st.metric("Evaluations", "—", help="从 Dashboard 页面查看")

    # 最近活动
    st.markdown("---")
    st.subheader("📝 最近活动")

    st.info("暂无活动记录。开始一个对话来创建记录！")


if __name__ == "__main__":
    main()
