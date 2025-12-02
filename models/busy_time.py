"""
Pydantic Model für belegte Zeiten (wiederkehrende Verpflichtungen)
"""

from datetime import time as time_type
from typing import List
from pydantic import BaseModel, Field, field_validator

from constants import WEEKDAY_NAMES_DE, WEEKDAY_NAMES_EN, TIME_FORMAT


class BusyTime(BaseModel):
    """
    Model für wiederkehrende wöchentliche Verpflichtungen (Arbeit, Vorlesungen, etc.)

    Attributes:
        label: Bezeichnung der Verpflichtung (z.B. "Arbeit", "Vorlesung")
        days: Liste von Wochentagen (Deutsch oder Englisch)
        start: Startzeit (HH:MM string)
        end: Endzeit (HH:MM string)
    """

    label: str = Field(..., min_length=1, max_length=100, description="Bezeichnung")
    days: List[str] = Field(..., min_length=1, description="Wochentage")
    start: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="Startzeit (HH:MM)")
    end: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="Endzeit (HH:MM)")

    @field_validator("days")
    @classmethod
    def validate_weekdays(cls, v: List[str]) -> List[str]:
        """Validiert dass nur gültige Wochentage verwendet werden"""
        valid_days_lower = [d.lower() for d in WEEKDAY_NAMES_DE + WEEKDAY_NAMES_EN]

        for day in v:
            if day.lower() not in valid_days_lower:
                raise ValueError(
                    f"Ungültiger Wochentag: {day}. "
                    f"Erlaubt: {', '.join(WEEKDAY_NAMES_DE)} oder {', '.join(WEEKDAY_NAMES_EN)}"
                )
        return v

    @field_validator("end")
    @classmethod
    def validate_end_after_start(cls, v: str, info) -> str:
        """Validiert dass Endzeit nach Startzeit liegt"""
        start_str = info.data.get("start")
        if start_str:
            start_time = time_type.fromisoformat(start_str)
            end_time = time_type.fromisoformat(v)
            if end_time <= start_time:
                raise ValueError(
                    f"Endzeit ({v}) muss nach Startzeit ({start_str}) liegen"
                )
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "label": "Arbeit (Teilzeit)",
                "days": ["Montag", "Dienstag"],
                "start": "09:00",
                "end": "17:00",
            }
        }

    def get_duration_hours(self) -> float:
        """Berechnet Dauer in Stunden"""
        from datetime import datetime, date

        start_time = time_type.fromisoformat(self.start)
        end_time = time_type.fromisoformat(self.end)

        dt_start = datetime.combine(date.min, start_time)
        dt_end = datetime.combine(date.min, end_time)
        duration = (dt_end - dt_start).total_seconds() / 3600
        return round(duration, 2)

    def get_total_hours_per_week(self) -> float:
        """Berechnet totale Stunden pro Woche"""
        return self.get_duration_hours() * len(self.days)
