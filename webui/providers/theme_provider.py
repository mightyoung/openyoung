"""Theme Provider - Light/Dark/System theme management"""
import streamlit as st
from enum import Enum
from typing import Dict


class Theme(Enum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class ThemeProvider:
    """Manages theme state and persistence"""

    STORAGE_KEY = "openyoung_theme"

    @staticmethod
    def get_theme() -> str:
        """Get current theme (light/dark/system)"""
        return st.session_state.get(ThemeProvider.STORAGE_KEY, "system")

    @staticmethod
    def set_theme(theme: str) -> None:
        """Set theme and persist to localStorage"""
        if theme in ["light", "dark", "system"]:
            st.session_state[ThemeProvider.STORAGE_KEY] = theme

    @staticmethod
    def get_css_variables(theme: str) -> Dict[str, str]:
        """Get CSS variables for theme"""
        base_colors = {
            "light": {
                "bg_primary": "#ffffff",
                "bg_secondary": "#f8f9fa",
                "text_primary": "#1a1a1a",
                "text_secondary": "#6c757d",
                "accent": "#4f46e5",
                "border": "#e5e7eb",
            },
            "dark": {
                "bg_primary": "#1a1a1a",
                "bg_secondary": "#2d2d2d",
                "text_primary": "#f8f9fa",
                "text_secondary": "#9ca3af",
                "accent": "#818cf8",
                "border": "#374151",
            },
            "system": {
                "bg_primary": "inherit",
                "bg_secondary": "inherit",
                "text_primary": "inherit",
                "text_secondary": "inherit",
                "accent": "inherit",
                "border": "inherit",
            },
        }
        return base_colors.get(theme, base_colors["system"])
