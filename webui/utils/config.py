"""
OpenYoung WebUI Configuration
"""

import os
from dataclasses import dataclass


@dataclass
class Config:
    """WebUI Configuration"""

    # API Configuration
    API_BASE_URL: str = os.getenv("OPENYOUNG_API_URL", "http://localhost:8000")
    API_KEY: str = os.getenv("OPENYOUNG_API_KEY", "")

    # Streamlit Configuration
    PAGE_ICON: str = "🤖"
    LAYOUT: str = "wide"
    INITIAL_SIDEBAR_STATE: str = "expanded"

    # Chat Configuration
    MAX_MESSAGES: int = 100
    TYPING_SPEED: float = 0.02  # seconds per character

    # Session Configuration
    SESSION_TIMEOUT: int = 3600  # seconds


# Global config instance
config = Config()
