"""
Pydantic Model für Abwesenheiten (Ferien, Events, etc.)
"""

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Absence(BaseModel):
    """
    Model für Abwesenheitsperioden (Ferien, Militär, Konferenzen, etc.)

    Attributes:
        label: Bezeichnung der Abwesenheit
        start_date: Erster Tag der Abwesenheit
        end_date: Letzter Tag der Abwesenheit
        description: Optional detaillierte Beschreibung
    """

    label: str = Field(default="Abwesenheit", max_length=100, description="Bezeichnung")
    start_date: date = Field(..., description="Startdatum")
    end_date: date = Field(..., description="Enddatum")
    description: Optional[str] = Field(None, max_length=500, description="Beschreibung")

    @field_validator("end_date")
    @classmethod
    def validate_end_after_start(cls, v: date, info) -> date:
        """Validiert dass Enddatum gleich oder nach Startdatum liegt"""
        start = info.data.get("start_date")
        if start and v < start:
            raise ValueError(
                f"end_date ({v}) muss gleich oder nach start_date ({start}) liegen"
            )
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "label": "Weihnachtsferien",
                "start_date": "2025-12-20",
                "end_date": "2026-01-05",
                "description": "Familienbesuch, keine Lernzeit möglich",
            }
        }

    def get_duration_days(self) -> int:
        """Berechnet Dauer in Tagen (inklusiv)"""
        return (self.end_date - self.start_date).days + 1

    def contains_date(self, check_date: date) -> bool:
        """Prüft ob ein Datum in dieser Abwesenheitsperiode liegt"""
        return self.start_date <= check_date <= self.end_date
