"""
Pydantic Model für Leistungsnachweise (Prüfungen, Hausarbeiten, etc.)
"""

from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

from constants import (
    LeistungsnachweisType,
    ExamFormat,
    MIN_PRIORITY,
    MAX_PRIORITY,
    MIN_EFFORT,
    MAX_EFFORT,
)


class Leistungsnachweis(BaseModel):
    """
    Model für einen Leistungsnachweis (Prüfung, Hausarbeit, Präsentation, etc.)

    Attributes:
        title: Titel des Leistungsnachweises
        type: Art des Leistungsnachweises (Enum)
        deadline: Fälligkeitsdatum / Prüfungsdatum
        module: Zugehöriges Modul (optional)
        topics: Liste von Themen/Inhalten
        priority: Prioritätsstufe (1-5)
        effort: Geschätzter Lernaufwand (1-5)
        exam_format: Prüfungsformat (nur bei type=Prüfung)
        exam_details: Zusätzliche Prüfungsdetails (optional)
    """

    title: str = Field(
        ..., min_length=1, max_length=200, description="Titel des Leistungsnachweises"
    )
    type: LeistungsnachweisType = Field(..., description="Art des Leistungsnachweises")
    deadline: Optional[date] = Field(None, description="Fälligkeitsdatum")
    module: Optional[str] = Field(None, max_length=200, description="Zugehöriges Modul")
    topics: List[str] = Field(default_factory=list, description="Liste von Themen")
    priority: int = Field(
        3, ge=MIN_PRIORITY, le=MAX_PRIORITY, description="Priorität 1-5"
    )
    effort: int = Field(3, ge=MIN_EFFORT, le=MAX_EFFORT, description="Lernaufwand 1-5")
    exam_format: Optional[ExamFormat] = Field(
        None, description="Prüfungsformat (nur bei Prüfungen)"
    )
    exam_details: Optional[str] = Field(
        None, max_length=500, description="Prüfungsdetails"
    )

    @field_validator("topics")
    @classmethod
    def filter_empty_topics(cls, v: List[str]) -> List[str]:
        """Filtert leere Strings aus Topics-Liste"""
        return [topic.strip() for topic in v if topic.strip()]

    @field_validator("exam_format")
    @classmethod
    def validate_exam_format(
        cls, v: Optional[ExamFormat], info
    ) -> Optional[ExamFormat]:
        """Prüfungsformat nur bei type=Prüfung erlaubt"""
        if v is not None:
            # Zugriff auf 'type' via info.data
            ln_type = info.data.get("type")
            if ln_type != LeistungsnachweisType.PRUEFUNG:
                raise ValueError(
                    f"exam_format nur bei type=Prüfung erlaubt, nicht bei {ln_type}"
                )
        return v

    class Config:
        # Erlaubt Verwendung von Enums als Values
        use_enum_values = False
        # JSON Schema Generation
        json_schema_extra = {
            "example": {
                "title": "Data Science Prüfung",
                "type": "Prüfung",
                "deadline": "2025-12-20",
                "module": "Data Science Grundlagen",
                "topics": ["Kapitel 1: Python", "Kapitel 2: Pandas", "Kapitel 3: ML"],
                "priority": 5,
                "effort": 4,
                "exam_format": "Multiple Choice",
                "exam_details": "60 Minuten, 40 Fragen, Closed Book",
            }
        }

    def to_dict(self) -> dict:
        """Konvertiert zu dict mit Enum-Values als Strings"""
        data = self.model_dump()
        # Konvertiere Enums zu Strings
        if isinstance(data.get("type"), LeistungsnachweisType):
            data["type"] = data["type"].value
        if isinstance(data.get("exam_format"), ExamFormat):
            data["exam_format"] = data["exam_format"].value
        # Konvertiere date zu ISO string
        if isinstance(data.get("deadline"), date):
            data["deadline"] = data["deadline"].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Leistungsnachweis":
        """Erstellt Leistungsnachweis aus dict (z.B. Session State)"""
        data = data.copy()

        # Konvertiere string zu Enum
        if isinstance(data.get("type"), str):
            data["type"] = LeistungsnachweisType(data["type"])
        if isinstance(data.get("exam_format"), str):
            data["exam_format"] = ExamFormat(data["exam_format"])

        # Konvertiere ISO string zu date
        if isinstance(data.get("deadline"), str):
            data["deadline"] = date.fromisoformat(data["deadline"])

        return cls(**data)
