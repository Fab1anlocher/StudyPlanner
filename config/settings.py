"""
Application settings and configuration
Zentralisiert alle App-weiten Einstellungen und konfigurierbare Parameter
"""

import os
from typing import Optional


class Settings:
    """
    Zentrale Anwendungs-Settings
    Kann später mit pydantic-settings oder python-decouple erweitert werden
    """

    # ════════════════════════════════════════════════════════════════
    # APP METADATA
    # ════════════════════════════════════════════════════════════════
    APP_NAME = "KI-Lernplaner für Studierende"
    APP_ICON = "📚"
    VERSION = "1.0.0"

    # ════════════════════════════════════════════════════════════════
    # STREAMLIT CONFIG
    # ════════════════════════════════════════════════════════════════
    PAGE_TITLE = "KI-Lernplaner"
    PAGE_ICON = "📚"
    LAYOUT = "wide"
    INITIAL_SIDEBAR_STATE = "expanded"

    # ════════════════════════════════════════════════════════════════
    # LLM SETTINGS
    # ════════════════════════════════════════════════════════════════
    LLM_TEMPERATURE = 0.7
    LLM_MAX_TOKENS = 16000
    LLM_RETRY_ATTEMPTS = 3
    LLM_RETRY_DELAY = 1.0  # Sekunden, mit exponentiellem Backoff

    # ════════════════════════════════════════════════════════════════
    # PLANNING DEFAULTS
    # ════════════════════════════════════════════════════════════════
    DEFAULT_MAX_HOURS_PER_DAY = 8
    DEFAULT_MAX_HOURS_PER_WEEK = 40
    DEFAULT_MIN_SESSION_DURATION = 60  # Minuten
    DEFAULT_EARLIEST_STUDY_TIME = "08:00"
    DEFAULT_LATEST_STUDY_TIME = "20:00"
    MIN_FREE_SLOT_DURATION = 0.25  # Stunden (15 Minuten)

    # ════════════════════════════════════════════════════════════════
    # UI DISPLAY SETTINGS
    # ════════════════════════════════════════════════════════════════
    MAX_TOPIC_DISPLAY_LENGTH = 25
    MAX_MODULE_DISPLAY_LENGTH = 20
    MAX_LABEL_DISPLAY_LENGTH = 20

    # ════════════════════════════════════════════════════════════════
    # FILE PATHS
    # ════════════════════════════════════════════════════════════════
    PROMPT_TEMPLATES_DIR = "data/prompt_templates"
    PROMPTS_DIR = "prompts"

    # ════════════════════════════════════════════════════════════════
    # DEVELOPMENT
    # ════════════════════════════════════════════════════════════════
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    # ════════════════════════════════════════════════════════════════
    # DATABASE (für spätere Erweiterung)
    # ════════════════════════════════════════════════════════════════
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")

    @classmethod
    def get_openai_key(cls) -> Optional[str]:
        """Holt OpenAI Key aus Environment (optional)"""
        return os.getenv("OPENAI_API_KEY")

    @classmethod
    def get_gemini_key(cls) -> Optional[str]:
        """Holt Gemini Key aus Environment (optional)"""
        return os.getenv("GEMINI_API_KEY")


# Singleton instance
settings = Settings()
