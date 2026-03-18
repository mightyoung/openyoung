"""Button Component with variants"""
import streamlit as st
from typing import Optional, Callable


def render_button(
    label: str,
    variant: str = "primary",
    disabled: bool = False,
    on_click: Optional[Callable] = None,
    key: Optional[str] = None,
    **kwargs
):
    """Render a button with variant support.

    Args:
        label: Button text label
        variant: Button style variant (primary, secondary, outline, ghost)
        disabled: Whether the button is disabled
        on_click: Callback function when button is clicked
        key: Optional unique key for the button
        **kwargs: Additional Streamlit button parameters
    """
    button_types = {
        "primary": "primary",
        "secondary": "secondary",
        "outline": "secondary",  # Streamlit uses secondary for outlined look
        "ghost": "secondary",    # Streamlit uses secondary for ghost look
    }

    button_type = button_types.get(variant, "primary")

    # Map variant to CSS class for custom styling
    variant_class = f"button-{variant}"

    # Custom CSS for button variants
    if variant == "outline":
        st.markdown("""
        <style>
        div.stButton > button[kind="secondary"] {
            border: 1px solid var(--border);
            background: transparent;
        }
        </style>
        """, unsafe_allow_html=True)
    elif variant == "ghost":
        st.markdown("""
        <style>
        div.stButton > button[kind="secondary"] {
            border: none;
            background: transparent;
        }
        </style>
        """, unsafe_allow_html=True)

    return st.button(
        label,
        type=button_type,
        disabled=disabled,
        on_click=on_click,
        key=key,
        **kwargs
    )


def render_icon_button(
    icon: str,
    label: str = "",
    variant: str = "ghost",
    disabled: bool = False,
    on_click: Optional[Callable] = None,
    key: Optional[str] = None,
    **kwargs
):
    """Render an icon button.

    Args:
        icon: Icon emoji or text (e.g., "🔗", "×")
        label: Optional label for accessibility
        variant: Button style variant
        disabled: Whether the button is disabled
        on_click: Callback function when button is clicked
        key: Optional unique key for the button
        **kwargs: Additional Streamlit button parameters
    """
    button_label = f"{icon} {label}".strip()
    return render_button(
        label=button_label,
        variant=variant,
        disabled=disabled,
        on_click=on_click,
        key=key,
        **kwargs
    )
