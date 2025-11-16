"""
KI-Lernplaner für Studierende

Eine Streamlit Web-Anwendung, die Studierenden hilft, einen KI-basierten Lernplan
für ihr Semester zu erstellen. Nutzt OpenAI GPT-4o-mini für intelligente Plan-Generierung.

Installation:
    pip install -r requirements.txt
    
Anwendung:
    streamlit run app.py

Autor: Locher, Wirth & Heiniger
Projekt: StudyPlanner
"""

import streamlit as st
from datetime import date, time, datetime, timedelta
import json
from openai import OpenAI
from fpdf import FPDF
from io import BytesIO

# Import prompt templates
from prompts import get_system_prompt, build_user_prompt


def calculate_free_slots():
    """
    Calculate all available free time slots for studying based on:
    - Semester date range
    - Recurring busy times
    - Absence periods
    - Rest days
    - Maximum daily study hours
    
    Returns:
        list: List of dicts with free time slots
              [{"date": date, "start": "HH:MM", "end": "HH:MM", "hours": float}, ...]
    """
    
    # Extract data from session state
    study_start = st.session_state.study_start
    study_end = st.session_state.study_end
    
    if not study_end:
        st.error("❌ Kein Enddatum verfügbar. Bitte füge mindestens einen Leistungsnachweis mit Fälligkeitsdatum hinzu.")
        return []
    
    busy_times = st.session_state.busy_times
    absences = st.session_state.absences
    rest_days = st.session_state.preferences.get("rest_days", [])
    max_hours_day = st.session_state.preferences.get("max_hours_day", None)
    
    # Map weekday numbers to names
    weekday_map = {
        0: "Monday",
        1: "Tuesday", 
        2: "Wednesday",
        3: "Thursday",
        4: "Friday",
        5: "Saturday",
        6: "Sunday"
    }
    
    free_slots = []
    
    # Iterate through each day in the semester
    current_date = study_start
    while current_date <= study_end:
        # Get weekday name
        weekday_name = weekday_map[current_date.weekday()]
        
        # Check if this is a rest day
        if weekday_name in rest_days:
            current_date += timedelta(days=1)
            continue
        
        # Check if this date falls within any absence period
        is_absent = False
        for absence in absences:
            if absence["start_date"] <= current_date <= absence["end_date"]:
                is_absent = True
                break
        
        if is_absent:
            current_date += timedelta(days=1)
            continue
        
        # Start with full potential study window (6:00 AM to 11:00 PM)
        study_start = time(6, 0)
        study_end = time(23, 0)
        
        # Create initial free intervals for this day
        free_intervals = [(study_start, study_end)]
        
        # Get all busy times that apply to this weekday
        applicable_busy_times = [bt for bt in busy_times if weekday_name in bt["days"]]
        
        # Subtract each busy time from the free intervals
        for busy in applicable_busy_times:
            busy_start = datetime.strptime(busy["start"], "%H:%M").time()
            busy_end = datetime.strptime(busy["end"], "%H:%M").time()
            
            new_free_intervals = []
            for free_start, free_end in free_intervals:
                # Subtract busy interval from this free interval
                result_intervals = subtract_time_interval(free_start, free_end, busy_start, busy_end)
                new_free_intervals.extend(result_intervals)
            
            free_intervals = new_free_intervals
        
        # Calculate total free hours for this day
        total_free_hours = sum([
            (datetime.combine(date.min, end) - datetime.combine(date.min, start)).total_seconds() / 3600
            for start, end in free_intervals
        ])
        
        # Apply max_hours_day limit if set
        if max_hours_day and total_free_hours > max_hours_day:
            # Truncate intervals to respect max daily hours
            free_intervals = truncate_intervals_to_max_hours(free_intervals, max_hours_day)
        
        # Convert intervals to output format
        for start_time, end_time in free_intervals:
            hours = (datetime.combine(date.min, end_time) - datetime.combine(date.min, start_time)).total_seconds() / 3600
            
            # Only include intervals with meaningful duration (at least 15 minutes)
            if hours >= 0.25:
                free_slots.append({
                    "date": current_date,
                    "start": start_time.strftime("%H:%M"),
                    "end": end_time.strftime("%H:%M"),
                    "hours": round(hours, 2)
                })
        
        current_date += timedelta(days=1)
    
    return free_slots


def subtract_time_interval(free_start, free_end, busy_start, busy_end):
    """
    Subtract a busy time interval from a free time interval.
    
    Args:
        free_start (time): Start of free interval
        free_end (time): End of free interval
        busy_start (time): Start of busy interval
        busy_end (time): End of busy interval
    
    Returns:
        list: List of tuples (start, end) representing remaining free intervals
    """
    
    # No overlap - return original interval
    if busy_end <= free_start or busy_start >= free_end:
        return [(free_start, free_end)]
    
    # Busy interval completely covers free interval - nothing left
    if busy_start <= free_start and busy_end >= free_end:
        return []
    
    # Busy interval is in the middle - split into two intervals
    if busy_start > free_start and busy_end < free_end:
        return [(free_start, busy_start), (busy_end, free_end)]
    
    # Busy interval overlaps beginning
    if busy_start <= free_start and busy_end < free_end:
        return [(busy_end, free_end)]
    
    # Busy interval overlaps end
    if busy_start > free_start and busy_end >= free_end:
        return [(free_start, busy_start)]
    
    # Default: return original (shouldn't reach here)
    return [(free_start, free_end)]


def truncate_intervals_to_max_hours(intervals, max_hours):
    """
    Truncate a list of time intervals to not exceed a maximum total duration.
    
    Args:
        intervals (list): List of (start_time, end_time) tuples
        max_hours (float): Maximum total hours allowed
    
    Returns:
        list: Truncated list of intervals
    """
    result = []
    accumulated_hours = 0.0
    
    for start_time, end_time in intervals:
        interval_hours = (datetime.combine(date.min, end_time) - datetime.combine(date.min, start_time)).total_seconds() / 3600
        
        if accumulated_hours >= max_hours:
            break
        
        if accumulated_hours + interval_hours <= max_hours:
            # This interval fits completely
            result.append((start_time, end_time))
            accumulated_hours += interval_hours
        else:
            # Partial interval - truncate to fit remaining hours
            remaining_hours = max_hours - accumulated_hours
            remaining_seconds = int(remaining_hours * 3600)
            new_end_time = (datetime.combine(date.min, start_time) + timedelta(seconds=remaining_seconds)).time()
            result.append((start_time, new_end_time))
            accumulated_hours = max_hours
            break
    
    return result


def generate_plan_via_ai():
    """
    Generate a detailed study plan using OpenAI ChatCompletion API.
    
    Uses the user's modules, preferences, and free slots to create an optimized
    study schedule that respects constraints and learning strategies.
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    # Validate preconditions
    if not st.session_state.openai_key:
        st.error("❌ OpenAI API-Schlüssel fehlt. Bitte konfiguriere ihn auf der Einrichtungs-Seite.")
        return False
    
    if not st.session_state.leistungsnachweise:
        st.error("❌ Keine Leistungsnachweise definiert. Bitte füge Leistungsnachweise auf der Einrichtungs-Seite hinzu.")
        return False
    
    if not st.session_state.get("free_slots"):
        st.error("❌ Keine freien Zeitfenster berechnet. Bitte berechne zuerst die freien Zeitfenster.")
        return False
    
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=st.session_state.openai_key)
        
        # Prepare data for prompt building
        prompt_data = {
            'semester_start': st.session_state.study_start,
            'semester_end': st.session_state.study_end,
            'leistungsnachweise': st.session_state.leistungsnachweise,
            'preferences': st.session_state.preferences,
            'free_slots': st.session_state.free_slots
        }
        
        # Get prompts from prompts module
        system_message = get_system_prompt()
        user_message = build_user_prompt(prompt_data)
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        
        # Extract response content
        response_content = response.choices[0].message.content.strip()
        
        # Try to parse as JSON
        try:
            # First, try direct parsing
            plan = json.loads(response_content)
        except json.JSONDecodeError:
            # Try to extract JSON array from potential markdown formatting
            if "```json" in response_content:
                # Extract content between ```json and ```
                start_idx = response_content.find("```json") + 7
                end_idx = response_content.find("```", start_idx)
                json_content = response_content[start_idx:end_idx].strip()
                plan = json.loads(json_content)
            elif "```" in response_content:
                # Extract content between ``` and ```
                start_idx = response_content.find("```") + 3
                end_idx = response_content.find("```", start_idx)
                json_content = response_content[start_idx:end_idx].strip()
                plan = json.loads(json_content)
            else:
                raise
        
        # Validate that plan is a list
        if not isinstance(plan, list):
            st.error("❌ KI-Antwort ist keine gültige Liste von Lerneinheiten.")
            return False
        
        # Store in session state
        st.session_state.plan = plan
        
        return True
        
    except json.JSONDecodeError as e:
        st.error(f"❌ Fehler beim Parsen der KI-Antwort als JSON: {str(e)}")
        st.error("Rohe Antwort (erste 500 Zeichen):")
        st.code(response_content[:500] if 'response_content' in locals() else "Keine Antwort")
        return False
    
    except Exception as e:
        st.error(f"❌ Fehler beim Generieren des Plans: {str(e)}")
        return False


def init_session_state():
    """
    Initialize all session state variables if they don't exist yet.
    This ensures data persistence across page interactions.
    """
    # Study plan dates
    if "study_start" not in st.session_state:
        st.session_state.study_start = date.today()
    
    if "study_end" not in st.session_state:
        st.session_state.study_end = None  # Wird automatisch aus Prüfungsdaten berechnet
    
    # Leistungsnachweise (exams, assignments, presentations)
    if "leistungsnachweise" not in st.session_state:
        st.session_state.leistungsnachweise = []
    
    # Busy times (when student cannot study)
    if "busy_times" not in st.session_state:
        st.session_state.busy_times = []
    
    # Absences (vacations, trips, etc.)
    if "absences" not in st.session_state:
        st.session_state.absences = []
    
    # User preferences (study style, daily limits, etc.)
    if "preferences" not in st.session_state:
        st.session_state.preferences = {}
    
    # Generated study plan
    if "plan" not in st.session_state:
        st.session_state.plan = []
    
    # OpenAI API key
    if "openai_key" not in st.session_state:
        st.session_state.openai_key = ""


def main():
    """
    Main application entry point.
    Sets up the page configuration, navigation, and routing.
    """
    # Initialize session state
    init_session_state()
    
    # Page configuration
    st.set_page_config(
        page_title="KI-Lernplaner",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Main title and description
    st.title("📚 KI-Lernplaner für Studierende")
    st.markdown("""
    Willkommen beim **KI-Lernplaner**! Diese Anwendung hilft dir, einen personalisierten, 
    KI-generierten Lernplan basierend auf deinen Prüfungen, Leistungsnachweisen, Verfügbarkeit und Lernpräferenzen zu erstellen.
    
    Nutze das Navigationsmenü links, um zu beginnen.
    """)
    
    st.markdown("---")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    st.sidebar.markdown("Wähle einen Bereich aus:")
    
    page = st.sidebar.radio(
        "Gehe zu:",
        ["Einrichtung", "Lernplan", "Anpassungen", "Export"],
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info("💡 Beginne mit **Einrichtung**, um deine Prüfungen und Leistungsnachweise zu erfassen.")
    
    # Route to the selected page
    if page == "Einrichtung":
        show_setup_page()
    elif page == "Lernplan":
        show_plan_page()
    elif page == "Anpassungen":
        show_adjustments_page()
    elif page == "Export":
        show_export_page()


def show_setup_page():
    """
    Setup page - Wizard for entering assessments, exams, and basic configuration.
    """
    st.header("⚙️ Einrichtungs-Assistent")
    st.markdown("Konfiguriere dein Semester, deine Leistungsnachweise und API-Einstellungen, um zu beginnen.")
    
    # ========== SECTION 1: STUDY PLAN START DATE ==========
    st.subheader("1️⃣ Start deines Lernplans")
    st.markdown("Ab wann möchtest du aktiv mit dem Lernen beginnen?")
    
    study_start = st.date_input(
        "Lernplan-Start",
        value=st.session_state.study_start,
        help="Ab wann möchtest du aktiv mit dem Lernen beginnen?"
    )
    st.session_state.study_start = study_start
    
    # Automatically calculate study_end from latest deadline
    if st.session_state.leistungsnachweise:
        deadlines = [ln['deadline'] for ln in st.session_state.leistungsnachweise if ln.get('deadline')]
        if deadlines:
            st.session_state.study_end = max(deadlines)
            st.info(f"ℹ️ Der Lernplan endet automatisch am Tag deines letzten Leistungsnachweises: **{st.session_state.study_end.strftime('%d.%m.%Y')}**")
        else:
            st.session_state.study_end = None
            st.info("ℹ️ Bitte gib zuerst mindestens einen Leistungsnachweis mit Fälligkeitsdatum ein.")
    else:
        st.session_state.study_end = None
        st.info("ℹ️ Bitte gib zuerst mindestens einen Leistungsnachweis mit Fälligkeitsdatum ein.")
    
    st.markdown("---")
    
    # ========== SECTION 2: LEISTUNGSNACHWEISE ==========
    st.subheader("2️⃣ Prüfungen & Leistungsnachweise")
    st.markdown("Füge alle Prüfungen, Hausarbeiten, Projekte oder Präsentationen hinzu, die du in diesem Semester abschliessen musst.")
    
    # Form to add new Leistungsnachweis
    with st.form("add_leistungsnachweis_form", clear_on_submit=True):
        st.markdown("**Neuen Leistungsnachweis hinzufügen:**")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            ln_title = st.text_input(
                "Titel des Leistungsnachweises",
                placeholder="z.B. Klausur Höhere Mathematik, Seminararbeit, Projektpräsentation",
                help="Der Titel deiner Prüfung, Arbeit oder Präsentation"
            )
        
        with col2:
            ln_type = st.selectbox(
                "Typ",
                ["Prüfung", "Hausarbeit", "Präsentation", "Projektarbeit", "Sonstiges"],
                help="Art des Leistungsnachweises"
            )
        
        col3, col4 = st.columns([2, 2])
        
        with col3:
            ln_deadline = st.date_input(
                "Fälligkeitsdatum / Prüfungsdatum",
                value=None,
                help="Wann findet die Prüfung statt oder ist die Abgabe fällig?"
            )
        
        with col4:
            ln_module = st.text_input(
                "Zugehöriges Modul (optional)",
                placeholder="z.B. Höhere Mathematik I",
                help="Falls dieser Leistungsnachweis zu einem bestimmten Kurs/Modul gehört"
            )
        
        ln_topics_input = st.text_area(
            "Themen / Inhalte (optional)",
            placeholder="Gib ein Thema pro Zeile ein, z.B.:\nKapitel 1: Analysis\nKapitel 2: Lineare Algebra\nAbschlussprojekt",
            help="Liste die Hauptthemen oder Aufgaben für diesen Leistungsnachweis auf (eines pro Zeile)",
            height=100
        )
        
        col5, col6 = st.columns(2)
        
        with col5:
            ln_priority = st.slider(
                "Prioritätsstufe",
                min_value=1,
                max_value=5,
                value=3,
                help="Wie wichtig ist dieser Leistungsnachweis? (1=niedrig, 5=hoch)"
            )
        
        with col6:
            ln_effort = st.slider(
                "Lernaufwand",
                min_value=1,
                max_value=5,
                value=3,
                help="Wie viel Lernaufwand braucht dieser Leistungsnachweis? (1 = wenig, 5 = sehr viel)"
            )
        
        submitted = st.form_submit_button("➕ Leistungsnachweis hinzufügen", use_container_width=True)
        
        if submitted:
            if ln_title.strip():
                # Parse topics from textarea (one per line, filter empty lines)
                topics_list = [t.strip() for t in ln_topics_input.split('\n') if t.strip()]
                
                # Create leistungsnachweis dict
                new_ln = {
                    "title": ln_title,
                    "type": ln_type,
                    "deadline": ln_deadline,
                    "module": ln_module if ln_module.strip() else None,
                    "topics": topics_list,
                    "priority": ln_priority,
                    "effort": ln_effort
                }
                
                # Add to session state
                st.session_state.leistungsnachweise.append(new_ln)
                st.success(f"✅ Leistungsnachweis '{ln_title}' erfolgreich hinzugefügt!")
                st.rerun()
            else:
                st.error("⚠️ Bitte gib einen Titel für den Leistungsnachweis ein.")
    
    # Display existing Leistungsnachweise
    if st.session_state.leistungsnachweise:
        st.markdown("---")
        st.markdown("**📚 Deine Leistungsnachweise:**")
        
        for idx, ln in enumerate(st.session_state.leistungsnachweise):
            # Build expander title
            expander_title = f"**{ln['title']}** ({ln['type']}) - Priorität: {ln.get('priority', 3)}/5, Lernaufwand: {ln.get('effort', 3)}/5"
            
            with st.expander(expander_title, expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    if ln['deadline']:
                        st.write(f"📅 **Fälligkeitsdatum:** {ln['deadline'].strftime('%d. %B %Y')}")
                    else:
                        st.write("📅 **Fälligkeitsdatum:** Nicht angegeben")
                    
                    if ln.get('module'):
                        st.write(f"📚 **Zugehöriges Modul:** {ln['module']}")
                    
                    if ln['topics']:
                        st.write(f"📝 **Themen ({len(ln['topics'])}):**")
                        for topic in ln['topics']:
                            st.write(f"  • {topic}")
                    else:
                        st.write("📝 **Themen:** Keine angegeben")
                
                with col2:
                    if st.button("🗑️ Entfernen", key=f"remove_ln_{idx}", use_container_width=True):
                        st.session_state.leistungsnachweise.pop(idx)
                        st.success(f"Leistungsnachweis '{ln['title']}' entfernt.")
                        st.rerun()
        
        # Summary
        st.info(f"📊 Total Leistungsnachweise: {len(st.session_state.leistungsnachweise)}")
    else:
        st.info("ℹ️ Noch keine Leistungsnachweise hinzugefügt. Nutze das Formular oben, um deinen ersten Leistungsnachweis hinzuzufügen.")
    
    st.markdown("---")
    
    # ========== SECTION 3: API KEY ==========
    st.subheader("3️⃣ OpenAI API-Konfiguration")
    st.markdown("Gib deinen OpenAI API-Schlüssel ein, um die KI-gestützte Lernplan-Generierung zu aktivieren.")
    
    api_key = st.text_input(
        "OpenAI API-Schlüssel",
        value=st.session_state.openai_key,
        type="password",
        placeholder="sk-...",
        help="Dein API-Schlüssel wird sicher in der Sitzung gespeichert und nie angezeigt"
    )
    st.session_state.openai_key = api_key
    
    if api_key:
        st.success("✅ API-Schlüssel konfiguriert")
    else:
        st.warning("⚠️ Kein API-Schlüssel eingegeben. KI-Funktionen sind nicht verfügbar.")
    
    st.markdown("---")
    
    # ========== SECTION 4: BUSY TIMES (RECURRING WEEKLY SCHEDULE) ==========
    st.subheader("4️⃣ Wiederkehrende belegte Zeiten")
    st.markdown("Definiere deine regelmässigen wöchentlichen Verpflichtungen (Arbeit, Vorlesungen, Sport etc.), damit der Planer weiss, wann du nicht verfügbar bist.")
    
    # Form to add busy interval
    with st.form("add_busy_time_form", clear_on_submit=True):
        st.markdown("**Neue belegte Zeit hinzufügen:**")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            busy_label = st.text_input(
                "Bezeichnung",
                placeholder="z.B. Arbeit, Vorlesung, Fitnessstudio, Nebenjob",
                help="z.B. Arbeit, Vorlesung, Fitnessstudio, Nebenjob"
            )
            
            busy_days = st.multiselect(
                "Wochentage",
                ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"],
                help="Wähle alle Tage aus, an denen diese belegte Zeit auftritt"
            )
        
        with col2:
            busy_start = st.time_input(
                "Startzeit",
                value=None,
                help="Wann beginnt diese Verpflichtung?"
            )
            
            busy_end = st.time_input(
                "Endzeit",
                value=None,
                help="Wann endet diese Verpflichtung?"
            )
        
        submitted_busy = st.form_submit_button("➕ Neue belegte Zeit hinzufügen", use_container_width=True)
        
        if submitted_busy:
            if busy_label.strip() and busy_days and busy_start and busy_end:
                # Convert time objects to string format for storage
                new_busy_time = {
                    "label": busy_label,
                    "days": busy_days,
                    "start": busy_start.strftime("%H:%M"),
                    "end": busy_end.strftime("%H:%M")
                }
                
                st.session_state.busy_times.append(new_busy_time)
                st.success(f"✅ Belegte Zeit '{busy_label}' hinzugefügt!")
                st.rerun()
            else:
                st.error("⚠️ Bitte fülle alle Felder aus (Bezeichnung, Tage, Startzeit und Endzeit).")
    
    st.info("💡 Diese Zeiten werden bei der Berechnung deiner freien Lernfenster automatisch ausgeschlossen.")
    
    # Display existing busy times
    if st.session_state.busy_times:
        st.markdown("**📅 Deine belegten Zeiten:**")
        
        for idx, busy in enumerate(st.session_state.busy_times):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                days_str = ", ".join(busy['days'])
                st.write(f"🔸 **{busy['label']}**: {days_str} von {busy['start']} bis {busy['end']}")
            
            with col2:
                if st.button("🗑️", key=f"remove_busy_{idx}", use_container_width=True):
                    st.session_state.busy_times.pop(idx)
                    st.success("Belegte Zeit entfernt.")
                    st.rerun()
        
        st.info(f"📊 Total belegte Zeitfenster: {len(st.session_state.busy_times)}")
    else:
        st.info("ℹ️ Noch keine belegten Zeiten hinzugefügt. Nutze das Formular oben, um deine Verpflichtungen hinzuzufügen.")
    
    st.markdown("---")
    
    # ========== SECTION 5: ABSENCES / EXCEPTIONS ==========
    st.subheader("5️⃣ Abwesenheiten & Ausnahmen")
    st.markdown("Definiere Zeiträume, in denen du komplett nicht verfügbar bist (Ferien, Militärdienst, Events etc.).")
    
    # Form to add absence
    with st.form("add_absence_form", clear_on_submit=True):
        st.markdown("**Neue Abwesenheitsperiode hinzufügen:**")
        
        col1, col2, col3 = st.columns([2, 2, 2])
        
        with col1:
            absence_start = st.date_input(
                "Startdatum",
                value=None,
                help="Erster Tag deiner Abwesenheit"
            )
        
        with col2:
            absence_end = st.date_input(
                "Enddatum",
                value=None,
                help="Letzter Tag deiner Abwesenheit"
            )
        
        with col3:
            absence_label = st.text_input(
                "Bezeichnung (optional)",
                placeholder="z.B. Ferien, Militär, Konferenz",
                help="Beschreibung dieser Abwesenheit"
            )
        
        submitted_absence = st.form_submit_button("➕ Abwesenheit hinzufügen", use_container_width=True)
        
        if submitted_absence:
            if absence_start and absence_end:
                if absence_end >= absence_start:
                    new_absence = {
                        "start_date": absence_start,
                        "end_date": absence_end,
                        "label": absence_label if absence_label.strip() else "Abwesenheit"
                    }
                    
                    st.session_state.absences.append(new_absence)
                    st.success(f"✅ Abwesenheitsperiode hinzugefügt!")
                    st.rerun()
                else:
                    st.error("⚠️ Enddatum muss gleich oder nach dem Startdatum liegen.")
            else:
                st.error("⚠️ Bitte wähle Start- und Enddatum aus.")
    
    # Display existing absences
    if st.session_state.absences:
        st.markdown("**🚫 Deine Abwesenheitsperioden:**")
        
        for idx, absence in enumerate(st.session_state.absences):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                days_count = (absence['end_date'] - absence['start_date']).days + 1
                st.write(f"🔸 **{absence['label']}**: {absence['start_date'].strftime('%d. %b %Y')} → {absence['end_date'].strftime('%d. %b %Y')} ({days_count} Tage)")
            
            with col2:
                if st.button("🗑️", key=f"remove_absence_{idx}", use_container_width=True):
                    st.session_state.absences.pop(idx)
                    st.success("Abwesenheit entfernt.")
                    st.rerun()
        
        st.info(f"📊 Total Abwesenheitsperioden: {len(st.session_state.absences)}")
    else:
        st.info("ℹ️ Noch keine Abwesenheiten hinzugefügt. Füge Perioden hinzu, in denen du nicht verfügbar bist.")
    
    st.markdown("---")
    
    # ========== SECTION 6: REST DAYS & STUDY LIMITS ==========
    st.subheader("6️⃣ Ruhetage & Lern-Limits")
    st.markdown("Konfiguriere deine bevorzugten Ruhetage und maximale tägliche/wöchentliche Lernstunden.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        rest_days = st.multiselect(
            "Ruhetage (kein Lernen)",
            ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"],
            default=st.session_state.preferences.get("rest_days", []),
            help="Tage, an denen du komplett ruhen möchtest (keine Lerneinheiten werden eingeplant)"
        )
        
        max_hours_day = st.number_input(
            "Max. Lernstunden pro Tag",
            min_value=1,
            max_value=24,
            value=st.session_state.preferences.get("max_hours_day", 8),
            help="Maximale Anzahl Stunden, die du an einem Tag lernen möchtest"
        )
    
    with col2:
        max_hours_week = st.number_input(
            "Max. Lernstunden pro Woche (optional)",
            min_value=0,
            max_value=168,
            value=st.session_state.preferences.get("max_hours_week", 40),
            help="Maximale totale Lernstunden pro Woche (0 = kein Limit)"
        )
        
        min_session_duration = st.number_input(
            "Minimale Einheiten-Dauer (Minuten)",
            min_value=15,
            max_value=240,
            value=st.session_state.preferences.get("min_session_duration", 60),
            step=15,
            help="Kürzeste akzeptable Lerneinheit-Länge"
        )
    
    # Update preferences in session state
    st.session_state.preferences.update({
        "rest_days": rest_days,
        "max_hours_day": max_hours_day,
        "max_hours_week": max_hours_week if max_hours_week > 0 else None,
        "min_session_duration": min_session_duration
    })
    
    st.success("✅ Einstellungen automatisch gespeichert")
    
    st.markdown("---")
    
    # ========== SECTION 7: LEARNING PREFERENCES ==========
    st.subheader("7️⃣ Lernpräferenzen")
    st.markdown("Hier kannst du festlegen, wie dein Lernplan aufgebaut werden soll. Wenn du unsicher bist, kannst du auch einfach die empfohlenen Einstellungen verwenden.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        spacing = st.checkbox(
            "Wiederholen mit Abständen (Spaced Repetition)",
            value=st.session_state.preferences.get("spacing", True),
            help="Der Stoff wird mehrmals über mehrere Tage/Wochen verteilt wiederholt, statt alles kurz vor der Prüfung zu lernen. Gut für Fächer mit viel Theorie und Definitionen."
        )
        
        interleaving = st.checkbox(
            "Fächer mischen (Interleaving)",
            value=st.session_state.preferences.get("interleaving", False),
            help="Verschiedene Fächer oder Themen werden innerhalb einer Woche gemischt statt in grossen Blöcken gelernt. Hilft, Inhalte besser zu unterscheiden – sinnvoll, wenn du mehrere ähnliche Fächer parallel hast."
        )
    
    with col2:
        deep_work = st.checkbox(
            "Längere Fokus-Blöcke für schwierige Themen (Deep Work)",
            value=st.session_state.preferences.get("deep_work", True),
            help="Plane längere, ungestörte Lernblöcke für anspruchsvolle Module, Projekte oder rechenintensive Aufgaben. Empfohlen für Programmierung, Mathe, Projektarbeiten usw."
        )
        
        short_sessions = st.checkbox(
            "Kürzere Einheiten für theorielastige Fächer",
            value=st.session_state.preferences.get("short_sessions", False),
            help="Teilt lernintensive Theorie-Fächer in kürzere, besser verdauliche Einheiten (z.B. 30–45 Minuten) auf. Hilft, Überforderung zu vermeiden und konzentriert zu bleiben."
        )
    
    # Update learning preferences in session state
    st.session_state.preferences.update({
        "spacing": spacing,
        "interleaving": interleaving,
        "deep_work": deep_work,
        "short_sessions": short_sessions
    })
    
    st.success("✅ Lernpräferenzen gespeichert")
    
    # Detailed explanations expander
    with st.expander("ℹ️ Was bedeuten diese Lernstrategien?"):
        st.markdown("""
        ### 🔄 Wiederholen mit Abständen (Spaced Repetition)
        
        **Was ist das?**  
        Du wiederholst den Stoff mehrere Male mit wachsenden Abständen, statt alles am Ende zu büffeln. 
        Die KI plant automatisch Wiederholungs-Sessions ein, die über mehrere Tage oder Wochen verteilt sind.
        
        **Geeignet für:**  
        Sprachen, Recht, Medizin, theoretische Fächer, Definitionen, Vokabeln
        
        **Typische Methoden:**
        - Karteikarten (z.B. Begriffe, Definitionen, Formeln)
        - Kurze Wiederholungs-Sessions
        - Zusammenfassungen immer wieder durchgehen
        
        ---
        
        ### 🔀 Fächer mischen (Interleaving)
        
        **Was ist das?**  
        Du lernst verschiedene Themen oder Fächer im Wechsel, statt einen ganzen Tag nur ein Fach zu machen. 
        Die KI mischt verschiedene Leistungsnachweise innerhalb derselben Woche.
        
        **Geeignet für:**  
        Wenn du mehrere ähnliche Fächer hast, die du leicht durcheinanderbringst (z.B. mehrere BWL-Module, verschiedene Programmiersprachen)
        
        **Typische Methoden:**
        - Lernblöcke im Plan mischen (z.B. Mathe → Recht → Mathe → BWL)
        - Verschiedene Aufgabentypen abwechseln
        - Verhindert Monotonie und fördert Transfer zwischen Themen
        
        ---
        
        ### 💪 Längere Fokus-Blöcke (Deep Work)
        
        **Was ist das?**  
        Längere, ungestörte Konzentrationsphasen (60–120 Minuten) für komplexe Aufgaben. 
        Die KI plant gezielt längere Zeitblöcke für anspruchsvolle Leistungsnachweise ein.
        
        **Geeignet für:**  
        Programmierung, Projektarbeiten, komplexe Mathe-Aufgaben, Reports, Analysen
        
        **Typische Methoden:**
        - 60–90 Minuten fokussiert arbeiten ohne Unterbrechung
        - Handy weg, keine Ablenkung
        - Schwierige Übungsaufgaben durcharbeiten
        - Code schreiben oder debuggen
        
        ---
        
        ### ⏱️ Kürzere Einheiten für Theorie
        
        **Was ist das?**  
        Lernzeit in kurze, fokussierte Einheiten (z.B. 25–45 Minuten) aufteilen. 
        Die KI plant kürzere Sessions für sehr theorielastige Inhalte.
        
        **Geeignet für:**  
        Sehr theorielastige Fächer oder wenn deine Konzentration schnell nachlässt
        
        **Typische Methoden:**
        - Pomodoro-Technik (25 Min. lernen, 5 Min. Pause)
        - Nach jeder Einheit kurze Pause
        - Kleine Teilziele pro Einheit (z.B. 1 Kapitel, 10 Karteikarten)
        - Verhindert mentale Erschöpfung bei trockener Theorie
        """)
        
        st.info("💡 **Empfehlung für den Start:** Wenn du unsicher bist, aktiviere **Wiederholen mit Abständen** + **Längere Fokus-Blöcke für schwierige Themen**. Du kannst die Einstellungen später jederzeit auf der Anpassungen-Seite ändern.")
    
    st.markdown("---")
    
    st.markdown("---")
    
    # ========== SETUP SUMMARY ==========
    st.subheader("📋 Einrichtungs-Zusammenfassung")
    st.markdown("Überprüfe deine Konfiguration, bevor du deinen Lernplan generierst.")
    
    # Create summary data
    num_leistungsnachweise = len(st.session_state.leistungsnachweise)
    num_busy_times = len(st.session_state.busy_times)
    num_absences = len(st.session_state.absences)
    has_api_key = bool(st.session_state.openai_key)
    
    # Display summary in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.study_end:
            duration_days = (st.session_state.study_end - st.session_state.study_start).days
            st.metric("Lernplan-Dauer", 
                      f"{duration_days} Tage")
        else:
            st.metric("Lernplan-Dauer", "Noch nicht definiert")
        st.metric("Leistungsnachweise", num_leistungsnachweise)
        st.metric("API-Schlüssel", "✅ Gesetzt" if has_api_key else "❌ Fehlt")
    
    with col2:
        st.metric("Belegte Zeitintervalle", num_busy_times)
        st.metric("Abwesenheiten", num_absences)
        rest_days_count = len(st.session_state.preferences.get("rest_days", []))
        st.metric("Ruhetage pro Woche", rest_days_count)
    
    with col3:
        max_hours = st.session_state.preferences.get("max_hours_day", 0)
        st.metric("Max. Stunden/Tag", max_hours)
        max_week = st.session_state.preferences.get("max_hours_week", 0)
        st.metric("Max. Stunden/Woche", max_week if max_week else "Kein Limit")
        st.metric("Min. Einheit (Min.)", st.session_state.preferences.get("min_session_duration", 60))
    
    # Detailed Leistungsnachweise list
    if num_leistungsnachweise > 0:
        with st.expander("📚 Details zu deinen Leistungsnachweisen"):
            for ln in st.session_state.leistungsnachweise:
                deadline_str = f" - Fällig: {ln['deadline'].strftime('%d %b %Y')}" if ln.get('deadline') else ""
                module_str = f" [{ln['module']}]" if ln.get('module') else ""
                topics_count = len(ln['topics']) if ln['topics'] else 0
                st.write(f"• **{ln['title']}** ({ln['type']}){module_str} (Priorität {ln['priority']}/5, Aufwand {ln['effort']}/5{deadline_str}) - {topics_count} Themen")
    
    # Learning strategies summary
    with st.expander("🎯 Aktive Lernstrategien"):
        strategies = []
        if st.session_state.preferences.get("spacing"):
            strategies.append("✅ Spaced Repetition")
        if st.session_state.preferences.get("interleaving"):
            strategies.append("✅ Interleaving von Fächern")
        if st.session_state.preferences.get("deep_work"):
            strategies.append("✅ Deep-Work-Einheiten für komplexe Themen")
        if st.session_state.preferences.get("short_sessions"):
            strategies.append("✅ Kurze Einheiten für theorielastige Fächer")
        
        if strategies:
            for strategy in strategies:
                st.write(strategy)
        else:
            st.write("Keine spezifischen Lernstrategien ausgewählt")
    
    st.markdown("---")
    
    # ========== GUIDANCE & NEXT STEPS ==========
    st.info("""
    **💡 So funktioniert's:**
    
    Der KI-Planer nutzt:
    - Deine **belegten Zeiten**, um Lerneinheiten nicht während Arbeit/Vorlesungen zu planen
    - Deine **Abwesenheiten**, um diese Zeiträume komplett zu überspringen
    - Deine **Ruhetage**, damit du Zeit zum Erholen hast
    - Deine **Lern-Limits**, um einen nachhaltigen, ausgewogenen Zeitplan zu erstellen
    - Deine **Lernpräferenzen**, um die Lernstrategie zu optimieren
    
    All diese Informationen werden kombiniert, um optimale freie Zeitfenster zu berechnen, wenn du deinen Plan generierst.
    """)
    
    st.markdown("---")
    
    # ========== NEXT STEPS ==========
    
    # Check if minimum requirements are met
    setup_complete = (
        num_leistungsnachweise > 0 and
        has_api_key and
        st.session_state.study_end is not None
    )
    
    if setup_complete:
        st.success("""
        **✅ Einrichtung abgeschlossen!**
        
        Du hast alle notwendigen Informationen konfiguriert. Du bist bereit, deinen KI-gestützten Lernplan zu generieren!
        """)
        
        st.info("👉 **Nächster Schritt:** Wechsle zur **'Lernplan'**-Seite im Navigations-Menü, um deinen KI-basierten Lernplan zu generieren.")
    else:
        st.warning("""
        **⚠️ Einrichtung unvollständig**
        
        Bitte vervollständige Folgendes, bevor du den Plan generierst:
        """)
        
        if num_leistungsnachweise == 0:
            st.write("• Füge mindestens einen Leistungsnachweis hinzu")
        if not has_api_key:
            st.write("• Gib deinen OpenAI API-Schlüssel ein")
        if st.session_state.study_end is None:
            st.write("• Füge mindestens einen Leistungsnachweis mit Fälligkeitsdatum hinzu")


def show_plan_page():
    """
    Plan page - Display and generate the AI-powered study plan.
    """
    st.header("📅 Lernplan")
    st.markdown("Generiere deinen personalisierten KI-gestützten Lernplan basierend auf deiner Einrichtung.")
    
    # Check if setup is complete
    setup_complete = (
        len(st.session_state.leistungsnachweise) > 0 and
        st.session_state.openai_key and
        st.session_state.study_end is not None
    )
    
    if not setup_complete:
        st.warning("""
        ⚠️ **Einrichtung unvollständig**
        
        Bitte vervollständige zuerst die Einrichtungs-Seite:
        - Füge mindestens einen Leistungsnachweis hinzu
        - Gib deinen OpenAI API-Schlüssel ein
        - Setze gültige Semester-Daten
        """)
        return
    
    st.markdown("---")
    
    # ========== STEP 1: CALCULATE FREE TIME SLOTS ==========
    st.subheader("Schritt 1: Verfügbare Lernzeit berechnen")
    st.markdown("Zuerst identifizieren wir alle deine verfügbaren freien Zeitfenster basierend auf deinen Einschränkungen.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("🔍 Freie Zeitfenster berechnen", type="primary", use_container_width=True):
            with st.spinner("Berechne freie Zeitfenster..."):
                free_slots = calculate_free_slots()
                st.session_state.free_slots = free_slots
                st.success(f"✅ {len(free_slots)} freie Zeitfenster gefunden!")
    
    with col2:
        if "free_slots" in st.session_state and st.session_state.free_slots:
            total_hours = sum([slot["hours"] for slot in st.session_state.free_slots])
            st.metric("Gesamte freie Stunden", f"{total_hours:.1f}h")
    
    # Display free slots if calculated
    if "free_slots" in st.session_state and st.session_state.free_slots:
        free_slots = st.session_state.free_slots
        
        st.markdown("---")
        st.markdown("**📊 Zusammenfassung freie Zeitfenster:**")
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Zeitfenster gesamt", len(free_slots))
        with col2:
            total_hours = sum([slot["hours"] for slot in free_slots])
            st.metric("Stunden gesamt", f"{total_hours:.1f}h")
        with col3:
            avg_hours = total_hours / len(free_slots) if free_slots else 0
            st.metric("Ø Stunden/Fenster", f"{avg_hours:.1f}h")
        with col4:
            unique_days = len(set([slot["date"] for slot in free_slots]))
            st.metric("Lerntage", unique_days)
        
        # Preview first 10 slots
        st.markdown("**📋 Vorschau (Erste 10 Zeitfenster):**")
        
        preview_data = []
        for slot in free_slots[:10]:
            preview_data.append({
                "Datum": slot["date"].strftime("%a, %d %b %Y"),
                "Start": slot["start"],
                "Ende": slot["end"],
                "Dauer (Stunden)": slot["hours"]
            })
        
        st.dataframe(preview_data, use_container_width=True)
        
        if len(free_slots) > 10:
            with st.expander(f"📄 Alle {len(free_slots)} Zeitfenster anzeigen"):
                all_slots_data = []
                for slot in free_slots:
                    all_slots_data.append({
                        "Datum": slot["date"].strftime("%a, %d %b %Y"),
                        "Start": slot["start"],
                        "Ende": slot["end"],
                        "Dauer (Stunden)": slot["hours"]
                    })
                st.dataframe(all_slots_data, use_container_width=True)
        
        st.markdown("---")
        
        # Next step hint
        st.info("""
        **💡 Nächster Schritt:**
        
        Wenn du mit den freien Zeitfenstern zufrieden bist, klicke unten, um deinen KI-generierten Lernplan zu erstellen!
        """)
    
    st.markdown("---")
    
    # ========== STEP 2: GENERATE AI STUDY PLAN ==========
    st.subheader("Schritt 2: KI-Lernplan generieren")
    st.markdown("Nutze KI, um einen optimierten Lernplan zu erstellen, der zu deinen freien Zeitfenstern und Lernpräferenzen passt.")
    
    # Check if free slots exist
    if not st.session_state.get("free_slots"):
        st.warning("⚠️ Bitte berechne zuerst die freien Zeitfenster (Schritt 1), bevor du den KI-Plan generierst.")
    else:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            plan_exists = "plan" in st.session_state and st.session_state.plan
            button_label = "🔄 KI-Plan neu generieren" if plan_exists else "🤖 KI-Plan generieren"
            
            if st.button(button_label, type="primary", use_container_width=True):
                with st.spinner("🧠 KI erstellt deinen personalisierten Lernplan... Dies kann 30-60 Sekunden dauern."):
                    success = generate_plan_via_ai()
                    
                    if success:
                        st.success(f"✅ Lernplan erfolgreich generiert! {len(st.session_state.plan)} Lerneinheiten gefunden.")
                        st.balloons()
                    else:
                        st.error("Plan-Generierung fehlgeschlagen. Prüfe die Fehlermeldung oben.")
        
        with col2:
            if "plan" in st.session_state and st.session_state.plan:
                st.metric("Lerneinheiten", len(st.session_state.plan))
        
        # Display generated plan
        if "plan" in st.session_state and st.session_state.plan:
            plan = st.session_state.plan
            
            st.markdown("---")
            st.markdown("**📅 Dein KI-generierter Lernplan:**")
            
            # Summary statistics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Einheiten gesamt", len(plan))
            
            with col2:
                unique_assessments = len(set([session.get("module", "Unknown") for session in plan]))
                st.metric("Leistungsnachweise abgedeckt", unique_assessments)
            
            with col3:
                # Calculate total study hours
                total_study_hours = 0
                for session in plan:
                    try:
                        start = datetime.strptime(session.get("start", "00:00"), "%H:%M")
                        end = datetime.strptime(session.get("end", "00:00"), "%H:%M")
                        hours = (end - start).total_seconds() / 3600
                        total_study_hours += hours
                    except:
                        pass
                st.metric("Lernstunden gesamt", f"{total_study_hours:.1f}h")
            
            with col4:
                unique_dates = len(set([session.get("date", "") for session in plan]))
                st.metric("Lerntage", unique_dates)
            
            st.markdown("---")
            
            # Display plan with different views
            display_plan_views(plan)
            
            st.markdown("---")
            st.success("""
            **✅ Plan generiert!**
            
            Dein KI-generierter Lernplan ist bereit! Du kannst jetzt:
            - Den Zeitplan oben überprüfen
            - Zur **Anpassungen**-Seite gehen, um einzelne Einheiten anzupassen
            - Zur **Export**-Seite gehen, um deinen Plan als PDF oder Kalender-Format herunterzuladen
            """)


def display_sessions_table(sessions):
    """
    Display a list of study sessions as a formatted table.
    
    Args:
        sessions (list): List of session dicts
    """
    table_data = []
    for session in sessions:
        # Parse date
        try:
            session_date = datetime.fromisoformat(session.get("date", "")).date()
            date_str = session_date.strftime("%a, %d %b %Y")
        except:
            date_str = session.get("date", "Unknown")
        
        table_data.append({
            "Datum": date_str,
            "Zeit": f"{session.get('start', 'N/A')} - {session.get('end', 'N/A')}",
            "Thema": session.get("topic", "N/A"),
            "Beschreibung": session.get("description", "N/A")
        })
    
    st.dataframe(table_data, use_container_width=True, hide_index=True)


def display_plan_views(plan):
    """
    Display the study plan in multiple view formats.
    
    Args:
        plan (list): List of study session dicts
    """
    
    if not plan:
        st.info("📭 Noch kein Lernplan vorhanden. Generiere einen Plan mit dem Button oben.")
        return
    
    # Sort plan chronologically
    sorted_plan = sorted(plan, key=lambda x: (x.get("date", ""), x.get("start", "")))
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["📅 Wochenansicht", "📋 Listenansicht"])
    
    # ========== WEEKLY VIEW ==========
    with tab1:
        st.markdown("**Wochen-Kalenderansicht deines Lernplans**")
        st.caption("Lerneinheiten organisiert nach Woche und Tag")
        
        display_weekly_view(sorted_plan)
    
    # ========== LIST VIEW ==========
    with tab2:
        st.markdown("**Chronologische Liste aller Lerneinheiten**")
        st.caption("Vollständiger Zeitplan sortiert nach Datum und Zeit")
        
        display_list_view(sorted_plan)


def display_weekly_view(sorted_plan):
    """
    Display study plan grouped by weeks with daily columns.
    
    Args:
        sorted_plan (list): Sorted list of study session dicts
    """
    
    # Group sessions by ISO week
    weeks = {}
    for session in sorted_plan:
        try:
            session_date = datetime.fromisoformat(session.get("date", "")).date()
            # Get ISO week (year, week_number)
            iso_year, iso_week, _ = session_date.isocalendar()
            week_key = f"{iso_year}-W{iso_week:02d}"
            
            if week_key not in weeks:
                # Calculate week start (Monday) and end (Sunday)
                week_start = session_date - timedelta(days=session_date.weekday())
                week_end = week_start + timedelta(days=6)
                weeks[week_key] = {
                    "start": week_start,
                    "end": week_end,
                    "sessions": []
                }
            
            weeks[week_key]["sessions"].append(session)
        except:
            continue
    
    if not weeks:
        st.info("Keine gültigen Einheiten zum Anzeigen.")
        return
    
    # Sort weeks chronologically
    sorted_weeks = sorted(weeks.items(), key=lambda x: x[1]["start"])
    
    # Display each week
    for week_num, (week_key, week_data) in enumerate(sorted_weeks, 1):
        week_start = week_data["start"]
        week_end = week_data["end"]
        
        st.markdown(f"### Woche {week_num} ({week_start.strftime('%d %b')} – {week_end.strftime('%d %b %Y')})")
        
        # Group sessions by weekday
        days_sessions = {i: [] for i in range(7)}  # 0=Monday, 6=Sunday
        
        for session in week_data["sessions"]:
            try:
                session_date = datetime.fromisoformat(session.get("date", "")).date()
                weekday = session_date.weekday()
                days_sessions[weekday].append(session)
            except:
                continue
        
        # Create 7 columns for days of the week
        cols = st.columns(7)
        day_names = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        
        for day_idx, col in enumerate(cols):
            with col:
                # Calculate the actual date for this day
                day_date = week_start + timedelta(days=day_idx)
                st.markdown(f"**{day_names[day_idx]}**")
                st.caption(day_date.strftime("%d %b"))
                
                sessions_today = days_sessions[day_idx]
                
                if sessions_today:
                    for session in sessions_today:
                        # Create a compact card for each session
                        start = session.get("start", "N/A")
                        end = session.get("end", "N/A")
                        module = session.get("module", "Unknown")
                        topic = session.get("topic", "N/A")
                        
                        # Use a container with custom styling
                        st.markdown(f"""
                        <div style="background-color: #f0f2f6; padding: 8px; border-radius: 4px; margin-bottom: 8px;">
                            <div style="font-size: 0.8em; font-weight: bold;">{start}-{end}</div>
                            <div style="font-size: 0.85em; margin-top: 4px;"><b>{module}</b></div>
                            <div style="font-size: 0.75em; color: #666; margin-top: 2px;">{topic}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("<div style='color: #999; font-size: 0.85em;'>Keine Einheiten</div>", unsafe_allow_html=True)
        
        st.markdown("---")


def display_list_view(sorted_plan):
    """
    Display study plan as a chronological list grouped by date.
    
    Args:
        sorted_plan (list): Sorted list of study session dicts
    """
    
    # Group sessions by date
    sessions_by_date = {}
    for session in sorted_plan:
        date_key = session.get("date", "Unknown")
        if date_key not in sessions_by_date:
            sessions_by_date[date_key] = []
        sessions_by_date[date_key].append(session)
    
    # Display each date group
    for date_str in sorted(sessions_by_date.keys()):
        try:
            session_date = datetime.fromisoformat(date_str).date()
            date_display = session_date.strftime("%A, %d %B %Y")
        except:
            date_display = date_str
        
        st.markdown(f"### 📅 {date_display}")
        
        sessions = sessions_by_date[date_str]
        
        for session in sessions:
            start = session.get("start", "N/A")
            end = session.get("end", "N/A")
            module = session.get("module", "Unknown")
            topic = session.get("topic", "N/A")
            description = session.get("description", "")
            
            # Create formatted session entry
            col1, col2 = st.columns([1, 4])
            
            with col1:
                st.markdown(f"**{start} – {end}**")
            
            with col2:
                st.markdown(f"**{module}: {topic}**")
                if description:
                    st.caption(description)
        
        st.markdown("---")


def show_adjustments_page():
    """
    Adjustments page - Modify settings and regenerate the study plan.
    """
    st.header("🔧 Anpassungen")
    st.markdown("Verfeinere deine Einstellungen und generiere deinen Lernplan mit aktualisierten Präferenzen neu.")
    
    # Check if critical data exists
    has_leistungsnachweise = len(st.session_state.leistungsnachweise) > 0
    has_api_key = bool(st.session_state.openai_key)
    has_valid_dates = st.session_state.study_end is not None
    
    if not (has_leistungsnachweise and has_api_key and has_valid_dates):
        st.warning("""
        ⚠️ **Einrichtung unvollständig**
        
        Bitte schliesse zuerst die Einrichtung ab:
        - Füge mindestens einen Leistungsnachweis hinzu
        - Gib deinen OpenAI API-Schlüssel ein
        - Setze gültige Semesterdaten
        """)
        return
    
    st.markdown("---")
    
    # ========== SECTION 1: LEISTUNGSNACHWEISE PRIORITIES ==========
    st.subheader("1️⃣ Prioritäten & Lernaufwand")
    st.markdown("Passe Prioritätslevel und Lernaufwand für jeden Leistungsnachweis an. Höhere Werte = mehr Lernzeit zugeteilt.")
    
    if st.session_state.leistungsnachweise:
        # Display leistungsnachweise with priority sliders
        for idx, ln in enumerate(st.session_state.leistungsnachweise):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                st.markdown(f"**{ln['title']}** ({ln['type']})")
                if ln.get('deadline'):
                    st.caption(f"Fällig: {ln['deadline'].strftime('%d %b %Y')}")
                if ln.get('module'):
                    st.caption(f"Modul: {ln['module']}")
            
            with col2:
                new_priority = st.slider(
                    "Priorität",
                    min_value=1,
                    max_value=5,
                    value=ln.get('priority', 3),
                    key=f"priority_adjust_{idx}",
                    label_visibility="collapsed",
                    help="1 = niedrige Priorität, 5 = hohe Priorität"
                )
                # Update priority in session state
                st.session_state.leistungsnachweise[idx]['priority'] = new_priority
            
            with col3:
                new_effort = st.slider(
                    "Lernaufwand",
                    min_value=1,
                    max_value=5,
                    value=ln.get('effort', 3),
                    key=f"effort_adjust_{idx}",
                    label_visibility="collapsed",
                    help="1 = wenig Aufwand, 5 = sehr viel Aufwand"
                )
                # Update effort in session state
                st.session_state.leistungsnachweise[idx]['effort'] = new_effort
            
            with col4:
                st.metric("", f"P:{new_priority} A:{new_effort}")
        
        st.success("✅ Prioritätsänderungen automatisch gespeichert")
    else:
        st.info("Keine Leistungsnachweise zum Anpassen verfügbar.")
    
    st.markdown("---")
    
    # ========== SECTION 2: BUSY TIMES QUICK EDIT ==========
    st.subheader("2️⃣ Wann hast du schon etwas vor?")
    st.markdown("Verwalte deine wiederkehrenden wöchentlichen Verpflichtungen.")
    
    # Display existing busy times
    if st.session_state.busy_times:
        st.markdown("**Deine aktuellen belegten Zeiten:**")
        
        for idx, busy in enumerate(st.session_state.busy_times):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                days_str = ", ".join(busy['days'])
                st.write(f"• **{busy['label']}**: {days_str} von {busy['start']} bis {busy['end']}")
            
            with col2:
                if st.button("🗑️ Entfernen", key=f"remove_busy_adjust_{idx}", use_container_width=True):
                    st.session_state.busy_times.pop(idx)
                    st.success("Belegte Zeit entfernt!")
                    st.rerun()
    else:
        st.info("Keine belegten Zeiten konfiguriert.")
    
    # Add new busy time (simplified)
    with st.expander("➕ Neue belegte Zeit hinzufügen"):
        with st.form("add_busy_time_adjust", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                new_busy_label = st.text_input("Bezeichnung", placeholder="z.B. Meeting, Vorlesung")
                new_busy_days = st.multiselect(
                    "Tage",
                    ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
                )
            
            with col2:
                new_busy_start = st.time_input("Startzeit", value=None)
                new_busy_end = st.time_input("Endzeit", value=None)
            
            if st.form_submit_button("Hinzufügen", use_container_width=True):
                if new_busy_label and new_busy_days and new_busy_start and new_busy_end:
                    st.session_state.busy_times.append({
                        "label": new_busy_label,
                        "days": new_busy_days,
                        "start": new_busy_start.strftime("%H:%M"),
                        "end": new_busy_end.strftime("%H:%M")
                    })
                    st.success("Belegte Zeit hinzugefügt!")
                    st.rerun()
                else:
                    st.error("Bitte fülle alle Felder aus.")
    
    st.markdown("---")
    
    # ========== SECTION 3: LEARNING PREFERENCES QUICK EDIT ==========
    st.subheader("3️⃣ Lernpräferenzen")
    st.markdown("Passe deine Lernstrategien und Lern-Limits an.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Lernstrategien:**")
        
        spacing = st.checkbox(
            "Spaced Repetition",
            value=st.session_state.preferences.get("spacing", True),
            key="adjust_spacing"
        )
        
        interleaving = st.checkbox(
            "Interleaving von Fächern",
            value=st.session_state.preferences.get("interleaving", False),
            key="adjust_interleaving"
        )
        
        deep_work = st.checkbox(
            "Deep-Work-Einheiten für komplexe Themen",
            value=st.session_state.preferences.get("deep_work", True),
            key="adjust_deep_work"
        )
        
        short_sessions = st.checkbox(
            "Kurze Einheiten für theorielastige Fächer",
            value=st.session_state.preferences.get("short_sessions", False),
            key="adjust_short_sessions"
        )
    
    with col2:
        st.markdown("**Lern-Limits:**")
        
        max_hours_day = st.number_input(
            "Max. Stunden pro Tag",
            min_value=1,
            max_value=24,
            value=st.session_state.preferences.get("max_hours_day", 8),
            key="adjust_max_hours_day"
        )
        
        max_hours_week = st.number_input(
            "Max. Stunden pro Woche",
            min_value=0,
            max_value=168,
            value=st.session_state.preferences.get("max_hours_week", 40),
            key="adjust_max_hours_week"
        )
        
        min_session_duration = st.number_input(
            "Min. Einheiten-Dauer (Minuten)",
            min_value=15,
            max_value=240,
            value=st.session_state.preferences.get("min_session_duration", 60),
            step=15,
            key="adjust_min_session"
        )
    
    # Update preferences
    st.session_state.preferences.update({
        "spacing": spacing,
        "interleaving": interleaving,
        "deep_work": deep_work,
        "short_sessions": short_sessions,
        "max_hours_day": max_hours_day,
        "max_hours_week": max_hours_week if max_hours_week > 0 else None,
        "min_session_duration": min_session_duration
    })
    
    st.success("✅ Präferenzen aktualisiert")
    
    st.markdown("---")
    
    # ========== SECTION 4: RE-PLANNING ==========
    st.subheader("4️⃣ Lernplan neu generieren")
    st.markdown("Wende deine Änderungen an und erstelle einen neuen Lernplan basierend auf den aktualisierten Einstellungen.")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info("""
        **Was passiert bei der Neu-Generierung:**
        1. Freie Zeitfenster werden basierend auf aktuellen belegten Zeiten und Abwesenheiten neu berechnet
        2. KI erstellt einen neuen Lernplan mit aktualisierten Modul-Prioritäten und Präferenzen
        3. Dein vorheriger Plan wird durch den neuen ersetzt
        """)
    
    with col2:
        if st.button("🔄 Aktualisieren & Neu generieren", type="primary", use_container_width=True):
            with st.spinner("Neu berechnen und generieren..."):
                # Step 1: Recalculate free slots
                try:
                    free_slots = calculate_free_slots()
                    st.session_state.free_slots = free_slots
                    
                    # Step 2: Generate new AI plan
                    success = generate_plan_via_ai()
                    
                    if success:
                        st.success(f"""
                        ✅ **Plan erfolgreich neu generiert!**
                        
                        - Freie Zeitfenster neu berechnet: {len(free_slots)} Fenster
                        - Neuer Lernplan erstellt: {len(st.session_state.plan)} Einheiten
                        
                        👉 Gehe zur **Lernplan**-Seite, um deinen aktualisierten Zeitplan zu sehen!
                        """)
                        st.balloons()
                    else:
                        st.error("Neue Plan-Generierung fehlgeschlagen. Prüfe Fehlermeldungen oben.")
                
                except Exception as e:
                    st.error(f"Fehler bei der Neu-Generierung: {str(e)}")
    
    st.markdown("---")
    
    # Quick stats
    with st.expander("📊 Aktuelle Konfigurations-Übersicht"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Leistungsnachweise", len(st.session_state.leistungsnachweise))
            avg_priority = sum([ln.get('priority', 1) for ln in st.session_state.leistungsnachweise]) / len(st.session_state.leistungsnachweise) if st.session_state.leistungsnachweise else 0
            st.metric("Ø Priorität", f"{avg_priority:.1f}/5")
        
        with col2:
            st.metric("Belegte Zeiten", len(st.session_state.busy_times))
            st.metric("Abwesenheiten", len(st.session_state.absences))
        
        with col3:
            st.metric("Max. Stunden/Tag", st.session_state.preferences.get("max_hours_day", 0))
            rest_days = len(st.session_state.preferences.get("rest_days", []))
            st.metric("Ruhetage/Woche", rest_days)


def create_plan_pdf(plan):
    """
    Create a PDF document from the study plan.
    
    Args:
        plan (list): List of study session dicts, sorted chronologically
    
    Returns:
        bytes: PDF file as bytes
    """
    
    # Create PDF object
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Title
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 10, "AI Study Plan", ln=True, align="C")
    pdf.ln(5)
    
    # Study plan dates
    pdf.set_font("Helvetica", "", 12)
    study_start = st.session_state.study_start.strftime("%d %B %Y")
    study_end = st.session_state.study_end.strftime("%d %B %Y") if st.session_state.study_end else "N/A"
    pdf.cell(0, 8, f"Lernplan: {study_start} - {study_end}", ln=True, align="C")
    pdf.ln(10)
    
    # Group sessions by date
    sessions_by_date = {}
    for session in plan:
        date_key = session.get("date", "Unknown")
        if date_key not in sessions_by_date:
            sessions_by_date[date_key] = []
        sessions_by_date[date_key].append(session)
    
    # Iterate through each date
    for date_str in sorted(sessions_by_date.keys()):
        # Parse and format date
        try:
            session_date = datetime.fromisoformat(date_str).date()
            date_display = session_date.strftime("%A, %d %B %Y")
        except:
            date_display = date_str
        
        # Date header (bold)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 8, date_display, ln=True)
        pdf.ln(2)
        
        # Sessions for this date
        sessions = sessions_by_date[date_str]
        
        for session in sessions:
            start = session.get("start", "N/A")
            end = session.get("end", "N/A")
            module = session.get("module", "Unknown")
            topic = session.get("topic", "N/A")
            description = session.get("description", "")
            
            # Time (bold)
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(40, 6, f"{start} - {end}", ln=False)
            
            # Module and topic
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 6, f"{module}: {topic}")
            
            # Description (indented, smaller font)
            if description:
                pdf.set_font("Helvetica", "", 10)
                pdf.set_x(50)  # Indent
                pdf.multi_cell(0, 5, description)
            
            pdf.ln(2)
        
        pdf.ln(5)
    
    # Footer with generation info
    pdf.set_y(-30)
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 5, f"Generated on {datetime.now().strftime('%d %B %Y at %H:%M')}", ln=True, align="C")
    pdf.cell(0, 5, "Created with AI Study Planner", ln=True, align="C")
    
    # Return PDF as bytes
    pdf_bytes = pdf.output(dest="S").encode("latin-1")
    return pdf_bytes


def show_export_page():
    """
    Export page - Download the study plan as PDF or other formats.
    """
    st.header("📄 Export")
    st.markdown("Lade deinen personalisierten Lernplan in verschiedenen Formaten herunter.")
    
    st.markdown("---")
    
    # Check if plan exists
    if "plan" not in st.session_state or not st.session_state.plan:
        st.warning("""
        ⚠️ **Kein Lernplan vorhanden**
        
        Bitte generiere zuerst einen Lernplan:
        1. Vervollständige die **Einrichtung**-Seite
        2. Gehe zur **Lernplan**-Seite
        3. Klicke auf "KI-Plan generieren"
        
        Sobald du einen Plan hast, kannst du ihn hier exportieren.
        """)
        return
    
    plan = st.session_state.plan
    
    # Plan summary
    st.subheader("📊 Plan-Übersicht")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Einheiten gesamt", len(plan))
    
    with col2:
        unique_modules = len(set([s.get("module", "") for s in plan]))
        st.metric("Module", unique_modules)
    
    with col3:
        # Calculate total hours
        total_hours = 0
        for session in plan:
            try:
                start = datetime.strptime(session.get("start", "00:00"), "%H:%M")
                end = datetime.strptime(session.get("end", "00:00"), "%H:%M")
                hours = (end - start).total_seconds() / 3600
                total_hours += hours
            except:
                pass
        st.metric("Stunden gesamt", f"{total_hours:.1f}h")
    
    with col4:
        unique_dates = len(set([s.get("date", "") for s in plan]))
        st.metric("Lerntage", unique_dates)
    
    st.markdown("---")
    
    # Preview
    st.subheader("📋 Vorschau")
    st.markdown("Erste 5 Einheiten aus deinem Lernplan:")
    
    # Sort plan chronologically
    sorted_plan = sorted(plan, key=lambda x: (x.get("date", ""), x.get("start", "")))
    
    preview_data = []
    for session in sorted_plan[:5]:
        try:
            session_date = datetime.fromisoformat(session.get("date", "")).date()
            date_str = session_date.strftime("%a, %d %b %Y")
        except:
            date_str = session.get("date", "Unbekannt")
        
        preview_data.append({
            "Datum": date_str,
            "Zeit": f"{session.get('start', 'N/A')} - {session.get('end', 'N/A')}",
            "Modul": session.get("module", "N/A"),
            "Thema": session.get("topic", "N/A")
        })
    
    st.dataframe(preview_data, use_container_width=True, hide_index=True)
    
    if len(sorted_plan) > 5:
        st.caption(f"... und {len(sorted_plan) - 5} weitere Einheiten")
    
    st.markdown("---")
    
    # Export options
    st.subheader("💾 Export-Optionen")
    
    # PDF Export
    st.markdown("### 📑 PDF-Export")
    st.markdown("Lade deinen vollständigen Lernplan als professionell formatiertes PDF-Dokument herunter.")
    
    try:
        # Generate PDF
        pdf_bytes = create_plan_pdf(sorted_plan)
        
        # Download button
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.download_button(
                label="📥 Lernplan als PDF herunterladen",
                data=pdf_bytes,
                file_name="lernplan.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
        
        with col2:
            pdf_size_kb = len(pdf_bytes) / 1024
            st.metric("Dateigrösse", f"{pdf_size_kb:.1f} KB")
        
        st.success("✅ PDF bereit zum Download!")
        
    except Exception as e:
        st.error(f"❌ Fehler beim PDF-Generieren: {str(e)}")
        st.info("Bitte versuche, deinen Plan neu zu generieren oder kontaktiere den Support, falls das Problem weiterhin besteht.")
    
    st.markdown("---")
    
    # Future export options (placeholders)
    st.markdown("### 🔮 Bald verfügbar")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.button("📅 Export zu iCal", disabled=True, use_container_width=True)
        st.caption("*Kalender-Integration bald verfügbar*")
    
    with col2:
        st.button("📊 Export zu Excel", disabled=True, use_container_width=True)
        st.caption("*Tabellen-Format bald verfügbar*")
    
    with col3:
        st.button("📧 Plan per E-Mail", disabled=True, use_container_width=True)
        st.caption("*E-Mail-Versand bald verfügbar*")
    
    st.markdown("---")
    
    # Tips
    st.info("""
    **💡 Tipps:**
    - Drucke das PDF aus und behalte es an deinem Schreibtisch sichtbar
    - Importiere es in deinen digitalen Kalender für automatische Erinnerungen
    - Teile es mit Lernpartnern oder Beratern
    - Aktualisiere und exportiere neu, wenn du Anpassungen vornimmst
    """)


if __name__ == "__main__":
    main()
