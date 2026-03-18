"""
Sessions Page - Manage persistent sessions
"""

import asyncio
from datetime import datetime

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
    """Render sessions page"""
    st.title("Sessions")

    # Apply title styling
    st.markdown("""
        <style>
        .sessions-title {
            font-size: var(--text-2xl);
            font-weight: var(--weight-semibold);
            color: var(--foreground);
            margin-bottom: var(--space-6);
        }
        </style>
    """, unsafe_allow_html=True)

    # Actions row
    col1, col2 = st.columns([1, 1])

    with col1:
        if render_button("Refresh", variant="outline", key="refresh_sessions"):
            st.rerun()

    with col2:
        if render_button("New Session", variant="primary", key="new_session"):
            st.session_state.messages = []
            st.session_state.current_session_id = None
            st.rerun()

    st.markdown("---")

    # Fetch sessions
    try:
        client = st.session_state.api_client
        sessions = run_async(client.list_sessions())

        if not sessions:
            st.info("No active sessions. Start a new conversation to create one.")
            return

        # Display sessions as cards
        for session in sessions:
            session_id = session.get("session_id", "N/A")
            status = session.get("status", "unknown")
            agent_name = session.get("agent_name", "Unknown")

            # Status display
            status_colors = {
                "running": "🟢",
                "idle": "🔵",
                "suspended": "🟡",
                "completed": "⚪",
                "failed": "🔴",
            }
            status_icon = status_colors.get(status, "⚪")
            status_display = f"{status_icon} {status.capitalize()}"

            # Render session card
            render_card_expanded(
                title=f"Session: `{session_id[:8]}...`",
                description=f"Agent: {agent_name} | Status: {status_display}",
                border=True,
                SessionID=session_id,
                Agent=agent_name,
                Status=status.capitalize(),
            )

            # Action buttons row
            action_cols = st.columns([1, 1, 1])
            with action_cols[0]:
                if status in ("idle", "running"):
                    if render_button(
                        "Suspend",
                        variant="outline",
                        key=f"suspend_{session_id}",
                    ):
                        try:
                            run_async(client.suspend_session(session_id))
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

            with action_cols[1]:
                if status == "suspended":
                    if render_button(
                        "Resume",
                        variant="primary",
                        key=f"resume_{session_id}",
                    ):
                        try:
                            run_async(client.resume_session(session_id))
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

            with action_cols[2]:
                if render_button(
                    "Delete",
                    variant="ghost",
                    key=f"delete_{session_id}",
                ):
                    try:
                        run_async(client.delete_session(session_id))
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

            st.markdown("---")

    except Exception as e:
        st.error(f"Error loading sessions: {str(e)}")

        # Demo sessions for UI demo
        st.markdown("### Demo Sessions")
        demo_sessions = [
            {"session_id": "demo-001", "status": "running", "agent_name": "default coder"},
            {"session_id": "demo-002", "status": "idle", "agent_name": "default reviewer"},
            {"session_id": "demo-003", "status": "suspended", "agent_name": "default tester"},
        ]

        for session in demo_sessions:
            status = session["status"]
            status_colors = {
                "running": "🟢",
                "idle": "🔵",
                "suspended": "🟡",
            }
            status_display = f"{status_colors.get(status, '⚪')} {status.capitalize()}"

            render_card_expanded(
                title=f"Session: `{session['session_id']}`",
                description=f"Agent: {session['agent_name']} | Status: {status_display}",
                border=True,
                SessionID=session["session_id"],
                Agent=session["agent_name"],
                Status=status.capitalize(),
            )

            if render_button(
                "Continue",
                variant="primary",
                key=f"cont_{session['session_id']}",
            ):
                st.session_state.current_session_id = session["session_id"]
                st.rerun()

            st.markdown("---")
