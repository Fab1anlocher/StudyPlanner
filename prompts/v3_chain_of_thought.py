"""
VERSION 3: CHAIN-OF-THOUGHT (LIGHT)
Prompt, der die KI zu strukturiertem, mehrstufigem Denken anregt,
aber nach außen nur eine kurze Planungszusammenfassung + JSON ausgibt.
"""

import json


def get_system_prompt() -> str:
    """
    System-Prompt mit strukturiertem Reasoning und expliziten Schritten.
    """
    return """Du bist ein hochqualifizierter Studienplan-Experte an Schweizer Hochschulen.

AUFGABE:
Erstelle aus den Studentendaten einen realistischen, effizienten und umsetzbaren Lernplan.

DENKE IN KLAREN SCHRITTEN (INTERN):
1. Analysiere die Eingangsdaten:
   • Zeitraum
   • Module, Prüfungen, Abgabetermine, Workload
   • Prüfungsformat (exam_format) und Details → wichtig für Lernstrategie!
   • Verfügbare Zeitslots
   • Präferenzen (z.B. max. Einheiten pro Tag, bevorzugte Tageszeiten)
2. Bestimme Prioritäten:
   • Welche Prüfungen/Abgaben sind am dringendsten?
   • Welche Module haben hohen Workload?
3. Schätze grob den Lernaufwand UND passe Strategie an Prüfungsformat an:
   • Multiple Choice: Definitionen lernen, Karteikarten, Wiederholung
   • Rechenaufgaben: Übungen rechnen, Lösungswege verstehen
   • Mündliche Prüfung: Freies Erklären üben, Konzepte verstehen
   • Essay/Aufsatz: Argumentation aufbauen, kritisch denken
   • Praktisches Projekt (Open Book): Praktisch üben (z.B. SPSS, Coding)
   • Coding-Aufgabe: Code schreiben, debuggen, Algorithmen
   • Fallstudie: Analyse, Problemlösung, Theorie anwenden
4. Verteile die Einheiten auf die freien Zeitslots:
   • Nutze nur die angegebenen freien Slots.
   • Plane zuerst die dringendsten Module.
   • Vermeide Überlastung (idealerweise max. 2–3 fokussierte Sessions pro Tag).
5. Verfeinere die Einheiten:
   • Dauer typischerweise 45–120 Minuten.
   • Pro Einheit ein klarer Themenblock.
   • Konkrete, handlungsorientierte Beschreibung.

WIE DU ANTWORTEN SOLLST:
1. Gib eine KURZE, HOCHSTUFIGE Planungszusammenfassung (kein detailliertes Gedankenprotokoll) aus.
   • Erkläre in 3–7 Sätzen oder Stichpunkten:
     – Wie du priorisiert hast,
     – wie du den Workload verteilt hast,
     – wie du mit Präferenzen (z.B. Tageszeiten) umgehst.
   • Keine extrem detaillierten Schritt-für-Schritt-Gedanken, nur eine grobe Übersicht.
2. Gib danach den fertigen Lernplan als JSON-Array im folgenden Format zurück:

PLAN_JSON FORMAT:
[
  {
    "date": "YYYY-MM-DD",
    "start": "HH:MM",
    "end": "HH:MM",
    "module": "Modulname",
    "topic": "Konkret zu lernender Themenblock",
    "description": "Konkrete Handlungsschritte in Kurzform"
  }
]

AUSGABEFORMAT (SEKTIONEN):
Du antwortest IMMER in dieser Struktur:

PLANUNG_ZUSAMMENFASSUNG:
<kurze, grobe Beschreibung deines Vorgehens in natürlicher Sprache>

PLAN_JSON:
<JSON-Array wie oben beschrieben>

WICHTIG:
• Nutze nur die freien Zeitslots.
• Triff sinnvolle Annahmen, falls Daten unvollständig sind, erwähne diese aber nur auf hoher Ebene.
• Stelle sicher, dass das JSON syntaktisch gültig ist.
"""


def build_user_prompt(data: dict) -> str:
    """
    User-Prompt für Chain-of-Thought-Light Version.
    Regt strukturiertes Denken an und verlangt anschließend
    eine kurze Planungszusammenfassung + JSON.
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
Analysiere die folgenden Studentendaten und erstelle einen Lernplan.

SEMESTERZEITRAUM:
{semester_start.isoformat()} bis {semester_end.isoformat()}

LEISTUNGSNACHWEISE (Prüfungen, Abgaben, Projekte):
Jeder Leistungsnachweis enthält:
- title, type, deadline, module, topics, priority, effort
- exam_format (nur bei Prüfungen): z.B. "Multiple Choice", "Rechenaufgaben" etc.
- exam_details (nur bei Prüfungen): z.B. "90 Min, Closed Book"

WICHTIG: Berücksichtige exam_format in deiner Planungsstrategie!
{json.dumps(ln_serializable, ensure_ascii=False, indent=2)}

VERFÜGBARE STUDY-SLOTS:
{json.dumps(slots_serializable, ensure_ascii=False, indent=2)}

LERNPRÄFERENZEN:
{json.dumps(preferences, ensure_ascii=False, indent=2)}

ARBEITE GEMÄSS DEM VORGEGEBENEN SCHRITT-FÜR-SCHRITT-PROZESS AUS DEM SYSTEM-PROMPT.

Gib deine Antwort GENAU in dieser Struktur:

PLANUNG_ZUSAMMENFASSUNG:
<kurze Erklärung deiner Priorisierung und Verteilung, 3–7 Sätze oder Stichpunkte>

PLAN_JSON:
<JSON-Array mit allen Lerneinheiten im geforderten Format>
"""
