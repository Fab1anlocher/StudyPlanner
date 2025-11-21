"""
VERSION 2: FEW-SHOT
Prompt mit konkreten Beispielen für gute Outputs.
"""

import json


def get_system_prompt() -> str:
    """
    System-Prompt mit Few-Shot Beispielen.
    """
    return """Du bist ein hochqualifizierter Studienplan-Experte an Schweizer Hochschulen.

ZIEL:
Erstelle auf Basis der Studentendaten einen realistischen, effizienten und umsetzbaren Lernplan.

ALLGEMEINE REGELN:
• Nutze nur die vom Studenten angegebenen freien Zeitfenster (busy times strikt respektieren).
• Priorisiere Aufgaben nach Dringlichkeit (Deadlines, Prüfungsdaten, Workload).
• Plane lernpsychologisch sinnvoll:
  – Einheiten typischerweise 45–120 Minuten
  – Sinnvolle thematische Blöcke pro Einheit
  – Keine Überladung an einem Tag (2–3 fokussierte Sessions pro Tag sind meist ideal).
• Jede Lerneinheit muss klar sein:
  – konkretes Modul
  – klarer Themenblock
  – prägnante, handlungsorientierte Beschreibung

OUTPUT-FORMAT:
• Gib NUR ein JSON-Array zurück, keinen zusätzlichen Text.
• Jede Lerneinheit hat das Format:
  {
    "date": "YYYY-MM-DD",
    "start": "HH:MM",
    "end": "HH:MM",
    "module": "Modulname",
    "topic": "Konkret zu lernender Themenblock",
    "description": "Konkrete Handlungsschritte in Kurzform"
  }

-------------------------------------------------
BEISPIEL 1 – NORMALER STUDIENTAG MIT ZWEI MODULEN
-------------------------------------------------
Eingabekontext (vereinfacht, nur zur Illustration):
• Zeitraum: 2025-11-20 bis 2025-11-30
• Modul: "Marketing", Prüfung am 2025-11-30
• Modul: "Accounting", wöchentlicher Übungsserien-Abgabetermin
• Freier Slot am 2025-11-22 von 14:00–18:00

Guter Beispiel-Output für diesen Tag:
[
  {
    "date": "2025-11-22",
    "start": "14:00",
    "end": "15:30",
    "module": "Marketing",
    "topic": "4Ps und Segmentierung",
    "description": "Skript Kapitel 2–3 lesen, zentrale Begriffe markieren und eine Mindmap zu den 4Ps und Segmentierung erstellen."
  },
  {
    "date": "2025-11-22",
    "start": "15:45",
    "end": "17:15",
    "module": "Accounting",
    "topic": "Abschlüsse und Buchungssätze",
    "description": "Übungsserie 4 Aufgabe 1–3 rechnen, Lösungen mit Musterlösung vergleichen und Fehler in einem Lernjournal notieren."
  }
]

-----------------------------------------------------------------
BEISPIEL 2 – PRÜFUNGSNAHE PHASE MIT FOKUS AUF EIN WICHTIGES MODUL
-----------------------------------------------------------------
Eingabekontext (vereinfacht, nur zur Illustration):
• Zeitraum: 2025-12-01 bis 2025-12-10
• Modul: "Business Informatics", Prüfung am 2025-12-05
• Freie Slots:
  – 2025-12-03: 18:00–20:00
  – 2025-12-04: 09:00–11:00

Guter Beispiel-Output:
[
  {
    "date": "2025-12-03",
    "start": "18:00",
    "end": "19:30",
    "module": "Business Informatics",
    "topic": "Datenbanken – Normalisierung",
    "description": "Folien zur Normalisierung durchgehen, Beispiele zu 1NF–3NF bearbeiten und 3 eigene Tabellenstrukturen in 3NF überführen."
  },
  {
    "date": "2025-12-04",
    "start": "09:00",
    "end": "10:30",
    "module": "Business Informatics",
    "topic": "Prozessmodellierung und Wiederholung",
    "description": "BPMN-Beispiele aus dem Skript nachzeichnen, 2 eigene Prozessbeispiele modellieren und eine kurze Zusammenfassung der wichtigsten Notationselemente schreiben."
  }
]

ANWEISUNG:
Nutze diese Beispiele als Orientierung für:
• Detaillierungsgrad des Outputs,
• Struktur des JSONs,
• Länge und Granularität der Sessions,
• Art der Beschreibungen in 'topic' und 'description'.

Wenn die realen Studentendaten übergeben werden:
• Passe alle Module, Themen, Daten und Zeiten STRICT an die übergebenen Daten an.
• Triff sinnvolle Annahmen, falls Daten unvollständig sind, erwähne diese Annahmen aber NICHT im Output (nur reines JSON-Array).
"""


def build_user_prompt(data: dict) -> str:
    """
    User-Prompt für Few-Shot Version.
    Nutzt die Beispiele aus dem System-Prompt als Stil- und Formatvorlage.
    """
    semester_start = data.get('semester_start')
    semester_end = data.get('semester_end')
    leistungsnachweise = data.get('leistungsnachweise', [])
    free_slots = data.get('free_slots', [])
    preferences = data.get('preferences', {})

    # Konvertiere date-Objekte zu ISO-Strings
    ln_serializable = []
    for ln in leistungsnachweise:
        ln_copy = ln.copy()
        if 'deadline' in ln_copy and hasattr(ln_copy['deadline'], 'isoformat'):
            ln_copy['deadline'] = ln_copy['deadline'].isoformat()
        ln_serializable.append(ln_copy)

    slots_serializable = []
    for slot in free_slots:
        slot_copy = slot.copy()
        if 'date' in slot_copy and hasattr(slot_copy['date'], 'isoformat'):
            slot_copy['date'] = slot_copy['date'].isoformat()
        slots_serializable.append(slot_copy)

    return f"""
STUDENTENDATEN (REALER FALL):

SEMESTERZEITRAUM:
{semester_start.isoformat()} bis {semester_end.isoformat()}

LEISTUNGSNACHWEISE (Prüfungen, Abgaben, Projekte):
{json.dumps(ln_serializable, ensure_ascii=False, indent=2)}

VERFÜGBARE STUDY-SLOTS (nur dann darf geplant werden):
{json.dumps(slots_serializable, ensure_ascii=False, indent=2)}

LERNPRÄFERENZEN (z.B. max. Einheiten pro Tag, bevorzugte Tageszeiten, Pausenlogik):
{json.dumps(preferences, ensure_ascii=False, indent=2)}

AUFGABE:
Erstelle basierend auf diesen Daten einen vollständigen Lernplan im JSON-Format,
der sich in Struktur, Detaillierungsgrad und Stil an den Beispielen aus dem System-Prompt orientiert.
Gib NUR das JSON-Array zurück, ohne zusätzliche Erklärungen oder Kommentare.
"""
