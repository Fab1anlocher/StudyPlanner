"""
Zentrale Constants für den StudyPlanner
Eliminiert Code-Duplication und vereinheitlicht Magic Strings
"""

from enum import Enum
from typing import Dict


# ════════════════════════════════════════════════════════════════
# WEEKDAY MAPPINGS
# ════════════════════════════════════════════════════════════════

# Wochentage: Index (0=Monday) → Deutsch
WEEKDAY_INDEX_TO_DE: Dict[int, str] = {
    0: "Montag",
    1: "Dienstag",
    2: "Mittwoch",
    3: "Donnerstag",
    4: "Freitag",
    5: "Samstag",
    6: "Sonntag",
}

# Wochentage: Index (0=Monday) → Englisch (lowercase)
WEEKDAY_INDEX_TO_EN: Dict[int, str] = {
    0: "monday",
    1: "tuesday",
    2: "wednesday",
    3: "thursday",
    4: "friday",
    5: "saturday",
    6: "sunday",
}

# Wochentage: Deutsch → Englisch (lowercase)
WEEKDAY_DE_TO_EN: Dict[str, str] = {
    "Montag": "monday",
    "Dienstag": "tuesday",
    "Mittwoch": "wednesday",
    "Donnerstag": "thursday",
    "Freitag": "friday",
    "Samstag": "saturday",
    "Sonntag": "sunday",
}

# Wochentage: Englisch (capitalized) → Deutsch
WEEKDAY_EN_CAPITALIZED_TO_DE: Dict[str, str] = {
    "Monday": "Montag",
    "Tuesday": "Dienstag",
    "Wednesday": "Mittwoch",
    "Thursday": "Donnerstag",
    "Friday": "Freitag",
    "Saturday": "Samstag",
    "Sunday": "Sonntag",
}

# Wochentage: Alle deutschen Namen (für Validierung)
WEEKDAY_NAMES_DE = list(WEEKDAY_INDEX_TO_DE.values())

# Wochentage: Alle englischen Namen lowercase (für Validierung)
WEEKDAY_NAMES_EN = list(WEEKDAY_INDEX_TO_EN.values())


# ════════════════════════════════════════════════════════════════
# DATE & TIME FORMATS
# ════════════════════════════════════════════════════════════════

# Datetime format strings
TIME_FORMAT = "%H:%M"  # "14:30"
DATE_FORMAT_SHORT = "%d.%m.%Y"  # "01.12.2025"
DATE_FORMAT_DISPLAY = "%d. %B %Y"  # "01. Dezember 2025"
DATE_FORMAT_ISO = "%Y-%m-%d"  # "2025-12-01"
DATETIME_FORMAT_ISO = "%Y-%m-%d %H:%M:%S"  # "2025-12-01 14:30:00"


# ════════════════════════════════════════════════════════════════
# LEISTUNGSNACHWEIS TYPES
# ════════════════════════════════════════════════════════════════


class LeistungsnachweisType(str, Enum):
    """Typen von Leistungsnachweisen"""

    PRUEFUNG = "Prüfung"
    HAUSARBEIT = "Hausarbeit"
    PRAESENTATION = "Präsentation"
    PROJEKTARBEIT = "Projektarbeit"
    SONSTIGES = "Sonstiges"


# Liste für UI-Dropdowns
LEISTUNGSNACHWEIS_TYPES = [
    LeistungsnachweisType.PRUEFUNG.value,
    LeistungsnachweisType.HAUSARBEIT.value,
    LeistungsnachweisType.PRAESENTATION.value,
    LeistungsnachweisType.PROJEKTARBEIT.value,
    LeistungsnachweisType.SONSTIGES.value,
]


# ════════════════════════════════════════════════════════════════
# EXAM FORMATS
# ════════════════════════════════════════════════════════════════


class ExamFormat(str, Enum):
    """Prüfungsformate für Lernstrategie-Optimierung"""

    MULTIPLE_CHOICE = "Multiple Choice"
    RECHENAUFGABEN = "Rechenaufgaben"
    MUENDLICH = "Mündliche Prüfung"
    ESSAY = "Essay/Aufsatz"
    OPEN_BOOK_PROJECT = "Praktisches Projekt (Open Book)"
    CODING = "Coding-Aufgabe"
    FALLSTUDIE = "Fallstudie"
    GEMISCHT = "Gemischt"
    SONSTIGES = "Sonstiges"


# Liste für UI-Dropdowns
EXAM_FORMATS = [
    ExamFormat.MULTIPLE_CHOICE.value,
    ExamFormat.RECHENAUFGABEN.value,
    ExamFormat.MUENDLICH.value,
    ExamFormat.ESSAY.value,
    ExamFormat.OPEN_BOOK_PROJECT.value,
    ExamFormat.CODING.value,
    ExamFormat.FALLSTUDIE.value,
    ExamFormat.GEMISCHT.value,
    ExamFormat.SONSTIGES.value,
]


# ════════════════════════════════════════════════════════════════
# LLM PROVIDERS & MODELS
# ════════════════════════════════════════════════════════════════


class LLMProvider(str, Enum):
    """Unterstützte LLM-Provider"""

    OPENAI = "OpenAI"
    GEMINI = "Google Gemini"


# OpenAI Models
OPENAI_MODELS = ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]

# Gemini Models
GEMINI_MODELS = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]

# Default Models
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"


# ════════════════════════════════════════════════════════════════
# PREFERENCES & DEFAULTS
# ════════════════════════════════════════════════════════════════

# Default study preferences
DEFAULT_PREFERENCES = {
    "spacing": True,  # Spaced Repetition
    "interleaving": False,  # Fächer mischen
    "deep_work": True,  # Lange Fokusblöcke
    "short_sessions": False,  # Kurze Sessions
    "rest_days": [],  # Keine Standard-Ruhetage
    "max_hours_day": 8,  # Max Stunden pro Tag
    "max_hours_week": 40,  # Max Stunden pro Woche
    "min_session_duration": 60,  # Min. Session-Dauer (Minuten)
    "preferred_times_of_day": [],  # Keine Präferenz
}

# Time of day options
TIME_OF_DAY_OPTIONS = ["morning", "afternoon", "evening"]

# Default time boundaries
DEFAULT_EARLIEST_STUDY_TIME = "08:00"
DEFAULT_LATEST_STUDY_TIME = "20:00"


# ════════════════════════════════════════════════════════════════
# UI CONSTANTS
# ════════════════════════════════════════════════════════════════

# Page names
PAGE_SETUP = "Einrichtung"
PAGE_PLAN = "Lernplan"
PAGE_EXPORT = "Export"

# Session state keys
SESSION_STUDY_START = "study_start"
SESSION_STUDY_END = "study_end"
SESSION_LEISTUNGSNACHWEISE = "leistungsnachweise"
SESSION_BUSY_TIMES = "busy_times"
SESSION_ABSENCES = "absences"
SESSION_PREFERENCES = "preferences"
SESSION_PLAN = "plan"
SESSION_FREE_SLOTS = "free_slots"
SESSION_OPENAI_KEY = "openai_key"
SESSION_MODEL_PROVIDER = "model_provider"
SESSION_MODEL_NAME = "model_name"


# ════════════════════════════════════════════════════════════════
# VALIDATION CONSTRAINTS
# ════════════════════════════════════════════════════════════════

# Limits für Inputs
MIN_PRIORITY = 1
MAX_PRIORITY = 5
MIN_EFFORT = 1
MAX_EFFORT = 5
MIN_HOURS_PER_DAY = 1
MAX_HOURS_PER_DAY = 24
MIN_HOURS_PER_WEEK = 5
MAX_HOURS_PER_WEEK = 168
MIN_SESSION_DURATION_MINUTES = 15
MAX_SESSION_DURATION_MINUTES = 240

# Planning Constraints
MAX_PLANNING_DAYS = 365  # Maximum semester duration in days (1 year)
HOURS_PER_EFFORT_UNIT = 5  # Estimated hours per effort level (1-5 scale)

# LLM Service Constraints
MAX_RETRY_DELAY_SECONDS = 60  # Maximum retry delay for rate limit errors


# ════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════


def get_weekday_de(weekday_index: int) -> str:
    """Konvertiert Weekday-Index (0=Monday) zu deutschem Namen"""
    return WEEKDAY_INDEX_TO_DE.get(weekday_index, "Unknown")


def get_weekday_en(weekday_index: int) -> str:
    """Konvertiert Weekday-Index (0=Monday) zu englischem Namen (lowercase)"""
    return WEEKDAY_INDEX_TO_EN.get(weekday_index, "unknown")


def convert_weekday_de_to_en(weekday_de: str) -> str:
    """Konvertiert deutschen Wochentag zu englisch (lowercase)"""
    return WEEKDAY_DE_TO_EN.get(weekday_de, weekday_de.lower())


def convert_weekday_en_to_de(weekday_en: str) -> str:
    """Konvertiert englischen Wochentag (capitalized) zu deutsch"""
    return WEEKDAY_EN_CAPITALIZED_TO_DE.get(weekday_en, weekday_en)
