"""
VERSION 1: BASELINE / ZERO-SHOT
Optimierter Prompt für klare Zieldefinition,
Constraints und robustes JSON-Output.
"""

import json


def get_system_prompt() -> str:
    """
    System-Prompt für Zero-Shot Lernplan-Generierung.
    """
    return """Du bist ein hochqualifizierter Studienplan-Experte an Schweizer Hochschulen.

ZIEL:
Erstelle einen realistischen, effizienten und umsetzbaren Lernplan für die gesamte Semesterlaufzeit.

ANFORDERUNGEN:
• Passe die Planung an verfügbare Zeitfenster an (busy times strikt respektieren)
• Berücksichtige Abgabetermine, Prüfungsdaten und Prioritäten
• Plane zuerst die dringendsten Aufgaben (Deadline- und Prüfungsnähe)
• Plane lernpsychologisch sinnvoll (nicht zu lange Intervalle, genügend Pausen)
• Vermeide Überlastung: nicht mehr als 2–3 konzentrierte Einheiten pro Tag
• Inhalt PRO Eintrag: ein klarer Lernsprint mit spezifischem Auftrag

PRÜFUNGSFORMAT-STRATEGIE:
• Multiple Choice: Fokus auf Definitionen auswendig lernen, Karteikarten, Wiederholung
• Rechenaufgaben: Fokus auf Übungsaufgaben rechnen, Lösungswege verstehen, Formeln anwenden
• Mündliche Prüfung: Fokus auf freies Erklären üben, Konzepte verstehen, Beispiele parat haben
• Essay/Aufsatz: Fokus auf Argumentation aufbauen, kritisch denken, Quellen verwenden
• Praktisches Projekt (Open Book): Fokus auf praktisches Üben (z.B. SPSS, Coding), Tool-Kenntnisse
• Coding-Aufgabe: Fokus auf Code schreiben, debuggen, Algorithmen implementieren
• Fallstudie: Fokus auf Analyse, Problemlösung, Theorie anwenden
• Gemischt: Kombination der relevanten Strategien

OUTPUT:
• Nur JSON-Array
• Keine zusätzlichen Kommentare oder Erklärungen
• Jeder Eintrag beschreibt eine Lerneinheit

DATENFORMAT:
[
  {
    "date": "YYYY-MM-DD",
    "start": "HH:MM",
    "end": "HH:MM",
    "module": "Modulname",
    "topic": "Konkret zu lernender Themenblock",
    "description": "Handlungsschritte in Kurzform"
  }
]

WICHTIG:
Wenn Informationen unklar oder unvollständig sind:
• Treffen sinnvolle Annahmen
• Diese NICHT im Output erwähnen (kein Text ausser dem JSON selbst)
"""


def build_user_prompt(data: dict) -> str:
    """
    User-Prompt für Zero-Shot Version.
    """
    semester_start = data.get('semester_start')
    semester_end = data.get('semester_end')
    leistungsnachweise = data.get('leistungsnachweise', [])
    free_slots = data.get('free_slots', [])
    preferences = data.get('preferences', {})

    # ISO-konvertieren
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
SEMESTERZEITRAUM:
{semester_start.isoformat()} bis {semester_end.isoformat()}

LEISTUNGSNACHWEISE (Deadlines / Prüfungen / Workload):
Jeder Leistungsnachweis enthält:
- title, type, deadline, module, topics, priority, effort
- exam_format (nur bei Prüfungen): z.B. "Multiple Choice", "Rechenaufgaben", "Mündliche Prüfung" etc.
- exam_details (nur bei Prüfungen): z.B. "90 Min, Closed Book" oder "Open Book, Laptop erlaubt"

Passe die Lernstrategie an exam_format an!
{json.dumps(ln_serializable, ensure_ascii=False, indent=2)}

VERFÜGBARE STUDY-SLOTS:
{json.dumps(slots_serializable, ensure_ascii=False, indent=2)}

LERNPRÄFERENZEN:
{json.dumps(preferences, ensure_ascii=False, indent=2)}

Generiere den vollständigen Lernplan als JSON-Array im vorgegebenen Format."""
