"""
Agents Page - 可用 Agent 列表页面
"""

import asyncio

import streamlit as st

# 页面配置
st.set_page_config(page_title="Agents", page_icon="🤖", layout="wide")

# 导入服务
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from webui.services.api_client import APIClient
from webui.utils.config import config


def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.title(f"{config.PAGE_ICON} OpenYoung")
        st.divider()
        st.page_link("app.py", label="🏠 Home")
        st.page_link("pages/2_Chat.py", label="💬 Chat")
        st.page_link("pages/3_Sessions.py", label="📋 Sessions")
        st.page_link("pages/4_Dashboard.py", label="📊 Dashboard")
        st.page_link("pages/5_Settings.py", label="⚙️ Settings")


def render_agent_card(agent: dict):
    """渲染 Agent 卡片"""
    with st.container():
        col1, col2 = st.columns([3, 1])

        with col1:
            st.subheader(agent.get("name", "Unknown Agent"))
            st.write(agent.get("description", "No description"))

            # 标签
            tags = agent.get("tags", [])
            if tags:
                st.write(" ".join([f":blue[{tag}]" for tag in tags[:3]]))

        with col2:
            # 徽章
            if agent.get("verified"):
                st.success("✅ Verified")
            if agent.get("top_rated"):
                st.star("⭐ Top Rated")

            # 操作按钮
            if st.button("💬 Chat", key=f"chat_{agent.get('id')}", use_container_width=True):
                # 设置当前 Agent 并跳转到聊天页面
                st.session_state.target_agent = agent.get("id")
                st.session_state.target_agent_name = agent.get("name")
                st.switch_page("2_💬_Chat.py")

        st.divider()


async def load_agents(search: str = None):
    """加载 Agent 列表"""
    client = APIClient(config.API_BASE_URL, config.API_KEY)
    try:
        agents = await client.list_agents(search=search)
        await client.close()
        return agents
    except Exception as e:
        await client.close()
        st.error(f"Failed to load agents: {str(e)}")
        return []


def main():
    """主函数"""
    st.title("🤖 Available Agents")

    render_sidebar()

    # 搜索栏
    search_query = st.text_input(
        "🔍 Search agents", placeholder="Describe what you need...", key="agent_search"
    )

    # 加载 Agent
    if "agents" not in st.session_state:
        with st.spinner("Loading agents..."):
            agents = asyncio.run(load_agents(search_query))
            st.session_state.agents = agents
    else:
        agents = st.session_state.agents

    # 过滤搜索
    if search_query:
        filtered_agents = [
            a
            for a in agents
            if search_query.lower() in a.get("name", "").lower()
            or search_query.lower() in a.get("description", "").lower()
        ]
    else:
        filtered_agents = agents

    # 显示 Agent 列表
    if not filtered_agents:
        st.info("No agents found")
        if st.button("🔄 Refresh"):
            st.session_state.pop("agents", None)
            st.rerun()
    else:
        st.write(f"Found **{len(filtered_agents)}** agents")

        for agent in filtered_agents:
            render_agent_card(agent)


if __name__ == "__main__":
    main()
