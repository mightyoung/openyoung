"""
Settings Page - Configure WebUI settings
"""

import os
import streamlit as st
from webui.utils.config import config


def render():
    """Render settings page"""
    st.title("⚙️ Settings")

    # API Configuration
    st.markdown("### API Configuration")

    api_url = st.text_input(
        "API Base URL",
        value=config.API_BASE_URL,
        help="The base URL of the OpenYoung API server",
    )

    api_key = st.text_input(
        "API Key",
        value=config.API_KEY,
        type="password",
        help="Your API key for authentication",
    )

    if st.button("Save API Settings"):
        # In production, save to session state or environment
        st.success("API settings saved!")
        st.session_state.api_base_url = api_url
        st.session_state.api_key = api_key

    st.markdown("---")

    # Chat Settings
    st.markdown("### Chat Settings")

    typing_speed = st.slider(
        "Typing Speed (seconds per character)",
        min_value=0.01,
        max_value=0.1,
        value=config.TYPING_SPEED,
        step=0.01,
        help="Controls the speed of the typing animation",
    )

    max_messages = st.number_input(
        "Max Messages in History",
        min_value=10,
        max_value=500,
        value=config.MAX_MESSAGES,
        step=10,
        help="Maximum number of messages to keep in chat history",
    )

    st.markdown("---")

    # About
    st.markdown("### About")

    st.markdown("""
    **OpenYoung WebUI**

    Version: 0.1.0 (MVP)

    A web interface for the OpenYoung AI Agent platform.

    Based on:
    - [LangChain Streamlit Agent](https://github.com/langchain-ai/streamlit-agent)
    - [CrewAI Streamlit UI](https://github.com/crewAIInc/crewai_flows_streamlit_ui)
    """)

    # Links
    st.markdown("### Links")
    st.markdown("- [GitHub](https://github.com/your-repo)")
    st.markdown("- [Documentation](https://docs.openyoung.dev)")
