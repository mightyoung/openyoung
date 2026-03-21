"""
WebUI Configuration - OpenYoung Streamlit WebUI
"""

import os


class Config:
    """WebUI Configuration"""

    # API Configuration
    API_BASE_URL: str = os.getenv("OPENYOUNG_API_URL", "http://localhost:8000")
    API_KEY: str = os.getenv("OPENYOUNG_API_KEY", "")

    # Evaluation API (独立部署时使用)
    EVAL_API_URL: str = os.getenv("EVAL_API_URL", "http://localhost:8001")
    EVAL_API_KEY: str = os.getenv("EVAL_API_KEY", "")

    # Streamlit Configuration
    PAGE_ICON: str = "🤖"
    LAYOUT: str = "wide"
    INITIAL_SIDEBAR_STATE: str = "expanded"
    TITLE: str = "OpenYoung"

    # Session Configuration
    MAX_MESSAGES: int = 100
    TYPING_SPEED: float = 0.02  # seconds per character

    # Page Titles
    PAGE_TITLES: dict = {
        "home": "OpenYoung",
        "agents": "🤖 Agents",
        "chat": "💬 Chat",
        "sessions": "📋 Sessions",
        "dashboard": "📊 Dashboard",
        "settings": "⚙️ Settings",
    }


# 全局配置实例
config = Config()
