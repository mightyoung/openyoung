"""Chat Bubble Component for messages"""
import streamlit as st
from datetime import datetime
from typing import Optional, List, Dict


def render_chat_bubble(
    role: str,
    content: str,
    timestamp: Optional[datetime] = None,
    avatar: Optional[str] = None,
    **kwargs
):
    """Render a chat message bubble.

    Args:
        role: Message role ("user", "assistant", "system")
        content: Message content
        timestamp: Optional timestamp for the message
        avatar: Optional avatar emoji
        **kwargs: Additional metadata to display
    """
    # Map role to Streamlit's chat_message format
    role_map = {
        "user": "user",
        "assistant": "assistant",
        "bot": "assistant",
        "system": "assistant",
    }
    mapped_role = role_map.get(role, "assistant")

    with st.chat_message(mapped_role, avatar=avatar):
        st.markdown(content)
        if timestamp:
            st.caption(timestamp.strftime("%H:%M"))

        # Additional metadata
        for key, value in kwargs.items():
            st.caption(f"{key}: {value}")


def render_typing_indicator():
    """Render typing animation indicator."""
    with st.chat_message("assistant"):
        st.markdown("▌▌▌")


def render_message_list(messages: List[Dict], show_timestamps: bool = True):
    """Render a list of chat messages.

    Args:
        messages: List of message dictionaries with keys: role, content, timestamp
        show_timestamps: Whether to show timestamps

    Example:
        messages = [
            {"role": "user", "content": "Hello!", "timestamp": datetime.now()},
            {"role": "assistant", "content": "Hi there!", "timestamp": datetime.now()},
        ]
        render_message_list(messages)
    """
    for msg in messages:
        timestamp = msg.get("timestamp") if show_timestamps else None
        render_chat_bubble(
            role=msg.get("role", "assistant"),
            content=msg.get("content", ""),
            timestamp=timestamp,
            avatar=msg.get("avatar"),
        )


def render_loading_message(message: str = "Thinking..."):
    """Render a loading message with animation.

    Args:
        message: Loading message text
    """
    with st.chat_message("assistant"):
        # Simple animation using st.empty
        placeholder = st.empty()
        for i in range(4):
            dots = "." * (i + 1)
            placeholder.markdown(f"{message}{dots}")
            import time
            time.sleep(0.3)
        placeholder.empty()
