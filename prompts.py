"""
Prompt Templates für KI-Lernplaner

Dieses Modul enthält alle LLM-Prompt-Vorlagen für die Generierung von Lernplänen.
Die Trennung der Prompts vom Hauptcode ermöglicht einfache Anpassungen und
experimentelles Prompt Engineering ohne Änderungen an der UI-Logik.

Funktionen:
    - get_system_prompt(): System-Nachricht für das LLM (definiert Rolle und Verhalten)
    - build_user_prompt(data): Generiert den User-Prompt mit allen Kontext-Informationen
    - get_planning_tips(): Optionale Lern-Tipps für die UI

Anpassungen:
    Du kannst diese Prompts frei bearbeiten, um das Verhalten der KI zu ändern:
    - Mehr/weniger Details in der Ausgabe
    - Andere Lernstrategien betonen
    - Zusätzliche Constraints hinzufügen
    - Output-Format ändern (JSON-Struktur muss jedoch erhalten bleiben)

Autor: Fabian Locher
Projekt: SmartStudyAssistant
"""

import json


def get_system_prompt() -> str:
    """
    Get the system message for the AI study planner.
    
    Defines the AI's role as an expert educational planner and specifies
    the expected output format (JSON array).
    
    Returns:
        str: System prompt message
    """
    return """You are an expert educational planner assistant. You will be given a student's schedule availability, course information, and learning preferences. You create a detailed study plan fitting the free time slots and respecting the preferences.

Your response MUST be a valid JSON array only, with no additional text or markdown formatting. Each object in the array must have these fields:
- date: ISO format date string (YYYY-MM-DD)
- start: time in HH:MM format
- end: time in HH:MM format
- module: module/course name
- topic: specific topic being studied
- description: brief description of what to study in this session"""


def build_user_prompt(data: dict) -> str:
    """
    Build the user prompt for study plan generation.
    
    Creates a comprehensive prompt with all the student's information,
    constraints, and instructions for the AI to generate an optimal study plan.
    
    Args:
        data (dict): Dictionary containing:
            - semester_start (date): Semester start date
            - semester_end (date): Semester end date
            - leistungsnachweise (list): List of assessment dicts with title, type, deadline, module, topics, priority, effort
            - preferences (dict): Learning preferences and constraints
            - free_slots (list): Available time slots for studying
    
    Returns:
        str: Complete user prompt message
    """
    
    # Extract data
    semester_start = data.get('semester_start')
    semester_end = data.get('semester_end')
    leistungsnachweise = data.get('leistungsnachweise', [])
    preferences = data.get('preferences', {})
    free_slots = data.get('free_slots', [])
    
    # Prepare leistungsnachweise information
    ln_info = []
    for ln in leistungsnachweise:
        deadline_str = ln['deadline'].isoformat() if ln.get('deadline') else "No deadline specified"
        ln_info.append({
            "title": ln['title'],
            "type": ln['type'],
            "deadline": deadline_str,
            "module": ln.get('module', 'No module specified'),
            "topics": ln.get('topics', []),
            "priority": ln.get('priority', 3),
            "effort": ln.get('effort', 3)
        })
    
    # Prepare free slots information
    free_slots_info = []
    for slot in free_slots:
        free_slots_info.append({
            "date": slot['date'].isoformat(),
            "start": slot['start'],
            "end": slot['end'],
            "hours": slot['hours']
        })
    
    # Build the complete prompt
    prompt = f"""Create a detailed study plan with the following information:

SEMESTER DATES:
- Start: {semester_start.isoformat()}
- End: {semester_end.isoformat()}

ASSESSMENTS & EXAMS (Leistungsnachweise):
{json.dumps(ln_info, indent=2)}

LEARNING PREFERENCES:
- Spaced repetition: {preferences.get('spacing', False)}
- Interleaving of subjects: {preferences.get('interleaving', False)}
- Deep-work sessions for complex topics: {preferences.get('deep_work', False)}
- Short sessions for theory-heavy subjects: {preferences.get('short_sessions', False)}
- Rest days: {', '.join(preferences.get('rest_days', []))}
- Max hours per day: {preferences.get('max_hours_day', 'No limit')}
- Max hours per week: {preferences.get('max_hours_week', 'No limit')}
- Minimum session duration: {preferences.get('min_session_duration', 60)} minutes

AVAILABLE FREE TIME SLOTS:
{json.dumps(free_slots_info, indent=2)}

INSTRUCTIONS:
1. Assign each free slot to a study session for a specific assessment/exam and topic
2. Prioritize assessments with earlier deadlines or higher priority levels
3. Allocate more total study time to assessments with higher effort values (effort rating 1-5)
4. Apply spaced repetition if enabled: distribute topics over time with review sessions
5. Apply interleaving if enabled: mix different subjects/assessments within study days
6. Use longer sessions (2+ hours) for deep-work topics if enabled
7. Use shorter sessions (1-1.5 hours) for theory-heavy content if enabled
8. Ensure all topics are covered before their respective deadlines
9. Respect the maximum daily and weekly hour constraints
10. Create a balanced, sustainable study schedule

OUTPUT:
Return ONLY a JSON array of study sessions. Each session must have:
- date: ISO date (YYYY-MM-DD)
- start: time (HH:MM)
- end: time (HH:MM)
- module: the title of the assessment/exam (use the 'title' field from the data above)
- topic: specific topic to study
- description: brief description of the study session

Do not include any text before or after the JSON array."""
    
    return prompt


def get_planning_tips() -> str:
    """
    Get general study planning tips (optional, for display purposes).
    
    Returns:
        str: Study planning tips
    """
    return """
    **Effective Study Planning Tips:**
    
    1. **Spaced Repetition**: Review material multiple times over increasing intervals
    2. **Interleaving**: Mix different subjects to improve retention and transfer
    3. **Deep Work**: Schedule uninterrupted blocks for complex topics
    4. **Active Recall**: Test yourself instead of passive re-reading
    5. **Regular Breaks**: Use techniques like Pomodoro (25 min work, 5 min break)
    6. **Prioritize**: Focus on high-priority and time-sensitive topics first
    7. **Flexibility**: Allow buffer time for unexpected events
    8. **Track Progress**: Monitor completed sessions and adjust as needed
    """
