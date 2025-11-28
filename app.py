"""
KI-Lernplaner für Studierende

Eine Streamlit Web-Anwendung, die Studierenden hilft, einen KI-basierten Lernplan
für ihr Semester zu erstellen. 

Autor: Locher, Wirth & Heiniger
Projekt: StudyPlanner
"""

import streamlit as st
from datetime import date, time, datetime, timedelta
import json
from openai import OpenAI
import google.generativeai as genai

# Import prompt configuration FIRST
from prompt_config import get_active_prompts, AVAILABLE_VERSIONS, ACTIVE_PROMPT_VERSION

# Get active prompts from configuration
get_system_prompt, build_user_prompt = get_active_prompts()

# Import planning functions
from planning import calculate_free_slots as calc_free_slots

# Import display functions
from display_plan import display_plan_views

# Import PDF export
from pdf_export import create_plan_pdf

# Import test data
from test_data import load_test_data_into_session_state


def calculate_free_slots():
    """
    Streamlit wrapper for calculate_free_slots from planning module.
    Extracts parameters from session state and handles UI feedback.
    
    Returns:
        list: List of dicts with free time slots in format:
              [{"date": date, "day": str, "start_time": time, "end_time": time}, ...]
    """
    
    # Extract data from session state
    study_start = st.session_state.study_start
    study_end = st.session_state.study_end
    
    if not study_end:
        st.error("❌ Kein Enddatum verfügbar. Bitte füge mindestens einen Leistungsnachweis mit Fälligkeitsdatum hinzu.")
        return []
    
    # Ensure study_start and study_end are date objects, not time or datetime objects
    if isinstance(study_start, datetime):
        study_start = study_start.date()
    elif not isinstance(study_start, date):
        st.error(f"❌ Ungültiges Startdatum-Format. Bitte gehe zur Einrichtung.")
        return []
    
    if isinstance(study_end, datetime):
        study_end = study_end.date()
    elif not isinstance(study_end, date):
        st.error(f"❌ Ungültiges Enddatum-Format. Bitte gehe zur Einrichtung.")
        return []
    
    # Prepare parameters for planning module
    busy_times = st.session_state.busy_times
    absences = st.session_state.absences
    rest_days = st.session_state.preferences.get("rest_days", [])
    max_hours_day = st.session_state.preferences.get("max_hours_day", 8)
    
    # Determine smart time windows based on preferred times
    # This creates reasonable boundaries that prevent ridiculous times like Sunday 06:00
    preferred_times = st.session_state.preferences.get("preferred_times_of_day", [])
    
    if preferred_times:
        # Use preferred times to set boundaries
        if "morning" in preferred_times and "afternoon" not in preferred_times and "evening" not in preferred_times:
            # Only morning: 07:00-12:00
            earliest_study_time = datetime.strptime("07:00", "%H:%M").time()
            latest_study_time = datetime.strptime("12:00", "%H:%M").time()
        elif "afternoon" in preferred_times and "morning" not in preferred_times and "evening" not in preferred_times:
            # Only afternoon: 12:00-18:00
            earliest_study_time = datetime.strptime("12:00", "%H:%M").time()
            latest_study_time = datetime.strptime("18:00", "%H:%M").time()
        elif "evening" in preferred_times and "morning" not in preferred_times and "afternoon" not in preferred_times:
            # Only evening: 17:00-22:00
            earliest_study_time = datetime.strptime("17:00", "%H:%M").time()
            latest_study_time = datetime.strptime("22:00", "%H:%M").time()
        elif "morning" in preferred_times and "afternoon" in preferred_times:
            # Morning + afternoon: 07:00-18:00
            earliest_study_time = datetime.strptime("07:00", "%H:%M").time()
            latest_study_time = datetime.strptime("18:00", "%H:%M").time()
        elif "afternoon" in preferred_times and "evening" in preferred_times:
            # Afternoon + evening: 12:00-22:00
            earliest_study_time = datetime.strptime("12:00", "%H:%M").time()
            latest_study_time = datetime.strptime("22:00", "%H:%M").time()
        else:
            # All times or morning+evening: 07:00-22:00 (most flexible but still reasonable)
            earliest_study_time = datetime.strptime("07:00", "%H:%M").time()
            latest_study_time = datetime.strptime("22:00", "%H:%M").time()
    else:
        # No preference specified: use reasonable student hours
        # 08:00-20:00 is a sensible default (not too early, not too late)
        earliest_study_time = datetime.strptime("08:00", "%H:%M").time()
        latest_study_time = datetime.strptime("20:00", "%H:%M").time()
    
    # Convert busy_times format to match planning module expectations
    # Old format: {"days": [weekdays], "start": "HH:MM", "end": "HH:MM"}
    # New format: {"day": weekday, "start": time, "end": time}
    
    # Mapping German weekday names to English (lowercase)
    WEEKDAY_DE_TO_EN = {
        "Montag": "monday",
        "Dienstag": "tuesday",
        "Mittwoch": "wednesday",
        "Donnerstag": "thursday",
        "Freitag": "friday",
        "Samstag": "saturday",
        "Sonntag": "sunday"
    }
    
    converted_busy_times = []
    for busy in busy_times:
        for day in busy["days"]:
            # Convert German day name to English lowercase
            english_day = WEEKDAY_DE_TO_EN.get(day, day.lower())
            converted_busy_times.append({
                "day": english_day,
                "start": datetime.strptime(busy["start"], "%H:%M").time(),
                "end": datetime.strptime(busy["end"], "%H:%M").time()
            })
    
    # Convert absences format
    # Old format: {"start_date": date, "end_date": date}
    # New format: {"start": date, "end": date}
    converted_absences = []
    for absence in absences:
        converted_absences.append({
            "start": absence["start_date"],
            "end": absence["end_date"]
        })
    
    # Convert rest_days from German to English lowercase
    WEEKDAY_DE_TO_EN_REST = {
        "Montag": "monday",
        "Dienstag": "tuesday",
        "Mittwoch": "wednesday",
        "Donnerstag": "thursday",
        "Freitag": "friday",
        "Samstag": "saturday",
        "Sonntag": "sunday"
    }
    converted_rest_days = [WEEKDAY_DE_TO_EN_REST.get(day, day.lower()) for day in rest_days]
    
    # Call planning module
    free_slots, error = calc_free_slots(
        study_start=study_start,
        study_end=study_end,
        busy_times=converted_busy_times,
        absences=converted_absences,
        rest_days=converted_rest_days,
        max_hours_day=max_hours_day,
        earliest_study_time=earliest_study_time,
        latest_study_time=latest_study_time
    )
    
    # Handle errors
    if error:
        st.error(f"❌ {error}")
        return []
    
    # Convert output format to match expected format in rest of app
    # planning module returns: {"date": date, "day": str, "start_time": time, "end_time": time}
    # app expects: {"date": date, "start": "HH:MM", "end": "HH:MM", "hours": float}
    converted_output = []
    for slot in free_slots:
        hours = (datetime.combine(date.min, slot["end_time"]) - 
                datetime.combine(date.min, slot["start_time"])).total_seconds() / 3600
        
        # Only include intervals with meaningful duration (at least 15 minutes)
        if hours >= 0.25:
            converted_output.append({
                "date": slot["date"],
                "start": slot["start_time"].strftime("%H:%M"),
                "end": slot["end_time"].strftime("%H:%M"),
                "hours": round(hours, 2)
            })
    
    return converted_output


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
        st.error("❌ API-Schlüssel fehlt. Bitte konfiguriere ihn auf der Einrichtungs-Seite (OpenAI oder Gemini).")
        return False
    
    if not st.session_state.leistungsnachweise:
        st.error("❌ Keine Leistungsnachweise definiert. Bitte füge Leistungsnachweise auf der Einrichtungs-Seite hinzu.")
        return False
    
    if not st.session_state.get("free_slots"):
        st.error("❌ Keine freien Zeitfenster berechnet. Bitte berechne zuerst die freien Zeitfenster.")
        return False
    
    try:
        # Prepare data for prompt building
        prompt_data = {
            'semester_start': st.session_state.study_start,
            'semester_end': st.session_state.study_end,
            'leistungsnachweise': st.session_state.leistungsnachweise,
            'preferences': st.session_state.preferences,
            'free_slots': st.session_state.free_slots
        }
        
        # Get prompts - check if manual mode is active
        if st.session_state.get('manual_prompts_active', False):
            # Use manual prompts
            system_message = st.session_state.manual_system_prompt
            
            # Build user message from template by replacing placeholders
            user_message = st.session_state.manual_user_prompt_template
            
            # Simple placeholder replacement (you can make this more sophisticated)
            user_message = user_message.replace("{semester_start}", str(prompt_data['semester_start']))
            user_message = user_message.replace("{semester_end}", str(prompt_data['semester_end']))
            user_message = user_message.replace("{leistungsnachweise}", json.dumps(prompt_data['leistungsnachweise'], indent=2, ensure_ascii=False))
            user_message = user_message.replace("{preferences}", json.dumps(prompt_data['preferences'], indent=2, ensure_ascii=False))
            user_message = user_message.replace("{free_slots}", json.dumps(
                [{
                    'date': str(slot['date']),
                    'day': slot['day'],
                    'start_time': str(slot['start_time']),
                    'end_time': str(slot['end_time'])
                } for slot in prompt_data['free_slots']],
                indent=2,
                ensure_ascii=False
            ))
        else:
            # Use prompts from selected version
            system_message = get_system_prompt()
            user_message = build_user_prompt(prompt_data)
        
        # Get model configuration
        model_provider = st.session_state.get("model_provider", "OpenAI")
        model_name = st.session_state.get("model_name", "gpt-4o-mini")
        
        # Call appropriate API based on provider
        if model_provider == "OpenAI":
            # Initialize OpenAI client
            client = OpenAI(api_key=st.session_state.openai_key)
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=16000
            )
            
            # Extract response content
            response_content = response.choices[0].message.content.strip()
        
        else:  # Google Gemini
            # Configure Gemini API
            genai.configure(api_key=st.session_state.openai_key)
            model = genai.GenerativeModel(model_name)
            
            # Combine system and user prompts for Gemini
            combined_prompt = f"{system_message}\n\n{user_message}"
            
            # Call Gemini API
            response = model.generate_content(
                combined_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=16000,
                )
            )
            
            # Extract response content
            response_content = response.text.strip()
        
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
    
    """)
    
    st.markdown("---")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    st.sidebar.markdown("Wähle einen Bereich aus:")
    
    page = st.sidebar.radio(
        "Gehe zu:",
        ["Einrichtung", "Lernplan", "Export"],
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")
    
    # MODEL SELECTION
    st.sidebar.subheader("🤖 Modell Konfiguration")
    
    model_provider = st.sidebar.selectbox(
        "LLM Provider",
        options=["OpenAI", "Google Gemini"],
        index=0,
        key="model_provider_selector"
    )
    
    api_key = st.sidebar.text_input(
        f"{model_provider} API Key",
        type="password",
        help=f"Gib deinen {model_provider} API Key ein",
        key="api_key_input"
    )
    
    # Update openai_key in session state for compatibility
    if api_key:
        st.session_state.openai_key = api_key
    
    if model_provider == "OpenAI":
        model_name = st.sidebar.selectbox(
            "Modell",
            options=["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
            index=0,
            key="openai_model_selector"
        )
    else:  # Gemini
        model_name = st.sidebar.selectbox(
            "Modell",
            options=["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"],
            index=0,
            key="gemini_model_selector"
        )
    
    # Store in session state
    st.session_state.model_provider = model_provider
    st.session_state.model_name = model_name
    
    st.sidebar.markdown("---")
    
    # PROMPT-VERSION AUSWAHL
    st.sidebar.subheader("⚙️ Prompt Konfiguration")
    
    # Toggle zwischen Vorlagen und Manuell
    prompt_mode = st.sidebar.radio(
        "Modus",
        options=["Vorlagen", "Manuell"],
        horizontal=True,
        help="Vorlagen: Vordefinierte Prompt-Versionen | Manuell: Eigene Prompts schreiben"
    )
    
    if prompt_mode == "Vorlagen":
        selected_version = st.sidebar.selectbox(
            "Prompt-Version",
            options=list(AVAILABLE_VERSIONS.keys()),
            format_func=lambda x: AVAILABLE_VERSIONS[x],
            index=list(AVAILABLE_VERSIONS.keys()).index(ACTIVE_PROMPT_VERSION),
            key="prompt_version_selector",
            help="Wähle die Prompt-Engineering-Strategie für die KI"
        )
        
        # Version in Session State speichern
        if 'selected_prompt_version' not in st.session_state:
            st.session_state.selected_prompt_version = ACTIVE_PROMPT_VERSION
        
        if selected_version != st.session_state.selected_prompt_version:
            st.session_state.selected_prompt_version = selected_version
            # Prompts neu laden
            from prompt_config import set_active_version
            set_active_version(selected_version)
            st.sidebar.success(f"✅ Gewechselt zu: {AVAILABLE_VERSIONS[selected_version]}")
        
        # Manual prompts zurücksetzen
        if 'manual_prompts_active' in st.session_state:
            del st.session_state.manual_prompts_active
    
    else:  # Manueller Modus
        st.sidebar.info("🖊️ **Experimentier-Modus**: Schreibe eigene Prompts ohne Code!")
        
        # Expander für manuelle Prompt-Bearbeitung
        with st.sidebar.expander("✏️ Prompts bearbeiten", expanded=True):
            # Initialisiere mit Vorlage falls noch nicht gesetzt
            if 'manual_system_prompt' not in st.session_state:
                st.session_state.manual_system_prompt = get_system_prompt()
            
            # System Prompt Editor
            st.markdown("**System Prompt:**")
            manual_system = st.text_area(
                "System Prompt",
                value=st.session_state.manual_system_prompt,
                height=200,
                key="system_prompt_editor",
                label_visibility="collapsed",
                help="Definiert die Rolle und Regeln für die KI"
            )
            
            # User Prompt Template Editor
            st.markdown("**User Prompt Template:**")
            st.caption("Platzhalter: {semester_start}, {semester_end}, {leistungsnachweise}, {preferences}, {free_slots}")
            
            if 'manual_user_prompt_template' not in st.session_state:
                # Baue Standard-Template
                sample_data = {
                    'semester_start': date.today(),
                    'semester_end': date.today() + timedelta(days=90),
                    'leistungsnachweise': [],
                    'preferences': {},
                    'free_slots': []
                }
                st.session_state.manual_user_prompt_template = build_user_prompt(sample_data)
            
            manual_user_template = st.text_area(
                "User Prompt Template",
                value=st.session_state.manual_user_prompt_template,
                height=250,
                key="user_prompt_editor",
                label_visibility="collapsed",
                help="Template für User-Prompt (wird mit Daten gefüllt)"
            )
            
            # Speichern Button
            if st.button("💾 Prompts übernehmen", use_container_width=True, type="primary"):
                st.session_state.manual_system_prompt = manual_system
                st.session_state.manual_user_prompt_template = manual_user_template
                st.session_state.manual_prompts_active = True
                st.success("✅ Manuelle Prompts gespeichert!")
                st.rerun()
            
            # Reset Button
            if st.button("🔄 Auf Vorlage zurücksetzen", use_container_width=True):
                st.session_state.manual_system_prompt = get_system_prompt()
                sample_data = {
                    'semester_start': date.today(),
                    'semester_end': date.today() + timedelta(days=90),
                    'leistungsnachweise': [],
                    'preferences': {},
                    'free_slots': []
                }
                st.session_state.manual_user_prompt_template = build_user_prompt(sample_data)
                if 'manual_prompts_active' in st.session_state:
                    del st.session_state.manual_prompts_active
                st.success("✅ Zurückgesetzt!")
                st.rerun()
        
        # Export/Import Buttons
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            # Export Button
            if st.session_state.get('manual_prompts_active', False):
                prompt_export = {
                    "system_prompt": st.session_state.manual_system_prompt,
                    "user_prompt_template": st.session_state.manual_user_prompt_template,
                    "version": "manual",
                    "timestamp": datetime.now().isoformat()
                }
                
                st.download_button(
                    label="📥 Export",
                    data=json.dumps(prompt_export, indent=2, ensure_ascii=False),
                    file_name=f"prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True,
                    help="Speichere deine Prompts als JSON-Datei"
                )
        
        with col2:
            # Import Button
            uploaded_prompt = st.file_uploader(
                "Import",
                type=["json"],
                key="prompt_import",
                label_visibility="collapsed",
                help="Lade gespeicherte Prompts"
            )
            
            if uploaded_prompt is not None:
                try:
                    imported_data = json.load(uploaded_prompt)
                    st.session_state.manual_system_prompt = imported_data.get("system_prompt", "")
                    st.session_state.manual_user_prompt_template = imported_data.get("user_prompt_template", "")
                    st.session_state.manual_prompts_active = True
                    st.success("✅ Prompts importiert!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Fehler beim Import: {str(e)}")
    
    st.sidebar.markdown("---")
    
    # TEST-MODUS
    st.sidebar.subheader("🧪 Test-Modus")
    
    with st.sidebar.expander("ℹ️ Was ist das?", expanded=False):
        st.markdown("""
        **Test-Daten** bieten ein vordefiniertes Profil eines BWL-Studenten:
        
        - 5 Leistungsnachweise
        - Vorlesungszeiten & Nebenjob
        - Abwesenheiten & Präferenzen
        
        Perfekt zum Testen der App!
        """)
    
    if st.sidebar.button("📋 Test-Daten laden", type="primary", use_container_width=True):
        load_test_data_into_session_state(st)
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.info("💡 Beginne mit **Einrichtung**, um deine Prüfungen und Leistungsnachweise zu erfassen.")
    
    # Route to the selected page
    if page == "Einrichtung":
        show_setup_page()
    elif page == "Lernplan":
        show_plan_page()
    elif page == "Export":
        show_export_page()


def show_setup_page():
    # ========== SECTION 1: STUDY PLAN START DATE ==========
    st.subheader("1️⃣ Start deines Lernplans")
    st.markdown("Ab wann möchtest du aktiv mit dem Lernen beginnen?")
    
    study_start = st.date_input(
        "Lernplan-Start",
        value=st.session_state.study_start,
        format="DD.MM.YYYY",
        help="Ab wann möchtest du mit dem Lernplan beginnen?"
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
    else:
        st.session_state.study_end = None
    
    st.markdown("---")
    
    # ========== SECTION 2: LEISTUNGSNACHWEISE ==========
    st.subheader("2️⃣ Prüfungen & Leistungsnachweise")
    st.markdown("Füge alle Prüfungen, Hausarbeiten, Projekte oder Präsentationen hinzu, die du in diesem Semester abschliessen musst.")
    
    # Form to add new Leistungsnachweis
    # Typ-Auswahl AUSSERHALB des Formulars für dynamische UI
    st.markdown("**Neuen Leistungsnachweis hinzufügen:**")
    
    ln_type_preview = st.selectbox(
        "Typ",
        ["Prüfung", "Hausarbeit", "Präsentation", "Projektarbeit", "Sonstiges"],
        help="Art des Leistungsnachweises",
        key="ln_type_preview"
    )
    
    with st.form("add_leistungsnachweis_form", clear_on_submit=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            ln_title = st.text_input(
                "Titel des Leistungsnachweises",
                placeholder="z.B. Prüfung Data Science, Seminararbeit, Präsentation",
                help="Der Titel deiner Prüfung, Arbeit oder Präsentation"
            )
        
        with col2:
            st.markdown("**Typ:** " + ln_type_preview)
            ln_type = ln_type_preview  # Use the preview value
        
        col3, col4 = st.columns([2, 2])
        
        with col3:
            ln_deadline = st.date_input(
                "Fälligkeitsdatum / Prüfungsdatum",
                value=None,
                format="DD.MM.YYYY",
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
        
        # Prüfungsformat-Felder innerhalb des Formulars
        # (werden nur angezeigt wenn Typ außerhalb als "Prüfung" gewählt wurde)
        ln_exam_format = None
        ln_exam_details = None
        
        if ln_type_preview == "Prüfung":
            st.markdown("**📋 Prüfungsdetails**")
            col_format, col_details = st.columns([1, 2])
            
            with col_format:
                ln_exam_format = st.selectbox(
                    "Prüfungsformat",
                    ["Multiple Choice", "Rechenaufgaben", "Mündliche Prüfung", "Essay/Aufsatz", 
                     "Praktisches Projekt (Open Book)", "Coding-Aufgabe", "Fallstudie", "Gemischt", "Sonstiges"],
                    help="Welches Format hat die Prüfung? Wichtig für die Lernstrategie!"
                )
            
            with col_details:
                ln_exam_details = st.text_input(
                    "Weitere Details (optional)",
                    placeholder="z.B. '90 Min, Closed Book' oder 'Open Book, Laptop erlaubt'",
                    help="Weitere Details wie Dauer, erlaubte Hilfsmittel, Anzahl Fragen etc."
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
                    "effort": ln_effort,
                    "exam_format": ln_exam_format,
                    "exam_details": ln_exam_details if ln_exam_details.strip() else None
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
                    
                    # Prüfungsformat nur bei Typ "Prüfung" anzeigen
                    if ln.get('type') == 'Prüfung' and ln.get('exam_format'):
                        exam_info = f"📋 **Prüfungsformat:** {ln['exam_format']}"
                        if ln.get('exam_details'):
                            exam_info += f" - {ln['exam_details']}"
                        st.write(exam_info)
                    
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
    st.subheader("3️⃣ LLM API-Konfiguration")
    st.markdown("Gib deinen API-Schlüssel ein, um die KI-gestützte Lernplan-Generierung zu aktivieren. Du kannst zwischen **OpenAI** (GPT-4, GPT-3.5) und **Google Gemini** wählen.")
    
    api_key = st.text_input(
        "API-Schlüssel (OpenAI oder Gemini)",
        value=st.session_state.openai_key,
        type="password",
        placeholder="sk-... (OpenAI) oder AIza... (Gemini)",
        help="Dein API-Schlüssel wird sicher in der Sitzung gespeichert und nie angezeigt. Wähle den LLM-Provider in der Sidebar."
    )
    st.session_state.openai_key = api_key
    
    if api_key:
        st.success("✅ API-Schlüssel konfiguriert")
    else:
        st.warning("⚠️ Kein API-Schlüssel eingegeben. KI-Funktionen sind nicht verfügbar.")
    
    st.markdown("---")
    
    # ========== SECTION 4: BUSY TIMES (RECURRING WEEKLY SCHEDULE) ==========
    st.subheader("4️⃣ Belgete Zeiten (wöchentliche Verpflichtungen)")
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
                format="DD.MM.YYYY",
                help="Erster Tag deiner Abwesenheit"
            )
        
        with col2:
            absence_end = st.date_input(
                "Enddatum",
                value=None,
                format="DD.MM.YYYY",
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
    
    st.markdown("**ℹ️ Hinweis zu Lernzeiten:**")
    st.info("Die KI plant Lernzeiten intelligent basierend auf deinen bevorzugten Tageszeiten (siehe unten). Es werden keine unmöglichen Zeiten gewählt (z.B. nachts oder sehr früh morgens).")
    
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
    
    st.markdown("---")
    
    # Time-of-day preferences
    st.markdown("**Wann lernst du am liebsten?**")
    st.markdown("Diese Angabe ist eine Präferenz. Die KI versucht, deinen Lernplan eher in diesen Zeiten zu platzieren, kann aber bei Bedarf davon abweichen.")
    
    col_tod1, col_tod2, col_tod3 = st.columns(3)
    
    current_preferred_times = st.session_state.preferences.get("preferred_times_of_day", [])
    
    with col_tod1:
        prefer_morning = st.checkbox(
            "Morgens (ca. 06:00–11:00)",
            value="morning" in current_preferred_times,
            help="Du bevorzugst es, morgens zu lernen"
        )
    
    with col_tod2:
        prefer_afternoon = st.checkbox(
            "Nachmittags (ca. 12:00–17:00)",
            value="afternoon" in current_preferred_times,
            help="Du bevorzugst es, nachmittags zu lernen"
        )
    
    with col_tod3:
        prefer_evening = st.checkbox(
            "Abends (ca. 18:00–22:00)",
            value="evening" in current_preferred_times,
            help="Du bevorzugst es, abends zu lernen"
        )
    
    # Build list of preferred times
    preferred_times_of_day = []
    if prefer_morning:
        preferred_times_of_day.append("morning")
    if prefer_afternoon:
        preferred_times_of_day.append("afternoon")
    if prefer_evening:
        preferred_times_of_day.append("evening")
    
    st.session_state.preferences["preferred_times_of_day"] = preferred_times_of_day
    
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
        
        st.info("💡 **Empfehlung für den Start:** Wenn du unsicher bist, aktiviere **Wiederholen mit Abständen** + **Längere Fokus-Blöcke für schwierige Themen**. Du kannst die Einstellungen später jederzeit auf der Lernplan-Seite ändern.")
    
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
                deadline_str = f" - Fällig: {ln['deadline'].strftime('%d.%m.%Y')}" if ln.get('deadline') else ""
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
            st.write("• Gib deinen API-Schlüssel ein (OpenAI oder Gemini in der Sidebar wählbar)")
        if st.session_state.study_end is None:
            st.write("• Füge mindestens einen Leistungsnachweis mit Fälligkeitsdatum hinzu")


def show_plan_page():
    """
    Integrated plan page - Generate, view, and adjust the AI-powered study plan.
    Single page with conditional flow based on plan existence.
    """
    st.header("📅 Lernplan")
    st.markdown("Hier kannst du deinen KI-gestützten Lernplan generieren, anzeigen und bei Bedarf feinjustieren.")
    
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
        - Gib deinen API-Schlüssel ein (OpenAI oder Gemini)
        - Setze gültige Semester-Daten
        """)
        return
    
    st.markdown("---")
    
    # Check if plan already exists
    plan_exists = "plan" in st.session_state and st.session_state.plan and len(st.session_state.plan) > 0
    
    # ========== ZUSTAND 1: NOCH KEIN PLAN ==========
    if not plan_exists:
        st.subheader("Schritt 1: Lernplan generieren")
        st.markdown("""
        Basierend auf deinen Prüfungen, Leistungsnachweisen, belegten Zeiten und Lernpräferenzen 
        erstellt die KI einen ersten Vorschlag für deinen Lernplan.
        """)
        
        st.info("""
        **ℹ️ Was passiert bei der Generierung?**
        
        Die KI wird:
        - Deine verfügbaren freien Zeitfenster berechnen
        - Alle Leistungsnachweise und deren Deadlines berücksichtigen
        - Einen optimalen Lernplan erstellen, der zu deinen Präferenzen passt
        
        Dies kann 30-60 Sekunden dauern.
        """)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🤖 Lernplan jetzt generieren", type="primary", use_container_width=True, key="generate_initial_plan"):
                with st.spinner("🧠 KI erstellt deinen personalisierten Lernplan..."):
                    # Calculate free slots first
                    free_slots = calculate_free_slots()
                    st.session_state.free_slots = free_slots
                    
                    if not free_slots:
                        st.error("❌ Keine freien Zeitfenster gefunden. Bitte überprüfe deine Einstellungen.")
                    else:
                        # Generate plan via AI
                        success = generate_plan_via_ai()
                        
                        if success:
                            st.success(f"✅ Lernplan erfolgreich generiert! {len(st.session_state.plan)} Lerneinheiten gefunden.")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ Plan-Generierung fehlgeschlagen. Bitte versuche es erneut.")
    
    # ========== ZUSTAND 2: PLAN VORHANDEN ==========
    else:
        plan = st.session_state.plan
        
        # ========== PLAN ANZEIGEN ==========
        st.subheader("Dein aktueller Lernplan")
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Lerneinheiten", len(plan))
        
        with col2:
            unique_assessments = len(set([session.get("module", "Unknown") for session in plan]))
            st.metric("Leistungsnachweise", unique_assessments)
        
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
        
        # ========== FEINABSTIMMUNG & NEU-GENERIERUNG ==========
        st.divider()
        
        st.subheader("Feinabstimmung & Neu-Generierung")
        st.markdown("""
        Hier kannst du Prioritäten, Lernaufwand, belegte Zeiten und Lern-Limits anpassen. 
        Anschliessend kannst du einen neuen Lernplan auf Basis deiner aktualisierten Einstellungen erstellen.
        """)
        
        # Create tabs for different adjustment categories
        adj_tabs = st.tabs(["Prioritäten & Aufwand", "Belegte Zeiten", "Lernpräferenzen"])
        
        # ========== TAB 1: PRIORITÄTEN & LERNAUFWAND ==========
        with adj_tabs[0]:
            st.markdown("**Passe Prioritätslevel und Lernaufwand für jeden Leistungsnachweis an.**")
            st.caption("Höhere Werte = mehr Lernzeit zugeteilt")
            
            if st.session_state.leistungsnachweise:
                for idx, ln in enumerate(st.session_state.leistungsnachweise):
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                        
                        with col1:
                            st.markdown(f"**{ln['title']}** ({ln['type']})")
                            if ln.get('deadline'):
                                st.caption(f"Fällig: {ln['deadline'].strftime('%d.%m.%Y')}")
                            if ln.get('module'):
                                st.caption(f"Modul: {ln['module']}")
                        
                        with col2:
                            new_priority = st.slider(
                                "Priorität",
                                min_value=1,
                                max_value=5,
                                value=ln.get('priority', 3),
                                key=f"priority_adjust_{idx}",
                                help="1 = niedrige Priorität, 5 = hohe Priorität"
                            )
                            st.session_state.leistungsnachweise[idx]['priority'] = new_priority
                        
                        with col3:
                            new_effort = st.slider(
                                "Lernaufwand",
                                min_value=1,
                                max_value=5,
                                value=ln.get('effort', 3),
                                key=f"effort_adjust_{idx}",
                                help="1 = wenig Aufwand, 5 = sehr viel Aufwand"
                            )
                            st.session_state.leistungsnachweise[idx]['effort'] = new_effort
                        
                        with col4:
                            st.metric("", f"P:{new_priority} A:{new_effort}")
                    
                    if idx < len(st.session_state.leistungsnachweise) - 1:
                        st.markdown("")
                
                st.success("✅ Änderungen werden automatisch gespeichert")
            else:
                st.info("Keine Leistungsnachweise vorhanden.")
        
        # ========== TAB 2: BELEGTE ZEITEN ==========
        with adj_tabs[1]:
            st.markdown("**Verwalte deine wiederkehrenden wöchentlichen Verpflichtungen.**")
            
            # Display existing busy times
            if st.session_state.busy_times:
                st.markdown("**Aktuelle belegte Zeiten:**")
                
                for idx, busy in enumerate(st.session_state.busy_times):
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        days_str = ", ".join(busy['days'])
                        st.write(f"• **{busy['label']}**: {days_str} von {busy['start']} bis {busy['end']}")
                    
                    with col2:
                        if st.button("🗑️", key=f"remove_busy_{idx}", help="Entfernen", use_container_width=True):
                            st.session_state.busy_times.pop(idx)
                            st.success("Belegte Zeit entfernt!")
                            st.rerun()
            else:
                st.info("Keine belegten Zeiten konfiguriert.")
            
            # Add new busy time
            with st.expander("➕ Neue belegte Zeit hinzufügen"):
                with st.form("add_busy_time_adjust", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_busy_label = st.text_input("Bezeichnung", placeholder="z.B. Vorlesung, Meeting")
                        new_busy_days = st.multiselect(
                            "Tage",
                            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                            format_func=lambda x: {"Monday": "Montag", "Tuesday": "Dienstag", "Wednesday": "Mittwoch", 
                                                   "Thursday": "Donnerstag", "Friday": "Freitag", "Saturday": "Samstag", 
                                                   "Sunday": "Sonntag"}[x]
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
        
        # ========== TAB 3: LERNPRÄFERENZEN ==========
        with adj_tabs[2]:
            st.markdown("**Passe deine Lernstrategien und Limits an.**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Lernstrategien:**")
                
                spacing = st.checkbox(
                    "Spaced Repetition",
                    value=st.session_state.preferences.get("spacing", True),
                    key="adjust_spacing",
                    help="Verteile Lerneinheiten über mehrere Tage mit steigenden Intervallen"
                )
                st.session_state.preferences["spacing"] = spacing
                
                interleaving = st.checkbox(
                    "Interleaving von Fächern",
                    value=st.session_state.preferences.get("interleaving", False),
                    key="adjust_interleaving",
                    help="Mische verschiedene Leistungsnachweise innerhalb eines Tages"
                )
                st.session_state.preferences["interleaving"] = interleaving
                
                deep_work = st.checkbox(
                    "Deep Work (lange Fokusblöcke)",
                    value=st.session_state.preferences.get("deep_work", False),
                    key="adjust_deep_work",
                    help="Nutze längere Sessions (2-3h) für komplexe Themen"
                )
                st.session_state.preferences["deep_work"] = deep_work
                
                short_sessions = st.checkbox(
                    "Kurze Sessions für Theorie",
                    value=st.session_state.preferences.get("short_sessions", False),
                    key="adjust_short_sessions",
                    help="Nutze kürzere Sessions (45-60 Min) für theorielastige Inhalte"
                )
                st.session_state.preferences["short_sessions"] = short_sessions
            
            with col2:
                st.markdown("**Lern-Limits:**")
                
                max_hours_day = st.number_input(
                    "Max. Stunden pro Tag",
                    min_value=1,
                    max_value=12,
                    value=st.session_state.preferences.get("max_hours_day", 6),
                    key="adjust_max_hours_day",
                    help="Maximale Lernstunden pro Tag"
                )
                st.session_state.preferences["max_hours_day"] = max_hours_day
                
                max_hours_week = st.number_input(
                    "Max. Stunden pro Woche",
                    min_value=5,
                    max_value=80,
                    value=st.session_state.preferences.get("max_hours_week", 30),
                    key="adjust_max_hours_week",
                    help="Maximale Lernstunden pro Woche (0 = unbegrenzt)"
                )
                st.session_state.preferences["max_hours_week"] = max_hours_week if max_hours_week > 0 else None
                
                min_session_duration = st.number_input(
                    "Min. Session-Dauer (Minuten)",
                    min_value=15,
                    max_value=120,
                    value=st.session_state.preferences.get("min_session_duration", 60),
                    step=15,
                    key="adjust_min_session_duration",
                    help="Minimale Länge einer Lerneinheit"
                )
                st.session_state.preferences["min_session_duration"] = min_session_duration
        
        # ========== NEU-GENERIERUNG BUTTON ==========
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🔄 Lernplan mit aktualisierten Einstellungen neu generieren", type="primary", use_container_width=True, key="regenerate_plan"):
                with st.spinner("🧠 KI erstellt deinen aktualisierten Lernplan..."):
                    # Recalculate free slots with updated settings
                    free_slots = calculate_free_slots()
                    st.session_state.free_slots = free_slots
                    
                    if not free_slots:
                        st.error("❌ Keine freien Zeitfenster gefunden. Bitte überprüfe deine Einstellungen.")
                    else:
                        # Regenerate plan
                        success = generate_plan_via_ai()
                        
                        if success:
                            st.success(f"✅ Lernplan erfolgreich neu generiert! {len(st.session_state.plan)} Lerneinheiten gefunden.")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ Plan-Generierung fehlgeschlagen.")


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
    
    # Sort plan chronologically for export
    sorted_plan = sorted(plan, key=lambda x: (x.get("date", ""), x.get("start", "")))
    
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
    
if __name__ == "__main__":
    main()
