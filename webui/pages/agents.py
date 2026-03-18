"""
Agents Page - List and search available agents
"""
import asyncio

import streamlit as st

from webui.components.ui.card import render_card_expanded
from webui.components.ui.button import render_button


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
    st.title("Available Agents")

    # Custom CSS for agent cards
    st.markdown("""
        <style>
        .agent-card {
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: var(--space-4);
            margin-bottom: var(--space-4);
            background: var(--background);
            transition: box-shadow var(--duration-fast) var(--ease-default);
        }
        .agent-card:hover {
            box-shadow: var(--shadow-md);
        }
        .agent-name {
            font-size: var(--text-lg);
            font-weight: var(--weight-semibold);
            color: var(--foreground);
            margin-bottom: var(--space-1);
        }
        .agent-description {
            color: var(--foreground-muted);
            font-size: var(--text-sm);
            margin-bottom: var(--space-2);
        }
        .agent-badges {
            display: flex;
            gap: var(--space-2);
            flex-wrap: wrap;
            margin-top: var(--space-2);
        }
        .badge {
            background: var(--muted);
            color: var(--muted-foreground);
            padding: var(--space-1) var(--space-2);
            border-radius: var(--radius-full);
            font-size: var(--text-xs);
            font-weight: var(--weight-medium);
        }
        .badge-verified {
            background: var(--success-muted);
            color: var(--success);
        }
        .badge-top-rated {
            background: var(--accent-100);
            color: var(--accent-700);
        }
        .agent-actions {
            display: flex;
            gap: var(--space-2);
            margin-top: var(--space-3);
        }
        </style>
    """, unsafe_allow_html=True)

    # Search bar
    search_query = st.text_input(
        "Search Agents",
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
            agent_name = agent.get("name", "Unknown")
            agent_desc = agent.get("description", "No description")
            badges = agent.get("badges", [])

            # Render card with design system styling
            with st.container():
                render_card_expanded(
                    title=f"🤖 {agent_name}",
                    description=agent_desc,
                    border=True,
                )

                # Render badges if any
                if badges:
                    badge_html = '<div class="agent-badges">'
                    for b in badges:
                        badge_class = f"badge badge-{b}" if b in ("verified", "top-rated") else "badge"
                        badge_html += f'<span class="{badge_class}">{b}</span>'
                    badge_html += '</div>'
                    st.markdown(badge_html, unsafe_allow_html=True)

                # Display metadata in expander
                if agent.get("metadata"):
                    with st.expander("Details"):
                        for key, value in agent.get("metadata", {}).items():
                            st.markdown(f"**{key}**: {value}")

                # Action buttons
                col1, col2 = st.columns([1, 1])
                with col1:
                    if render_button(
                        "💬 Chat",
                        variant="primary",
                        key=f"chat_{agent_name}",
                        use_container_width=True,
                    ):
                        st.session_state.current_agent = agent_name
                        st.session_state.messages = []
                        st.session_state.current_session_id = None
                        st.rerun()

                with col2:
                    if render_button(
                        "ℹ️ Info",
                        variant="outline",
                        key=f"info_{agent_name}",
                        use_container_width=True,
                    ):
                        st.session_state.selected_agent = agent_name
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
            agent_name = agent["name"]
            agent_desc = agent["description"]
            badges = agent.get("badges", [])

            with st.container():
                render_card_expanded(
                    title=f"🤖 {agent_name}",
                    description=agent_desc,
                    border=True,
                )

                if badges:
                    badge_html = '<div class="agent-badges">'
                    for b in badges:
                        badge_class = f"badge badge-{b}" if b in ("verified", "top-rated") else "badge"
                        badge_html += f'<span class="{badge_class}">{b}</span>'
                    badge_html += '</div>'
                    st.markdown(badge_html, unsafe_allow_html=True)

                col1, col2 = st.columns([1, 1])
                with col1:
                    if render_button(
                        "💬 Chat",
                        variant="primary",
                        key=f"demo_{agent_name}",
                        use_container_width=True,
                    ):
                        st.session_state.current_agent = agent_name
                        st.session_state.messages = []
                        st.rerun()

                st.markdown("---")
