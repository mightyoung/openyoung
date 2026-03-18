"""Card Component - Compound component pattern"""
import streamlit as st


def render_card(title: str, description: str = None, **kwargs):
    """Render a card with title and description.

    Args:
        title: The card title
        description: Optional description text
        **kwargs: Additional content key-value pairs to render
    """
    with st.container():
        st.markdown(f"### {title}")
        if description:
            st.caption(description)
        # Content area
        for key, value in kwargs.items():
            st.markdown(f"**{key}**: {value}")


def render_card_expanded(title: str, description: str = None, border: bool = True, **kwargs):
    """Render an expanded card with more styling options.

    Args:
        title: The card title
        description: Optional description text
        border: Whether to show border (default True)
        **kwargs: Additional content key-value pairs to render
    """
    card_class = "card" if border else ""

    with st.container():
        if border:
            st.markdown("<div style='border: 1px solid var(--border); border-radius: var(--radius-lg); padding: var(--space-4);'>", unsafe_allow_html=True)

        st.markdown(f"**{title}**")
        if description:
            st.markdown(f"<small style='color: var(--foreground-muted);'>{description}</small>", unsafe_allow_html=True)

        # Content area
        for key, value in kwargs.items():
            st.markdown(f"**{key}**: {value}")

        if border:
            st.markdown("</div>", unsafe_allow_html=True)
