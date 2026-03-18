"""Metric Card Component with trend indicator"""
import streamlit as st
from typing import Optional, Union


def render_metric_card(
    label: str,
    value: Union[str, float, int],
    delta: Optional[float] = None,
    help_text: Optional[str] = None,
    **kwargs
):
    """Render a metric card with optional trend delta.

    Args:
        label: Metric label
        value: Metric value (displayed prominently)
        delta: Optional trend indicator (positive/negative change)
        help_text: Optional help text tooltip
        **kwargs: Additional metadata key-value pairs to display
    """
    col1, col2 = st.columns([2, 1])
    with col1:
        st.metric(
            label=label,
            value=value,
            delta=delta,
            help=help_text
        )

    # Additional info from kwargs
    if kwargs:
        with col2:
            for key, val in kwargs.items():
                st.caption(f"{key}: {val}")


def render_metric_grid(metrics: list[dict], columns: int = 3):
    """Render a grid of metric cards.

    Args:
        metrics: List of metric dictionaries with keys: label, value, delta, help_text
        columns: Number of columns in the grid (default 3)

    Example:
        metrics = [
            {"label": "Total Users", "value": "1,234", "delta": 12.5},
            {"label": "Active Sessions", "value": 89, "delta": -5.2},
            {"label": "Revenue", "value": "$12,345", "delta": 8.1},
        ]
        render_metric_grid(metrics)
    """
    cols = st.columns(columns)

    for i, metric in enumerate(metrics):
        with cols[i % columns]:
            render_metric_card(
                label=metric.get("label", ""),
                value=metric.get("value", ""),
                delta=metric.get("delta"),
                help_text=metric.get("help_text"),
                **metric.get("kwargs", {})
            )


def render_stat_card(
    label: str,
    value: Union[str, float, int],
    icon: Optional[str] = None,
    description: Optional[str] = None,
    trend: Optional[str] = None,
    trend_value: Optional[float] = None,
):
    """Render a stat card with more customization options.

    Args:
        label: Card label
        value: The main value to display
        icon: Optional emoji icon
        description: Optional description text
        trend: Trend direction ("up", "down", "neutral")
        trend_value: Optional numeric trend value
    """
    with st.container():
        # Icon and label
        if icon:
            st.markdown(f"{icon} **{label}**")
        else:
            st.markdown(f"**{label}**")

        # Value with trend
        if trend_value is not None:
            trend_icon = "↑" if trend == "up" else "↓" if trend == "down" else "→"
            trend_color = "green" if trend == "up" else "red" if trend == "down" else "gray"
            st.markdown(
                f"<span style='font-size: 1.5em;'>{value}</span> "
                f"<span style='color: {trend_color};'>{trend_icon} {abs(trend_value)}%</span>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(f"<span style='font-size: 1.5em;'>{value}</span>", unsafe_allow_html=True)

        # Description
        if description:
            st.caption(description)
