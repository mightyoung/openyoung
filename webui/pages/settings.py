"""Settings Page - Configure WebUI settings"""

import streamlit as st

from webui.components.ui.button import render_button
from webui.components.ui.card import render_card_expanded
from webui.utils.config import config


def render():
    """Render settings page."""
    st.title("Settings")

    # API Configuration
    with st.container():
        render_card_expanded(
            title="API Configuration",
            description="Configure your OpenYoung API connection",
            border=True,
        )

        api_url = st.text_input(
            "API Base URL",
            value=config.API_BASE_URL,
            help="The base URL of the OpenYoung API server",
            key="api_base_url",
        )

        api_key = st.text_input(
            "API Key",
            value=config.API_KEY,
            type="password",
            help="Your API key for authentication",
            key="api_key",
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            save_api = render_button("Save API Settings", variant="primary", key="save_api_btn")
        with col2:
            reset_api = render_button("Reset", variant="outline", key="reset_api_btn")

        if save_api:
            st.session_state.api_base_url = api_url
            st.session_state.api_key = api_key
            st.success("API settings saved!")

        if reset_api:
            st.rerun()

    st.markdown("")

    # Chat Settings
    with st.container():
        render_card_expanded(
            title="Chat Settings",
            description="Configure chat behavior and appearance",
            border=True,
        )

        typing_speed = st.slider(
            "Typing Speed (seconds per character)",
            min_value=0.01,
            max_value=0.1,
            value=config.TYPING_SPEED,
            step=0.01,
            help="Controls the speed of the typing animation",
            key="typing_speed",
        )

        max_messages = st.number_input(
            "Max Messages in History",
            min_value=10,
            max_value=500,
            value=config.MAX_MESSAGES,
            step=10,
            help="Maximum number of messages to keep in chat history",
            key="max_messages",
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            save_chat = render_button("Save Chat Settings", variant="primary", key="save_chat_btn")
        with col2:
            reset_chat = render_button("Reset", variant="outline", key="reset_chat_btn")

        if save_chat:
            st.session_state.typing_speed = typing_speed
            st.session_state.max_messages = max_messages
            st.success("Chat settings saved!")

        if reset_chat:
            st.rerun()

    st.markdown("")

    # About
    with st.container():
        render_card_expanded(
            title="About",
            description="OpenYoung WebUI v0.1.0 (MVP)",
            border=True,
        )

        st.markdown("""
        **OpenYoung WebUI**

        A web interface for the OpenYoung AI Agent platform.

        Built with Streamlit and powered by modern design tokens.

        Based on:
        - [LangChain Streamlit Agent](https://github.com/langchain-ai/streamlit-agent)
        - [CrewAI Streamlit UI](https://github.com/crewAIInc/crewai_flows_streamlit_ui)
        """)

    st.markdown("")

    # Links
    with st.container():
        render_card_expanded(
            title="Links",
            description="Useful resources and documentation",
            border=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("- [GitHub](https://github.com/your-repo)")
        with col2:
            st.markdown("- [Documentation](https://docs.openyoung.dev)")
