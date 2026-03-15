"""
Sessions Page - Manage persistent sessions
"""

import asyncio
import streamlit as st
from datetime import datetime


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
    st.title("📋 Sessions")

    # Actions
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("🔄 Refresh"):
            st.rerun()

    with col2:
        if st.button("➕ New Session"):
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

        # Display sessions
        for session in sessions:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

                session_id = session.get("session_id", "N/A")
                status = session.get("status", "unknown")
                agent_name = session.get("agent_name", "Unknown")

                with col1:
                    st.markdown(f"**Session:** `{session_id[:8]}...`")
                    st.markdown(f"**Agent:** {agent_name}")

                with col2:
                    # Status badge
                    status_colors = {
                        "running": "🟢",
                        "idle": "🔵",
                        "suspended": "🟡",
                        "completed": "⚪",
                        "failed": "🔴",
                    }
                    status_icon = status_colors.get(status, "⚪")
                    st.markdown(f"{status_icon} {status.capitalize()}")

                with col3:
                    if status == "idle" or status == "running":
                        if st.button(
                            "⏸️ Suspend",
                            key=f"suspend_{session_id}",
                            use_container_width=True,
                        ):
                            try:
                                run_async(client.suspend_session(session_id))
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

                with col4:
                    if status == "suspended":
                        if st.button(
                            "▶️ Resume",
                            key=f"resume_{session_id}",
                            use_container_width=True,
                        ):
                            try:
                                run_async(client.resume_session(session_id))
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

                    if st.button(
                        "🗑️ Delete",
                        key=f"delete_{session_id}",
                        use_container_width=True,
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
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.markdown(f"**Session:** `{session['session_id']}`")
                    st.markdown(f"**Agent:** {session['agent_name']}")

                with col2:
                    status = session["status"]
                    status_colors = {
                        "running": "🟢",
                        "idle": "🔵",
                        "suspended": "🟡",
                    }
                    st.markdown(f"{status_colors.get(status, '⚪')} {status.capitalize()}")

                with col3:
                    if st.button(
                        "💬 Continue",
                        key=f"cont_{session['session_id']}",
                        use_container_width=True,
                    ):
                        st.session_state.current_session_id = session["session_id"]
                        st.rerun()

                st.markdown("---")
