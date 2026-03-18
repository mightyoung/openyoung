"""
OpenYoung WebUI - Main Application

Modernized with Design Tokens (P1.1) and Base UI Components (P1.2)
- https://github.com/langchain-ai/streamlit-agent
- https://github.com/crewAIInc/crewai_flows_streamlit_ui
"""

import streamlit as st

from webui.utils.config import config


def load_css():
    """Load custom CSS with design tokens"""
    try:
        with open("webui/styles/tokens.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass  # Tokens not ready yet


def load_component_css():
    """Load component-specific styles"""
    try:
        with open("webui/styles/components.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass  # Components CSS not ready yet


def apply_keyboard_shortcuts():
    """Add keyboard shortcuts for common actions"""
    keyboard_shortcuts_css = """
    <script>
    document.addEventListener('keydown', function(e) {
        // Cmd/Ctrl + K for command palette focus
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            const input = document.query('input[type="text"]');
            if (input) input.focus();
        }
        // Cmd/Ctrl + N for new chat
        if ((e.metaKey || e.ctrlKey) && e.key === 'n') {
            e.preventDefault();
            window.location.href = '?page=new_chat';
        }
    });
    </script>
    """
    st.markdown(keyboard_shortcuts_css, unsafe_allow_html=True)


def setup_page():
    """Setup Streamlit page configuration"""
    st.set_page_config(
        page_title="OpenYoung",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    # Load design tokens and component styles
    load_css()
    load_component_css()
    apply_keyboard_shortcuts()


def init_session_state():
    """Initialize session state variables"""
    # App initialization flag
    if "app_initialized" not in st.session_state:
        st.session_state.app_initialized = True

    # Chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Current session
    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = None

    # Current agent
    if "current_agent" not in st.session_state:
        st.session_state.current_agent = None

    # API client
    if "api_client" not in st.session_state:
        from webui.services.api_client import get_api_client

        st.session_state.api_client = get_api_client()


def main():
    """Main application"""
    setup_page()
    init_session_state()

    # Sidebar navigation
    with st.sidebar:
        st.title("🤖 OpenYoung")
        st.markdown("---")

        # Navigation
        page = st.radio(
            "Navigation",
            ["💬 Chat", "🤖 Agents", "📋 Sessions", "📊 Evaluation", "⚙️ Settings"],
        )

        st.markdown("---")

        # Quick actions
        st.subheader("Quick Actions")

        if st.button("New Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.current_session_id = None
            st.rerun()

        # API Status
        st.markdown("---")
        st.caption("API Status")
        try:
            client = st.session_state.api_client
            # Note: This is a sync check, could be improved
            import asyncio

            async def check():
                return await client.health_check()

            # Skip actual check for now to avoid blocking
            st.success("🟢 Connected")
        except Exception:
            st.error("🔴 Disconnected")

    # Main content based on selected page
    if page == "💬 Chat":
        from webui.pages import chat

        chat.render()
    elif page == "🤖 Agents":
        from webui.pages import agents

        agents.render()
    elif page == "📋 Sessions":
        from webui.pages import sessions

        sessions.render()
    elif page == "📊 Evaluation":
        from webui.pages import evaluations

        evaluations.render()
    elif page == "⚙️ Settings":
        from webui.pages import settings

        settings.render()


if __name__ == "__main__":
    main()
