"""
Settings Page - 设置页面
配置 API 连接和其他选项，支持YAML持久化
"""

import asyncio
import os
from pathlib import Path

import streamlit as st
import yaml

# 页面配置
st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

# 导入服务
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from webui.services.api_client import APIClient
from webui.utils.config import config

# 配置文件路径
CONFIG_DIR = Path.home() / ".openyoung"
CONFIG_FILE = CONFIG_DIR / "settings.yaml"


def load_settings() -> dict:
    """加载YAML配置文件"""
    if CONFIG_FILE.exists():
        try:
            return yaml.safe_load(CONFIG_FILE.read_text()) or {}
        except Exception:
            return {}
    return {}


def save_settings(settings: dict) -> bool:
    """保存设置到YAML文件"""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(yaml.dump(settings, default_flow_style=False))
        return True
    except Exception as e:
        st.error(f"Failed to save: {e}")
        return False


def get_env_list() -> list:
    """获取环境列表"""
    return ["development", "staging", "production"]


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

    # 标签页: API配置 | 环境管理 | 多Provider
    tab1, tab2, tab3 = st.tabs(["🔌 API Config", "🌍 Environments", "🔗 Providers"])

    with tab1:
        # 加载现有配置
        saved_settings = load_settings()

        st.header("API Configuration")

        with st.form("api_config"):
            col1, col2 = st.columns(2)

            with col1:
                api_url = st.text_input(
                    "API Base URL",
                    value=saved_settings.get("api_url", config.API_BASE_URL),
                    help="OpenYoung API 服务器地址",
                )

            with col2:
                api_key = st.text_input(
                    "API Key",
                    value=saved_settings.get("api_key", config.API_KEY),
                    type="password",
                    help="API 认证密钥",
                )

            submitted = st.form_submit_button("💾 Save to YAML")

            if submitted:
                settings = load_settings()
                settings["api_url"] = api_url
                settings["api_key"] = api_key
                if save_settings(settings):
                    st.success(f"Settings saved to {CONFIG_FILE}")

        # 测试连接
        st.subheader("🔍 Connection Test")

        if st.button("Test Connection"):
            with st.spinner("Testing connection..."):
                healthy, message = asyncio.run(
                    test_connection(
                        api_url,
                        api_key,
                    )
                )

            if healthy:
                st.success(f"✅ {message}")
            else:
                st.error(f"❌ {message}")

    with tab2:
        st.header("Environment Management")

        # 环境选择
        current_env = saved_settings.get("environment", "development")
        env_options = get_env_list()

        col1, col2 = st.columns([1, 2])

        with col1:
            selected_env = st.selectbox(
                "Current Environment",
                env_options,
                index=env_options.index(current_env) if current_env in env_options else 0,
            )

        with col2:
            if st.button("Switch Environment"):
                settings = load_settings()
                settings["environment"] = selected_env
                if save_settings(settings):
                    st.success(f"Switched to {selected_env}")

        # 环境详情
        st.subheader(f"📝 {selected_env.title()} Config")

        env_settings = saved_settings.get("environments", {}).get(selected_env, {})

        with st.form(f"env_config_{selected_env}"):
            env_url = st.text_input(
                "API URL",
                value=env_settings.get("api_url", ""),
                placeholder="https://api.example.com",
            )
            env_key = st.text_input(
                "API Key",
                value=env_settings.get("api_key", ""),
                type="password",
                placeholder="Your API key",
            )

            if st.form_submit_button("Save Environment"):
                settings = load_settings()
                if "environments" not in settings:
                    settings["environments"] = {}
                settings["environments"][selected_env] = {
                    "api_url": env_url,
                    "api_key": env_key,
                }
                if save_settings(settings):
                    st.success(f"Saved {selected_env} config")

    with tab3:
        st.header("Provider Management")

        # Provider列表
        providers = saved_settings.get("providers", {})

        # 添加新Provider
        with st.expander("➕ Add New Provider"):
            with st.form("add_provider"):
                provider_name = st.text_input("Provider Name", placeholder="my-provider")
                provider_type = st.selectbox("Type", ["openai", "anthropic", "azure", "custom"])
                provider_url = st.text_input("API URL", placeholder="https://api.example.com/v1")
                provider_key = st.text_input("API Key", type="password")

                if st.form_submit_button("Add Provider"):
                    settings = load_settings()
                    if "providers" not in settings:
                        settings["providers"] = {}
                    settings["providers"][provider_name] = {
                        "type": provider_type,
                        "api_url": provider_url,
                        "api_key": provider_key,
                    }
                    if save_settings(settings):
                        st.success(f"Provider {provider_name} added")
                        st.rerun()

        # 显示Provider列表
        st.subheader("📋 Registered Providers")

        if not providers:
            st.info("No providers configured")
        else:
            for name, details in providers.items():
                with st.expander(f"🔗 {name}"):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.write(f"**Type**: {details.get('type', 'N/A')}")
                        st.write(f"**URL**: {details.get('api_url', 'N/A')}")

                    with col2:
                        if st.button("🗑️ Delete", key=f"del_{name}"):
                            settings = load_settings()
                            if name in settings.get("providers", {}):
                                del settings["providers"][name]
                                save_settings(settings)
                                st.rerun()

    st.markdown("---")

    # 显示当前配置
    st.header("📋 Current Configuration")

    st.write(f"**Config File**: `{CONFIG_FILE}`")
    st.write(f"**API Base URL**: `{saved_settings.get('api_url', config.API_BASE_URL)}`")
    st.write(f"**Environment**: `{saved_settings.get('environment', 'development')}`")

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
