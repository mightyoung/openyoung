"""
Chat Page - Main conversation interface

Based on LangChain streamlit-agent patterns:
- https://github.com/langchain-ai/streamlit-agent/blob/main/streamlit_agent/basic_streaming.py
- https://github.com/langchain-ai/streamlit-agent/blob/main/streamlit_agent/basic_memory.py
"""

import asyncio

import streamlit as st

from webui.components.ui.chat_bubble import render_chat_bubble, render_message_list
from webui.utils.config import config


def run_async(coro):
    """Run async coroutine in Streamlit"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Create a new loop in a thread
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return asyncio.run(coro)
    except Exception:
        return asyncio.run(coro)


def render():
    """Render chat page"""
    st.title("💬 Chat")

    # Agent selector
    with st.expander("Agent Settings", expanded=False):
        agent_name = st.text_input(
            "Agent Name",
            value=st.session_state.get("current_agent", "default"),
            help="Enter the agent name to use for this conversation",
        )
        if agent_name != st.session_state.get("current_agent"):
            st.session_state.current_agent = agent_name

    st.markdown("---")

    # Display chat history using design system
    render_message_list(st.session_state.messages, show_timestamps=False)

    # Chat input
    if prompt := st.chat_input("Message your agent..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Render user message with design system
        render_chat_bubble(role="user", content=prompt)

        # Get response
        with st.chat_message("assistant"):
            placeholder = st.empty()

            try:
                # Get API client
                client = st.session_state.api_client
                agent = st.session_state.current_agent or "default"

                # Create session if not exists
                if not st.session_state.current_session_id:
                    # Create a new session
                    session = run_async(client.create_session(agent_name=agent))
                    st.session_state.current_session_id = session.get("session_id")

                # Send message with streaming
                session_id = st.session_state.current_session_id

                # Use streaming response
                full_response = ""
                placeholder.markdown("▌")

                try:
                    # Get the async generator
                    stream_gen = run_async(client.send_message_stream(session_id, prompt))

                    # Process the stream
                    for chunk in stream_gen:
                        full_response += chunk
                        placeholder.markdown(full_response + "▌")

                    placeholder.markdown(full_response)

                except Exception as e:
                    st.error(f"Streaming error: {str(e)}, falling back to non-streaming")
                    # Fallback to non-streaming
                    result = run_async(client.send_message(session_id, prompt))
                    full_response = result.get("response", "")

                    # Display with typing effect
                    displayed = ""
                    for char in full_response:
                        displayed += char
                        placeholder.markdown(displayed + "▌")

                    placeholder.markdown(full_response)

            except Exception as e:
                st.error(f"Error: {str(e)}")
                full_response = f"抱歉，发生错误: {str(e)}"

        # Add assistant response
        st.session_state.messages.append({"role": "assistant", "content": full_response})


# Import for type hints
from webui.services.api_client import APIClient
