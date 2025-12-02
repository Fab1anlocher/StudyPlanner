"""
Planning Service - Business Logic für Zeitfenster-Berechnung
Wrapper um planning.py mit Session-State-Integration und Datenkonvertierung
"""

from datetime import date, time, datetime
from typing import List, Dict, Any, Tuple, Optional

from planning import calculate_free_slots as calc_free_slots_core
from constants import (
    convert_weekday_de_to_en,
    TIME_FORMAT,
    DEFAULT_EARLIEST_STUDY_TIME,
    DEFAULT_LATEST_STUDY_TIME,
)

# Pre-computed time constants to avoid repeated datetime.strptime() calls
# These are module-level constants parsed once at import time
_TIME_07_00 = time(7, 0)
_TIME_08_00 = time(8, 0)
_TIME_12_00 = time(12, 0)
_TIME_17_00 = time(17, 0)
_TIME_18_00 = time(18, 0)
_TIME_20_00 = time(20, 0)
_TIME_22_00 = time(22, 0)


def calculate_free_slots_from_session(
    session_state,
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Berechnet freie Zeitfenster basierend auf Session State

    Konvertiert Session-State-Daten in das Format für planning.py,
    ruft die Core-Logik auf und konvertiert das Ergebnis zurück.

    Args:
        session_state: Streamlit Session State Object

    Returns:
        Tuple of (free_slots_list, error_message)
        - free_slots_list: List of dicts mit freien Zeitfenstern
        - error_message: Fehlermeldung oder None

    Format der free_slots:
        [
            {
                "date": date object,
                "start": "HH:MM",
                "end": "HH:MM",
                "hours": float
            },
            ...
        ]
    """

    # Extract data from session state
    study_start = session_state.study_start
    study_end = session_state.study_end

    if not study_end:
        return (
            [],
            "Kein Enddatum verfügbar. Bitte füge mindestens einen Leistungsnachweis mit Fälligkeitsdatum hinzu.",
        )

    # Ensure dates are date objects
    if isinstance(study_start, datetime):
        study_start = study_start.date()
    elif not isinstance(study_start, date):
        return [], "Ungültiges Startdatum-Format."

    if isinstance(study_end, datetime):
        study_end = study_end.date()
    elif not isinstance(study_end, date):
        return [], "Ungültiges Enddatum-Format."

    # Get constraints from session state
    busy_times = session_state.get("busy_times", [])
    absences = session_state.get("absences", [])
    preferences = session_state.get("preferences", {})

    rest_days = preferences.get("rest_days", [])
    max_hours_day = preferences.get("max_hours_day", 8)
    max_hours_week = preferences.get("max_hours_week", 0)
    min_session_duration = preferences.get("min_session_duration", 15) / 60.0

    # Determine time boundaries based on preferences
    preferred_times = preferences.get("preferred_times_of_day", [])
    earliest_study_time, latest_study_time = _get_time_boundaries(preferred_times)

    # Convert busy_times format
    # Old format: {"days": [weekdays], "start": "HH:MM", "end": "HH:MM"}
    # New format: {"day": weekday, "start": time, "end": time}
    converted_busy_times = _convert_busy_times(busy_times)

    # Convert absences format
    # Old format: {"start_date": date, "end_date": date}
    # New format: {"start": date, "end": date}
    converted_absences = _convert_absences(absences)

    # Convert rest_days from German to English lowercase
    converted_rest_days = [convert_weekday_de_to_en(day) for day in rest_days]

    # Call core planning function
    free_slots, error = calc_free_slots_core(
        study_start=study_start,
        study_end=study_end,
        busy_times=converted_busy_times,
        absences=converted_absences,
        rest_days=converted_rest_days,
        max_hours_day=max_hours_day,
        max_hours_week=max_hours_week,
        min_session_duration=min_session_duration,
        earliest_study_time=earliest_study_time,
        latest_study_time=latest_study_time,
    )

    # Handle errors
    if error:
        return [], error

    # Convert output format to match app expectations
    # Core returns: {"date": date, "day": str, "start_time": time, "end_time": time}
    # App expects: {"date": date, "start": "HH:MM", "end": "HH:MM", "hours": float}
    converted_output = _convert_free_slots_output(free_slots)

    return converted_output, None


def _get_time_boundaries(preferred_times: List[str]) -> Tuple[time, time]:
    """
    Bestimmt Zeitgrenzen basierend auf bevorzugten Tageszeiten

    Args:
        preferred_times: List of preferred times ("morning", "afternoon", "evening")

    Returns:
        Tuple of (earliest_time, latest_time)
    """
    if not preferred_times:
        # Default: 08:00-20:00 (reasonable student hours)
        return (_TIME_08_00, _TIME_20_00)

    # Convert to set for O(1) membership testing
    prefs = set(preferred_times)

    # Map preferences to time ranges using pre-computed time constants
    if prefs == {"morning"}:
        # Only morning: 07:00-12:00
        return (_TIME_07_00, _TIME_12_00)
    elif prefs == {"afternoon"}:
        # Only afternoon: 12:00-18:00
        return (_TIME_12_00, _TIME_18_00)
    elif prefs == {"evening"}:
        # Only evening: 17:00-22:00
        return (_TIME_17_00, _TIME_22_00)
    elif "morning" in prefs and "afternoon" in prefs and "evening" not in prefs:
        # Morning + afternoon: 07:00-18:00
        return (_TIME_07_00, _TIME_18_00)
    elif "afternoon" in prefs and "evening" in prefs and "morning" not in prefs:
        # Afternoon + evening: 12:00-22:00
        return (_TIME_12_00, _TIME_22_00)
    else:
        # All times or morning+evening: 07:00-22:00 (most flexible)
        return (_TIME_07_00, _TIME_22_00)


def _convert_busy_times(busy_times: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Konvertiert busy_times von Session-Format zu Planning-Format

    Session Format: {"label": str, "days": [weekdays], "start": "HH:MM", "end": "HH:MM"}
    Planning Format: {"day": weekday_en, "start": time, "end": time, "label": str}

    Returns:
        List of converted busy times (one entry per day with label)
    """
    converted = []

    for busy in busy_times:
        label = busy.get("label", "Verpflichtung")
        for day in busy.get("days", []):
            # Convert German day name to English lowercase
            english_day = convert_weekday_de_to_en(day)

            converted.append(
                {
                    "day": english_day,
                    "start": datetime.strptime(busy["start"], TIME_FORMAT).time(),
                    "end": datetime.strptime(busy["end"], TIME_FORMAT).time(),
                    "label": label,
                }
            )

    return converted


def _convert_absences(absences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Konvertiert absences von Session-Format zu Planning-Format

    Session Format: {"label": str, "start_date": date, "end_date": date}
    Planning Format: {"start": date, "end": date, "label": str}
    """
    return [
        {
            "start": absence["start_date"],
            "end": absence["end_date"],
            "label": absence.get("label", "Abwesenheit"),
        }
        for absence in absences
    ]


def _convert_free_slots_output(
    free_slots: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Konvertiert Output von Planning-Format zu App-Format

    Planning Format: {"date": date, "day": str, "start_time": time, "end_time": time}
    App Format: {"date": date, "start": "HH:MM", "end": "HH:MM", "hours": float}
    """
    converted = []

    for slot in free_slots:
        # Calculate duration
        start_time = slot["start_time"]
        end_time = slot["end_time"]

        dt_start = datetime.combine(date.min, start_time)
        dt_end = datetime.combine(date.min, end_time)
        hours = (dt_end - dt_start).total_seconds() / 3600

        # Only include intervals with meaningful duration (at least 15 minutes)
        if hours >= 0.25:
            converted.append(
                {
                    "date": slot["date"],
                    "start": start_time.strftime(TIME_FORMAT),
                    "end": end_time.strftime(TIME_FORMAT),
                    "hours": round(hours, 2),
                }
            )

    return converted


def get_total_available_hours(free_slots: List[Dict[str, Any]]) -> float:
    """
    Berechnet totale verfügbare Lernstunden aus free_slots

    Args:
        free_slots: List of free slot dicts

    Returns:
        Total hours available
    """
    return sum(slot.get("hours", 0) for slot in free_slots)


def get_available_days_count(free_slots: List[Dict[str, Any]]) -> int:
    """
    Zählt Anzahl Tage mit verfügbarer Lernzeit

    Args:
        free_slots: List of free slot dicts

    Returns:
        Number of unique days with free slots
    """
    unique_dates = set(slot["date"] for slot in free_slots)
    return len(unique_dates)
