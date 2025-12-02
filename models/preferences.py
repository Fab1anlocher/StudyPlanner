"""
Pydantic Model für Benutzerpräferenzen
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from constants import (
    WEEKDAY_NAMES_DE,
    TIME_OF_DAY_OPTIONS,
    MIN_HOURS_PER_DAY,
    MAX_HOURS_PER_DAY,
    MIN_HOURS_PER_WEEK,
    MAX_HOURS_PER_WEEK,
    MIN_SESSION_DURATION_MINUTES,
    MAX_SESSION_DURATION_MINUTES,
)


class UserPreferences(BaseModel):
    """
    Model für Benutzerpräferenzen und Lernstrategien

    Attributes:
        spacing: Spaced Repetition aktiviert
        interleaving: Fächer mischen (Interleaving)
        deep_work: Lange Fokusblöcke für komplexe Themen
        short_sessions: Kurze Sessions für theorielastige Fächer
        rest_days: Liste von Ruhetagen (Deutsch)
        max_hours_day: Maximale Lernstunden pro Tag
        max_hours_week: Maximale Lernstunden pro Woche (None = unbegrenzt)
        min_session_duration: Minimale Session-Dauer in Minuten
        preferred_times_of_day: Bevorzugte Tageszeiten ("morning", "afternoon", "evening")
    """

    spacing: bool = Field(default=True, description="Spaced Repetition")
    interleaving: bool = Field(default=False, description="Fächer mischen")
    deep_work: bool = Field(default=True, description="Lange Fokusblöcke")
    short_sessions: bool = Field(default=False, description="Kurze Sessions")
    rest_days: List[str] = Field(default_factory=list, description="Ruhetage")
    max_hours_day: int = Field(
        default=8,
        ge=MIN_HOURS_PER_DAY,
        le=MAX_HOURS_PER_DAY,
        description="Max. Stunden/Tag",
    )
    max_hours_week: Optional[int] = Field(
        default=40,
        ge=MIN_HOURS_PER_WEEK,
        le=MAX_HOURS_PER_WEEK,
        description="Max. Stunden/Woche",
    )
    min_session_duration: int = Field(
        default=60,
        ge=MIN_SESSION_DURATION_MINUTES,
        le=MAX_SESSION_DURATION_MINUTES,
        description="Min. Session-Dauer (Minuten)",
    )
    preferred_times_of_day: List[str] = Field(
        default_factory=list, description="Bevorzugte Tageszeiten"
    )

    @field_validator("rest_days")
    @classmethod
    def validate_rest_days(cls, v: List[str]) -> List[str]:
        """Validiert dass nur gültige Wochentage (Deutsch) verwendet werden"""
        for day in v:
            if day not in WEEKDAY_NAMES_DE:
                raise ValueError(
                    f"Ungültiger Ruhetag: {day}. "
                    f"Erlaubt: {', '.join(WEEKDAY_NAMES_DE)}"
                )
        return v

    @field_validator("preferred_times_of_day")
    @classmethod
    def validate_times_of_day(cls, v: List[str]) -> List[str]:
        """Validiert bevorzugte Tageszeiten"""
        for time_of_day in v:
            if time_of_day not in TIME_OF_DAY_OPTIONS:
                raise ValueError(
                    f"Ungültige Tageszeit: {time_of_day}. "
                    f"Erlaubt: {', '.join(TIME_OF_DAY_OPTIONS)}"
                )
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "spacing": True,
                "interleaving": False,
                "deep_work": True,
                "short_sessions": False,
                "rest_days": ["Sonntag"],
                "max_hours_day": 6,
                "max_hours_week": 30,
                "min_session_duration": 90,
                "preferred_times_of_day": ["afternoon", "evening"],
            }
        }

    def get_total_rest_days_per_week(self) -> int:
        """Anzahl Ruhetage pro Woche"""
        return len(self.rest_days)

    def get_max_study_days_per_week(self) -> int:
        """Maximale Lerntage pro Woche"""
        return 7 - self.get_total_rest_days_per_week()
