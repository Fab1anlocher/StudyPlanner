"""
Pydantic Models für Lerneinheiten und freie Zeitfenster
"""

from datetime import date as date_type, time as time_type
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from constants import TIME_FORMAT


class StudySession(BaseModel):
    """
    Model für eine geplante Lerneinheit

    Attributes:
        date: Datum der Lerneinheit (ISO format)
        start: Startzeit (HH:MM)
        end: Endzeit (HH:MM)
        module: Modulname / Leistungsnachweis
        topic: Spezifisches Lernthema
        description: Detaillierte Beschreibung der Lernaktivität
    """

    date: str = Field(
        ..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Datum (YYYY-MM-DD)"
    )
    start: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="Startzeit (HH:MM)")
    end: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="Endzeit (HH:MM)")
    module: str = Field(
        ..., min_length=1, max_length=200, description="Modul/Leistungsnachweis"
    )
    topic: str = Field(..., min_length=1, max_length=300, description="Lernthema")
    description: str = Field(
        ..., max_length=1000, description="Beschreibung der Aktivität"
    )

    @field_validator("end")
    @classmethod
    def validate_end_after_start(cls, v: str, info) -> str:
        """Validiert dass Endzeit nach Startzeit liegt"""
        start_str = info.data.get("start")
        if start_str:
            # Parse times for comparison
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
                "date": "2025-12-15",
                "start": "14:00",
                "end": "16:00",
                "module": "Data Science",
                "topic": "Kapitel 3: Machine Learning Grundlagen",
                "description": "Supervised Learning Algorithmen durcharbeiten, Übungsaufgaben lösen",
            }
        }

    def get_duration_hours(self) -> float:
        """Berechnet Dauer in Stunden"""
        from datetime import datetime, date as dt_date

        start_time = time_type.fromisoformat(self.start)
        end_time = time_type.fromisoformat(self.end)

        dt_start = datetime.combine(dt_date.min, start_time)
        dt_end = datetime.combine(dt_date.min, end_time)

        duration = (dt_end - dt_start).total_seconds() / 3600
        return round(duration, 2)


class FreeSlot(BaseModel):
    """
    Model für ein freies Zeitfenster (verfügbar zum Lernen)

    Attributes:
        date: Datum des Zeitfensters
        day: Wochentag (Deutsch)
        start_time: Startzeit als time object
        end_time: Endzeit als time object
    """

    date: date_type = Field(..., description="Datum")
    day: str = Field(..., min_length=1, max_length=20, description="Wochentag")
    start_time: time_type = Field(..., description="Startzeit")
    end_time: time_type = Field(..., description="Endzeit")

    @field_validator("end_time")
    @classmethod
    def validate_end_after_start(cls, v: time_type, info) -> time_type:
        """Validiert dass Endzeit nach Startzeit liegt"""
        start = info.data.get("start_time")
        if start and v <= start:
            raise ValueError(f"end_time ({v}) muss nach start_time ({start}) liegen")
        return v

    class Config:
        # Erlaubt date/time objects
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "date": "2025-12-15",
                "day": "Montag",
                "start_time": "14:00",
                "end_time": "17:00",
            }
        }

    def get_duration_hours(self) -> float:
        """Berechnet Dauer in Stunden"""
        from datetime import datetime, date as dt_date

        dt_start = datetime.combine(dt_date.min, self.start_time)
        dt_end = datetime.combine(dt_date.min, self.end_time)
        duration = (dt_end - dt_start).total_seconds() / 3600
        return round(duration, 2)

    def to_dict(self) -> dict:
        """Konvertiert zu dict mit serialisierbaren Werten"""
        return {
            "date": self.date.isoformat(),
            "day": self.day,
            "start_time": self.start_time.strftime(TIME_FORMAT),
            "end_time": self.end_time.strftime(TIME_FORMAT),
        }
