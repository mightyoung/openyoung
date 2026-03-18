"""Global State Management for Streamlit WebUI"""
import streamlit as st
from typing import Any, Optional, Dict
from datetime import datetime


class AppState:
    """Singleton state manager using Streamlit session_state"""

    def __init__(self):
        self._defaults = {
            "theme": "system",
            "current_agent": None,
            "sessions": [],
            "messages": {},
            "user_preferences": {},
        }

    def initialize(self) -> None:
        """Initialize default state"""
        for key, value in self._defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get state value"""
        return st.session_state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set state value"""
        st.session_state[key] = value

    def update(self, **kwargs: Any) -> None:
        """Batch update state"""
        for key, value in kwargs.items():
            st.session_state[key] = value

    # Theme management
    def get_theme(self) -> str:
        return self.get("theme", "system")

    def set_theme(self, theme: str) -> None:
        self.set("theme", theme)

    # Session management
    def get_current_session(self) -> Optional[str]:
        return self.get("current_session_id")

    def set_current_session(self, session_id: str) -> None:
        self.set("current_session_id", session_id)


app_state = AppState()
