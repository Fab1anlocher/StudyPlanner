"""
Session Manager Service
Zentralisiert Session State Management und Validation
"""

from datetime import date
from typing import Any, Dict


def init_session_state(session_state: Any) -> None:
    """
    Initialize all session state variables if they don't exist yet.
    This ensures data persistence across page interactions.

    Args:
        session_state: Streamlit session state object
    """
    # Study plan dates
    if "study_start" not in session_state:
        session_state.study_start = date.today()

    if "study_end" not in session_state:
        session_state.study_end = None

    # Leistungsnachweise (exams, assignments, presentations)
    if "leistungsnachweise" not in session_state:
        session_state.leistungsnachweise = []

    # Busy times (when student cannot study)
    if "busy_times" not in session_state:
        session_state.busy_times = []

    # Absences (vacations, trips, etc.)
    if "absences" not in session_state:
        session_state.absences = []

    # User preferences (study style, daily limits, etc.)
    if "preferences" not in session_state:
        session_state.preferences = {}

    # Generated study plan
    if "plan" not in session_state:
        session_state.plan = []

    # Free time slots
    if "free_slots" not in session_state:
        session_state.free_slots = []

    # API key
    if "openai_key" not in session_state:
        session_state.openai_key = ""

    # Model configuration
    if "model_provider" not in session_state:
        session_state.model_provider = "OpenAI"

    if "model_name" not in session_state:
        session_state.model_name = "gpt-4o-mini"


def validate_setup_complete(session_state: Any) -> tuple[bool, list[str]]:
    """
    Validate if the setup is complete for plan generation.

    Args:
        session_state: Streamlit session state object

    Returns:
        Tuple of (is_complete, missing_items)
    """
    missing = []

    # Check for leistungsnachweise
    if (
        not session_state.leistungsnachweise
        or len(session_state.leistungsnachweise) == 0
    ):
        missing.append("Mindestens ein Leistungsnachweis")

    # Check for API key
    if not session_state.openai_key or session_state.openai_key.strip() == "":
        missing.append("API-Schlüssel (OpenAI oder Gemini)")

    # Check for study end date
    if session_state.study_end is None:
        missing.append("Enddatum (wird automatisch aus Leistungsnachweisen berechnet)")

    is_complete = len(missing) == 0
    return is_complete, missing


def get_setup_summary(session_state: Any) -> Dict[str, Any]:
    """
    Get a summary of the current setup configuration.

    Args:
        session_state: Streamlit session state object

    Returns:
        Dictionary with setup summary statistics
    """
    summary = {
        "num_leistungsnachweise": len(session_state.leistungsnachweise),
        "num_busy_times": len(session_state.busy_times),
        "num_absences": len(session_state.absences),
        "has_api_key": bool(
            session_state.openai_key and session_state.openai_key.strip()
        ),
        "study_start": session_state.study_start,
        "study_end": session_state.study_end,
        "rest_days_count": len(session_state.preferences.get("rest_days", [])),
        "max_hours_day": session_state.preferences.get("max_hours_day", 8),
        "max_hours_week": session_state.preferences.get("max_hours_week", 40),
        "min_session_duration": session_state.preferences.get(
            "min_session_duration", 60
        ),
    }

    # Calculate duration if both dates are set
    if session_state.study_start and session_state.study_end:
        summary["duration_days"] = (
            session_state.study_end - session_state.study_start
        ).days
    else:
        summary["duration_days"] = None

    return summary


def get_active_learning_strategies(session_state: Any) -> list[str]:
    """
    Get a list of active learning strategies.

    Args:
        session_state: Streamlit session state object

    Returns:
        List of active strategy names
    """
    strategies = []

    if session_state.preferences.get("spacing", False):
        strategies.append("Spaced Repetition")

    if session_state.preferences.get("interleaving", False):
        strategies.append("Interleaving von Fächern")

    if session_state.preferences.get("deep_work", False):
        strategies.append("Deep-Work-Einheiten für komplexe Themen")

    if session_state.preferences.get("short_sessions", False):
        strategies.append("Kurze Einheiten für theorielastige Fächer")

    return strategies


def reset_plan_data(session_state: Any) -> None:
    """
    Reset plan-related data (useful before regenerating plan).

    Args:
        session_state: Streamlit session state object
    """
    session_state.plan = []
    session_state.free_slots = []


def has_plan(session_state: Any) -> bool:
    """
    Check if a plan exists in session state.

    Args:
        session_state: Streamlit session state object

    Returns:
        True if plan exists and has entries
    """
    return (
        "plan" in session_state and session_state.plan and len(session_state.plan) > 0
    )
