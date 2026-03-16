"""
Agents Page - List and search available agents
"""

import asyncio

import streamlit as st


def run_async(coro):
    """Run async coroutine in Streamlit"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return asyncio.run(coro)
    except Exception:
        return asyncio.run(coro)


def render():
    """Render agents page"""
    st.title("🤖 Available Agents")

    # Search bar
    search_query = st.text_input(
        "🔍 Search Agents",
        placeholder="Describe what you need...",
        help="Search agents by description or capability",
    )

    st.markdown("---")

    # Fetch agents
    try:
        client = st.session_state.api_client

        with st.spinner("Loading agents..."):
            agents = run_async(client.list_agents(search=search_query))

        if not agents:
            st.info("No agents found. Try a different search query.")
            return

        # Display agents in cards
        for agent in agents:
            with st.container():
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.subheader(f"🤖 {agent.get('name', 'Unknown')}")
                    st.markdown(agent.get("description", "No description"))

                    # Display badges if any
                    if agent.get("badges"):
                        badges = agent.get("badges", [])
                        badge_text = " ".join([f"`{b}`" for b in badges])
                        st.markdown(badge_text)

                    # Display metadata
                    if agent.get("metadata"):
                        with st.expander("Details"):
                            for key, value in agent.get("metadata", {}).items():
                                st.markdown(f"**{key}**: {value}")

                with col2:
                    # Start chat with this agent
                    if st.button(
                        "💬 Chat",
                        key=f"chat_{agent.get('name')}",
                        use_container_width=True,
                    ):
                        st.session_state.current_agent = agent.get("name")
                        # Clear messages for new conversation
                        st.session_state.messages = []
                        st.session_state.current_session_id = None
                        st.rerun()

                    if st.button(
                        "ℹ️ Info",
                        key=f"info_{agent.get('name')}",
                        use_container_width=True,
                    ):
                        # Could open a modal or navigate to detail page
                        st.session_state.selected_agent = agent.get("name")
                        st.rerun()

                st.markdown("---")

    except Exception as e:
        st.error(f"Error loading agents: {str(e)}")

        # Show fallback - mock data for demo
        st.markdown("### Demo Agents")
        demo_agents = [
            {
                "name": "default coder",
                "description": "General-purpose coding assistant",
                "badges": ["verified"],
            },
            {
                "name": "default reviewer",
                "description": "Code review specialist",
                "badges": ["top-rated"],
            },
            {
                "name": "default tester",
                "description": "Test generation and execution",
            },
        ]

        for agent in demo_agents:
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader(f"🤖 {agent['name']}")
                    st.markdown(agent["description"])
                    if agent.get("badges"):
                        st.markdown(" ".join([f"`{b}`" for b in agent["badges"]]))
                with col2:
                    if st.button(
                        "💬 Chat",
                        key=f"demo_{agent['name']}",
                        use_container_width=True,
                    ):
                        st.session_state.current_agent = agent["name"]
                        st.session_state.messages = []
                        st.rerun()
                st.markdown("---")
