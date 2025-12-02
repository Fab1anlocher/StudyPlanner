"""
Application settings and configuration
Kann später für Environment-spezifische Configs erweitert werden
"""

import os
from typing import Optional


class Settings:
    """
    Zentrale Anwendungs-Settings
    Kann später mit pydantic-settings oder python-decouple erweitert werden
    """

    # App Metadata
    APP_NAME = "KI-Lernplaner für Studierende"
    APP_ICON = "📚"
    VERSION = "1.0.0"

    # Streamlit Config
    PAGE_TITLE = "KI-Lernplaner"
    PAGE_ICON = "📚"
    LAYOUT = "wide"
    INITIAL_SIDEBAR_STATE = "expanded"

    # LLM Settings
    LLM_TEMPERATURE = 0.7
    LLM_MAX_TOKENS = 16000

    # File paths (relativ zum Projekt-Root)
    PROMPT_TEMPLATES_DIR = "data/prompt_templates"
    PROMPTS_DIR = "prompts"

    # Development
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    # Database (für später)
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
