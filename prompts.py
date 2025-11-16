import json

def get_system_prompt() -> str:
    """
    Get the system message for the AI study planner.
    
    Defines the AI's role as an expert educational planner and specifies
    the expected output format (JSON array).
    
    Returns:
        str: System prompt message
    """
    return """Du bist ein Experte für Lernplanung an Schweizer Universitäten.

DEINE AUFGABE:
Erstelle einen realistischen, umsetzbaren Lernplan basierend auf verfügbaren Zeitfenstern und Prüfungsterminen für Studenten.
Die Stundenten haben begrenzte Zeitfenster zum Lernen, da sie Arbeit, Vorlesungen und andere Verpflichtungen haben.

OUTPUT-FORMAT (NUR JSON, KEINE ZUSATZTEXTE):
[
  {
    "date": "YYYY-MM-DD",
    "start": "HH:MM",
    "end": "HH:MM", 
    "module": "Prüfungs-/Modulname",
    "topic": "Spezifisches Thema",
    "description": "Konkrete Handlung zum Lernen (1-2 Sätze)"
  }
]

SPRACHE: Alle Felder auf DEUTSCH
- Verwende: "vertiefen", "wiederholen", "üben", "erstellen", "durcharbeiten"

DESCRIPTIONS müssen sein:
✓ Konkret: "Kapitel 3-4 lesen, Formeln auf Karteikarten schreiben"
✓ Handlungsorientiert: Mit Verb beginnen
✗ Vage: "Vorbereitung", "Lernen", "Allgemeine Wiederholung"
"""


def build_user_prompt(data: dict) -> str:
    """
    Build the user prompt for study plan generation.
    
    Creates a comprehensive prompt with all the student's information,
    constraints, and instructions for the AI to generate an optimal study plan.
    
    Args:
        data (dict): Dictionary containing student's complete study context.
        
        Expected structure:
        {
            "semester_start": date,       # Study period start date
            "semester_end": date,         # Study period end date (latest deadline)
            "leistungsnachweise": [       # List of assessments to prepare for
                {
                    "title": str,         # Assessment name (e.g., "Data Science Prüfung")
                    "type": str,          # Type: "Prüfung", "Präsentation", "Hausarbeit", "Projektarbeit", "Sonstiges"
                    "deadline": date,     # Due date / exam date
                    "module": str | None, # Associated course/module name (optional)
                    "topics": [str],      # List of specific topics to cover
                    "priority": int,      # Urgency: 1 (low) to 5 (high)
                    "effort": int         # Expected workload: 1 (minimal) to 5 (intensive)
                },
                ...
            ],
            "preferences": {              # Learning preferences and constraints
                "spacing": bool,          # Enable spaced repetition?
                "interleaving": bool,     # Mix different subjects within days?
                "deep_work": bool,        # Use longer blocks for complex work?
                "short_sessions": bool,   # Use shorter blocks for theory?
                "rest_days": [str],       # Days with no studying (e.g., ["Sonntag"])
                "max_hours_day": int | None,      # Daily study limit (hours)
                "max_hours_week": int | None,     # Weekly study limit (hours)
                "min_session_duration": int,      # Minimum session length (minutes)
                "earliest_study_time": str,       # Daily window start "HH:MM"
                "latest_study_time": str,         # Daily window end "HH:MM"
                "preferred_times_of_day": [str]   # ["morning", "afternoon", "evening"]
            },
            "free_slots": [               # Available time slots (already filtered)
                {
                    "date": date,         # Date of the slot
                    "start": str,         # Start time "HH:MM"
                    "end": str,           # End time "HH:MM"
                    "hours": float        # Duration in hours
                },
                ...
            ]
        }
    
    Returns:
        str: Complete user prompt message with all constraints and preferences
    """
    
    # ===== EXTRACT AND VALIDATE ALL DATA =====
    semester_start = data.get('semester_start')
    semester_end = data.get('semester_end')
    leistungsnachweise = data.get('leistungsnachweise', [])
    preferences = data.get('preferences', {})
    free_slots = data.get('free_slots', [])
    
    # ===== PREPARE LEISTUNGSNACHWEISE (ASSESSMENTS) =====
    # Include ALL fields with clear explanations for the LLM
    ln_info = []
    for ln in leistungsnachweise:
        deadline_str = ln['deadline'].isoformat() if ln.get('deadline') else "No deadline specified"
        ln_info.append({
            "title": ln['title'],
            "type": ln['type'],  # e.g., "Prüfung", "Projektarbeit", "Präsentation"
            "deadline": deadline_str,
            "module": ln.get('module', 'No module specified'),
            "topics": ln.get('topics', []),  # List of specific topics to cover
            "priority": ln.get('priority', 3),  # 1=low, 5=high urgency
            "effort": ln.get('effort', 3)  # 1=minimal, 5=very intensive
        })
    
    # ===== PREPARE FREE SLOTS =====
    # Slots are already filtered for busy times, absences, and rest days
    free_slots_info = []
    for slot in free_slots:
        free_slots_info.append({
            "date": slot['date'].isoformat(),
            "start": slot['start'],
            "end": slot['end'],
            "hours": slot['hours']
        })
    
    # ===== EXTRACT TIME-OF-DAY PREFERENCES (SOFT) =====
    # LLM should PREFER these times but can intelligently choose others
    preferred_times = preferences.get('preferred_times_of_day', [])
    
    time_pref_parts = []
    if 'morning' in preferred_times:
        time_pref_parts.append('Morgen (06:00–11:00)')
    if 'afternoon' in preferred_times:
        time_pref_parts.append('Nachmittag (12:00–17:00)')
    if 'evening' in preferred_times:
        time_pref_parts.append('Abend (18:00–22:00)')
    
    time_pref_str = ', '.join(time_pref_parts) if time_pref_parts else 'Keine Präferenz - wähle vernünftige Zeiten'
    
    # ===== EXTRACT LEARNING STRATEGY PREFERENCES =====
    spacing = preferences.get('spacing', False)
    interleaving = preferences.get('interleaving', False)
    deep_work = preferences.get('deep_work', False)
    short_sessions = preferences.get('short_sessions', False)
    
    # ===== EXTRACT LIMITS AND CONSTRAINTS =====
    rest_days = preferences.get('rest_days', [])
    max_hours_day = preferences.get('max_hours_day', None)
    max_hours_week = preferences.get('max_hours_week', None)
    min_session_duration = preferences.get('min_session_duration', 60)
    
    # ===== BUILD THE COMPLETE, DETAILED PROMPT =====
    prompt = f"""Erstelle einen Lernplan für einen Schweizer Studenten.

═══════════════════════════════════════════════════════════
📅 ZEITRAUM: {semester_start.strftime('%d.%m.%Y')} - {semester_end.strftime('%d.%m.%Y')}
═══════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════
📚 PRÜFUNGEN & LEISTUNGSNACHWEISE
═══════════════════════════════════════════════════════════

{json.dumps(ln_info, indent=2, ensure_ascii=False)}

WICHTIGE FELDER:
• type: "Prüfung" = Theorie+Übungen / "Präsentation" = Folien+Üben / "Hausarbeit" = Recherche+Schreiben
• priority (1-5): 5=höchste Dringlichkeit, 1=niedrig
• effort (1-5): Bestimmt Gesamtstunden → 5=25-35h, 4=15-25h, 3=10-15h, 2=5-10h, 1=3-5h
• deadline: ⚠️ KEINE Sessions NACH diesem Datum planen!
• topics: Jedes Thema 2-3x einplanen (Lernen → Üben → Wiederholen)

═══════════════════════════════════════════════════════════
⏰ VERFÜGBARE ZEITFENSTER (bereits gefiltert!)
═══════════════════════════════════════════════════════════

{json.dumps(free_slots_info, indent=2, ensure_ascii=False)}

🚨 KRITISCH - LIES DAS GENAU:

Diese Slots schliessen bereits aus:
✓ Arbeit, Vorlesungen, andere Verpflichtungen  
✓ Ferien und Abwesenheiten
✓ Ruhetage

PFLICHT-REGELN:
1. Verwende NUR Slots aus dieser Liste
2. Datum, Start UND Ende müssen EXAKT übereinstimmen
3. KEINE eigenen Zeiten erfinden
4. Wenn kein Slot passt → Session weglassen

BEISPIEL:
Slot in Liste: {{"date": "2025-11-20", "start": "14:00", "end": "16:00"}}
✅ OK: "2025-11-20", "14:00", "16:00"
❌ FALSCH: "2025-11-20", "07:30", "09:30" (nicht in Liste = Student arbeitet! oder hat Vorlesung oder Ruhetag)

═══════════════════════════════════════════════════════════
PLANUNGS-STRATEGIE NACH TYP
═══════════════════════════════════════════════════════════

PRÜFUNG:
Phase 1 (60%): Grundlagen - "Kapitel X lesen und Zusammenfassung schreiben"
Phase 2 (30%): Üben - "15 Übungsaufgaben zu Thema Y lösen"  
Phase 3 (10%): Wiederholen - "Alle Karteikarten durchgehen, Probeprüfung"
Tag davor: Max 1-2h leichte Wiederholung

PRÄSENTATION:
Phase 1: Struktur - "Gliederung mit 5 Hauptpunkten erstellen"
Phase 2: Folien - "Einleitung-Slides gestalten (3-4 Folien)"
Phase 3: Üben - "Präsentation 2x laut durchgehen, Zeit stoppen"
Phase 4: Generalprobe - "Kompletter Durchlauf unter realen Bedingungen"

HAUSARBEIT/PROJEKT:
Phase 1: Recherche - "5-7 relevante Quellen finden und lesen"
Phase 2: Schreiben - "Einleitung verfassen (ca. 2 Seiten)"
Phase 3: Überarbeiten - "Hauptteil durchgehen, Argumentation schärfen"
Phase 4: Finalisieren - "Formatierung, Zitate prüfen, Korrekturlesen"

═══════════════════════════════════════════════════════════
⚙️ EINSTELLUNGEN
═══════════════════════════════════════════════════════════

Spaced Repetition: {spacing} {'→ Themen über mehrere Tage verteilen' if spacing else ''}
Interleaving: {interleaving} {'→ Fächer innerhalb eines Tages mischen' if interleaving else ''}
Deep Work: {deep_work} {'→ Längere Blöcke (90-120min) für komplexe Arbeit' if deep_work else ''}
Short Sessions: {short_sessions} {'→ Kürzere Blöcke (30-60min) für Theorie' if short_sessions else ''}

Bevorzugte Lernzeiten: {time_pref_str}
→ Die verfügbaren Slots wurden bereits auf diese Zeiten optimiert

🧠 INTELLIGENTE ZEITWAHL (WICHTIG!):
Die Slots in der Liste sind bereits gefiltert, ABER du musst trotzdem klug wählen:

1. WOCHENTAG-LOGIK:
   • Montag-Freitag: Nutze Slots ab 08:00 wenn frei sonst am abend, bevorzugt 09:00-17:00
   • Samstag: Nutze Slots ab 09:00, bevorzugt 10:00-16:00  
   • Sonntag: Nutze Slots ab 10:00, bevorzugt 11:00-16:00
   • Spätabends (nach 20:00): Nur für dringende Deadlines
   
2. REALITÄTSCHECK vor JEDER Session:
   ✓ Sonntag 14:00? → OK, vernünftig
   ✗ Sonntag 06:30? → NEIN! Zu früh, wähle späteren Slot
   ✓ Montag 09:00? → OK, normale Arbeitszeit
   ✗ Freitag 22:30? → NEIN! Zu spät, wähle früheren Slot
   
3. PRIORITÄT DER SLOT-AUSWAHL:
   a) Wochentag, normale Zeiten (Mo-Fr 09:00-17:00)
   b) Wochenende, vernünftige Zeiten (Sa-So 10:00-16:00)
   c) Frühabend (Mo-Fr 17:00-19:00)
   d) Notfälle: Spätabend oder frühe Zeiten (nur bei Deadline!)

Limits:
• Max {max_hours_day}h/Tag → OBERGRENZE, nicht Ziel! Nutze nur was nötig ist
• Max {max_hours_week if max_hours_week else '∞'}h/Woche → OBERGRENZE, nicht Ziel!
• Min {min_session_duration} Min/Session

⚠️ WICHTIG - SEI EIN KLUGER PLANER:
• Wähle Zeiten wie ein vernünftiger Student
• Nicht zu früh (07:00 am Wochenende? Nein!)
• Nicht zu spät (22:00 abends? Nur in Notfällen!)
• Pausen zwischen Sessions einbauen
• Realistische, nachhaltige Planung

═══════════════════════════════════════════════════════════
✅ VALIDIERUNG (für JEDE Session vor Ausgabe)
═══════════════════════════════════════════════════════════

1. ⚠️ Slot-Check: Gibt es einen Slot mit EXAKT diesem Datum+Start+Ende?
   Wenn NEIN → Session LÖSCHEN
   
2. Deadline-Check: Ist session.date < assessment.deadline?
   Wenn NEIN → Session LÖSCHEN
   
3. Sprache: Ist description auf Deutsch, konkret, handlungsorientiert?
   Wenn NEIN → Session LÖSCHEN

═══════════════════════════════════════════════════════════
📤 DEINE AUSGABE (NUR JSON!)
═══════════════════════════════════════════════════════════

Gib NUR ein JSON-Array zurück, KEINE Erklärungen:

[
  {{
    "date": "2025-11-20",
    "start": "14:00",
    "end": "16:00",
    "module": "Data Science Prüfung",
    "topic": "SQL Grundlagen",
    "description": "Kapitel 2-3 zu SQL-Syntax durcharbeiten, SELECT und JOIN verstehen"
  }}
]

Jetzt erstelle den Plan - realistisch, umsetzbar, mit konkreten Beschreibungen auf Deutsch:"""
    
    return prompt

