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
            - semester_start (date): Study plan start date
            - semester_end (date): Study plan end date (latest deadline)
            - leistungsnachweise (list): List of assessment dicts with:
                - title (str): Assessment name
                - type (str): Assessment type (Prüfung, Projektarbeit, etc.)
                - deadline (date): Due date
                - module (str, optional): Associated module/course
                - topics (list): List of topic strings
                - priority (int 1-5): Importance level
                - effort (int 1-5): Expected workload
            - preferences (dict): Learning preferences and constraints:
                - spacing (bool): Enable spaced repetition
                - interleaving (bool): Mix subjects within days
                - deep_work (bool): Use longer blocks for complex topics
                - short_sessions (bool): Use shorter blocks for theory
                - rest_days (list): Days with no studying (e.g. ["Sonntag"])
                - max_hours_day (int): Daily study limit
                - max_hours_week (int or None): Weekly study limit
                - min_session_duration (int): Minimum session length in minutes
                - earliest_study_time (str "HH:MM"): Daily start window
                - latest_study_time (str "HH:MM"): Daily end window
                - preferred_times_of_day (list): ["morning", "afternoon", "evening"]
            - free_slots (list): Available time slots with:
                - date (date): The date
                - start (str "HH:MM"): Slot start time
                - end (str "HH:MM"): Slot end time
                - hours (float): Duration in hours
    
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
    # All slots already respect user's daily time window (earliest/latest)
    free_slots_info = []
    for slot in free_slots:
        free_slots_info.append({
            "date": slot['date'].isoformat(),
            "start": slot['start'],
            "end": slot['end'],
            "hours": slot['hours']
        })
    
    # ===== EXTRACT TIME WINDOW CONSTRAINTS (HARD) =====
    # These are ABSOLUTE boundaries - LLM must never violate these
    earliest_study_time = preferences.get('earliest_study_time', '06:00')
    latest_study_time = preferences.get('latest_study_time', '22:00')
    
    # ===== EXTRACT TIME-OF-DAY PREFERENCES (SOFT) =====
    # LLM should PREFER these times but can use others if needed
    preferred_times = preferences.get('preferred_times_of_day', [])
    
    time_pref_parts = []
    if 'morning' in preferred_times:
        time_pref_parts.append('Morning (06:00–11:00)')
    if 'afternoon' in preferred_times:
        time_pref_parts.append('Afternoon (12:00–17:00)')
    if 'evening' in preferred_times:
        time_pref_parts.append('Evening (18:00–22:00)')
    
    time_pref_str = ', '.join(time_pref_parts) if time_pref_parts else 'No preference specified'
    
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
    prompt = f"""Create a detailed, personalized study plan based on the student's complete profile below.

╔══════════════════════════════════════════════════════════════╗
║                    STUDY PLAN TIME FRAME                      ║
╚══════════════════════════════════════════════════════════════╝

Start Date: {semester_start.isoformat()}
End Date: {semester_end.isoformat()}

The study plan covers this entire period. All assessments must be prepared before their respective deadlines.

╔══════════════════════════════════════════════════════════════╗
║              ASSESSMENTS & EXAMS TO PREPARE FOR               ║
╚══════════════════════════════════════════════════════════════╝

{json.dumps(ln_info, indent=2)}

INTERPRETATION GUIDE FOR ASSESSMENTS:
- "priority" (1-5): How urgent/important this assessment is
  → Higher priority = should get preferential scheduling and earlier start
  → Priority 5 assessments should begin preparation immediately
  → Priority 1 assessments can be scheduled more flexibly

- "effort" (1-5): Expected workload/difficulty
  → Higher effort = allocate MORE total study hours
  → Effort 5 might need 20-30+ hours total study time
  → Effort 1 might need only 3-5 hours total study time
  → Distribute these hours across multiple sessions using spaced repetition

- "topics": Specific content areas to cover
  → Each topic should appear in multiple sessions (review + practice)
  → Break complex topics into smaller sub-sessions
  → Use topic names in session descriptions

- "type": Assessment format
  → "Prüfung" (Exam): Focus on review, practice problems, memorization
  → "Projektarbeit" (Project): Allocate longer deep-work blocks
  → "Präsentation" (Presentation): Include preparation AND practice sessions

╔══════════════════════════════════════════════════════════════╗
║                 TIME WINDOW CONSTRAINTS (HARD)                ║
╚══════════════════════════════════════════════════════════════╝

ABSOLUTE STUDY TIME BOUNDARIES:
- Earliest allowed start time: {earliest_study_time}
- Latest allowed end time: {latest_study_time}

⚠️ CRITICAL: You MUST NOT schedule any session outside this window.
The free slots provided already respect this constraint.

╔══════════════════════════════════════════════════════════════╗
║            PREFERRED TIMES OF DAY (SOFT PREFERENCE)           ║
╚══════════════════════════════════════════════════════════════╝

Student prefers to study during:
- Morning (06:00–11:00): {'✓ PREFERRED' if 'morning' in preferred_times else '✗ Not preferred'}
- Afternoon (12:00–17:00): {'✓ PREFERRED' if 'afternoon' in preferred_times else '✗ Not preferred'}
- Evening (18:00–22:00): {'✓ PREFERRED' if 'evening' in preferred_times else '✗ Not preferred'}

Selected preferences: {time_pref_str}

INSTRUCTION: When choosing between available free slots:
1. FIRST, try to use slots in the preferred time-of-day windows
2. If preferred slots are insufficient, use any other available slots
3. This is a SOFT preference - meeting deadlines takes priority

╔══════════════════════════════════════════════════════════════╗
║                   LEARNING STYLE PREFERENCES                  ║
╚══════════════════════════════════════════════════════════════╝

SPACED REPETITION: {spacing}
{'→ ENABLED: Distribute each topic over multiple sessions with increasing intervals' if spacing else '→ DISABLED: You may group topic coverage more densely'}
{'→ Example: Study "Topic A" on Day 1, review on Day 3, final review on Day 7' if spacing else ''}

INTERLEAVING: {interleaving}
{'→ ENABLED: Mix different assessments/subjects within the same day or week' if interleaving else '→ DISABLED: You may focus on one assessment at a time in blocks'}
{'→ Example: Morning = Assessment A, Afternoon = Assessment B, Evening = Assessment A' if interleaving else ''}

DEEP WORK (Long focused blocks): {deep_work}
{'→ ENABLED: For complex topics, use longer sessions (2-3 hours) without breaks' if deep_work else '→ DISABLED: Keep most sessions around 1-1.5 hours'}
{'→ Apply to: Programming, math problems, project work, complex analysis' if deep_work else ''}

SHORT SESSIONS (For theory): {short_sessions}
{'→ ENABLED: For theory-heavy content, use shorter sessions (45-60 min) to maintain focus' if short_sessions else '→ DISABLED: Standard session lengths are fine'}
{'→ Apply to: Reading textbooks, memorizing definitions, reviewing lecture notes' if short_sessions else ''}

╔══════════════════════════════════════════════════════════════╗
║                    STUDY LIMITS & REST DAYS                   ║
╚══════════════════════════════════════════════════════════════╝

REST DAYS (no studying): {', '.join(rest_days) if rest_days else 'None - can study any day'}
→ The free slots already exclude these days

MAXIMUM HOURS PER DAY: {max_hours_day if max_hours_day else 'No limit'}
{'→ Do not exceed this daily limit across all sessions on the same date' if max_hours_day else '→ You can use all available free slots on a day'}

MAXIMUM HOURS PER WEEK: {max_hours_week if max_hours_week else 'No limit'}
{'→ Track cumulative hours and ensure no week exceeds this total' if max_hours_week else '→ Weekly totals are flexible'}

MINIMUM SESSION DURATION: {min_session_duration} minutes
→ Do not create sessions shorter than this (they are ineffective)
→ If a free slot is shorter than this, skip it or combine it with adjacent slots

╔══════════════════════════════════════════════════════════════╗
║                  AVAILABLE FREE TIME SLOTS                    ║
╚══════════════════════════════════════════════════════════════╝

{json.dumps(free_slots_info, indent=2)}

NOTE: These slots already exclude:
- Busy times (work, classes, commitments)
- Absence periods (vacations, trips)
- Rest days
- Times outside the allowed daily window ({earliest_study_time}–{latest_study_time})

╔══════════════════════════════════════════════════════════════╗
║                    DETAILED INSTRUCTIONS                      ║
╚══════════════════════════════════════════════════════════════╝

YOUR TASK: Create an optimal study schedule by:

1. ASSESSMENT PRIORITIZATION
   - Start with highest priority (5) and earliest deadline assessments
   - Allocate total study time proportional to effort rating
   - Ensure all topics are covered before their deadlines

2. TIME ALLOCATION BY EFFORT
   - Effort 5: Allocate 25-35 hours total across multiple sessions
   - Effort 4: Allocate 15-25 hours total
   - Effort 3: Allocate 10-15 hours total
   - Effort 2: Allocate 5-10 hours total
   - Effort 1: Allocate 3-5 hours total

3. SESSION DISTRIBUTION (if Spaced Repetition is enabled)
   - First exposure: Initial learning (60-70% of material)
   - Second session (2-3 days later): Review + extend (20-30% more)
   - Third session (5-7 days later): Final review + practice
   - More sessions if needed before deadline

4. SESSION TYPES BY ASSESSMENT TYPE
   - Prüfung (Exam): Study, Review, Practice Problems, Mock Test
   - Projektarbeit (Project): Research, Planning, Implementation, Testing, Documentation
   - Präsentation (Presentation): Content Prep, Slides, Practice, Final Rehearsal

5. TOPIC COVERAGE
   - Each topic from the topics list should appear in at least 2-3 sessions
   - Use specific topic names in session descriptions
   - Vary the focus: "Introduction to X", "Practice X", "Review X"

6. TIME-OF-DAY OPTIMIZATION
   - Prefer slots in student's preferred time windows when possible
   - Use non-preferred times only if necessary to meet all deadlines

7. LEARNING STRATEGY APPLICATION
   - Apply interleaving: Mix subjects if enabled
   - Apply deep work: Use 2-3 hour blocks for complex topics if enabled
   - Apply short sessions: Use 45-60 min blocks for theory if enabled

8. BALANCE AND SUSTAINABILITY
   - Spread study load evenly across weeks
   - Avoid cramming everything close to deadlines
   - Leave some buffer days before each deadline
   - Respect daily and weekly hour limits

9. QUALITY OVER QUANTITY
   - Every session must have a clear, specific goal
   - Include actionable descriptions: "Solve practice problems 1-10" not just "Study"
   - Align session duration with content depth

╔══════════════════════════════════════════════════════════════╗
║                      OUTPUT FORMAT                            ║
╚══════════════════════════════════════════════════════════════╝

Return ONLY a JSON array of study sessions (no markdown, no explanations).

Each session object must have exactly these fields:
{{
  "date": "YYYY-MM-DD",          // ISO format date
  "start": "HH:MM",              // 24-hour format, must be >= {earliest_study_time}
  "end": "HH:MM",                // 24-hour format, must be <= {latest_study_time}
  "module": "Assessment Title",  // Use the exact "title" from the assessments above
  "topic": "Specific Topic",     // One of the topics from the assessment's topic list
  "description": "Concrete action"  // What specifically to do in this session
}}

EXAMPLE SESSIONS:
[
  {{
    "date": "2025-01-15",
    "start": "14:00",
    "end": "16:00",
    "module": "AI Prüfung",
    "topic": "Kapitel 2 - Prompt Engineering",
    "description": "Read chapter 2, take notes on prompt design patterns, complete exercises 2.1-2.5"
  }},
  {{
    "date": "2025-01-17",
    "start": "09:00",
    "end": "10:30",
    "module": "AI Prüfung",
    "topic": "Kapitel 2 - Prompt Engineering",
    "description": "Review notes from last session, practice writing prompts for different use cases"
  }}
]

START GENERATING THE STUDY PLAN NOW:"""
    
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
