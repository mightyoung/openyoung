"""
Settings Page - 设置页面
配置 API 连接和其他选项
"""

import asyncio

import streamlit as st

# 页面配置
st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

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
        st.page_link("pages/1_Agents.py", label="🤖 Agents")
        st.page_link("pages/2_Chat.py", label="💬 Chat")
        st.page_link("pages/3_Sessions.py", label="📋 Sessions")
        st.page_link("pages/4_Dashboard.py", label="📊 Dashboard")


async def test_connection(base_url: str, api_key: str) -> tuple[bool, str]:
    """测试 API 连接"""
    client = APIClient(base_url, api_key)
    try:
        healthy = await client.health_check()
        await client.close()
        return healthy, "Connected successfully" if healthy else "API returned unhealthy"
    except Exception as e:
        await client.close()
        return False, str(e)


def main():
    """主函数"""
    st.title("⚙️ Settings")

    render_sidebar()

    # API 配置
    st.header("🔌 API Configuration")

    with st.form("api_config"):
        col1, col2 = st.columns(2)

        with col1:
            api_url = st.text_input(
                "API Base URL", value=config.API_BASE_URL, help="OpenYoung API 服务器地址"
            )

        with col2:
            api_key = st.text_input(
                "API Key", value=config.API_KEY, type="password", help="API 认证密钥"
            )

        submitted = st.form_submit_button("💾 Save")

        if submitted:
            st.success("Settings saved (session only)")
            st.session_state.api_url = api_url
            st.session_state.api_key = api_key

    # 测试连接
    st.subheader("🔍 Connection Test")

    if st.button("Test Connection"):
        with st.spinner("Testing connection..."):
            healthy, message = asyncio.run(
                test_connection(
                    st.session_state.get("api_url", config.API_BASE_URL),
                    st.session_state.get("api_key", config.API_KEY),
                )
            )

        if healthy:
            st.success(f"✅ {message}")
        else:
            st.error(f"❌ {message}")

    st.markdown("---")

    # 显示当前配置
    st.header("📋 Current Configuration")

    st.write(f"**API Base URL**: `{config.API_BASE_URL}`")
    st.write(f"**API Key**: `{'*' * len(config.API_KEY) if config.API_KEY else '(not set)'}`")

    st.markdown("---")

    # 关于
    st.header("ℹ️ About")

    st.markdown("""
    **OpenYoung WebUI**

    - Version: 1.0.0
    - Framework: Streamlit
    - Backend: FastAPI

    查看文档: [GitHub](https://github.com/ruvnet/openyoung)
    """)


if __name__ == "__main__":
    main()
