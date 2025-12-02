"""
KI-Lernplaner für Studierende
Eine Streamlit Web-Anwendung, die Studierenden hilft, einen KI-basierten Lernplan
für ihr Semester zu erstellen.
Autor: Locher, Wirth & Heiniger
Projekt: StudyPlanner
"""

import streamlit as st
from datetime import date, datetime, timedelta
import json

# Import constants
from constants import (
    OPENAI_MODELS,
    GEMINI_MODELS,
)

# Import prompt configuration
from prompts.prompt_config import get_active_prompts, AVAILABLE_VERSIONS, ACTIVE_PROMPT_VERSION

# Get active prompts from configuration
get_system_prompt, build_user_prompt = get_active_prompts()

# Import test data
from data.test_data import load_test_data_into_session_state, AVAILABLE_TEST_PROFILES

# Import Services
from services import (
    get_llm_provider,
    LLMError,
    LLMRateLimitError,
    LLMResponseError,
    calculate_free_slots_from_session,
    init_session_state,
)

# Import UI Pages
from ui.pages import show_setup_page, show_plan_page, show_export_page


def calculate_free_slots():
    """
    Streamlit wrapper for calculate_free_slots from planning service.
    Extracts parameters from session state and handles UI feedback.

    Returns:
        list: List of dicts with free time slots in format:
              [{"date": date, "start": "HH:MM", "end": "HH:MM", "hours": float}, ...]
    """
    free_slots, error = calculate_free_slots_from_session(st.session_state)

    if error:
        st.error(f"❌ {error}")
        return []

    return free_slots


def generate_plan_via_ai():
    """
    Generate a detailed study plan using LLM API.

    Uses the user's modules, preferences, and free slots to create an optimized
    study schedule that respects constraints and learning strategies.

    Returns:
        bool: True if successful, False otherwise
    """

    # Validate preconditions
    if not st.session_state.openai_key:
        st.error(
            "❌ API-Schlüssel fehlt. Bitte konfiguriere ihn auf der Einrichtungs-Seite (OpenAI oder Gemini)."
        )
        return False

    if not st.session_state.leistungsnachweise:
        st.error(
            "❌ Keine Leistungsnachweise definiert. Bitte füge Leistungsnachweise auf der Einrichtungs-Seite hinzu."
        )
        return False

    if not st.session_state.get("free_slots"):
        st.error(
            "❌ Keine freien Zeitfenster berechnet. Bitte berechne zuerst die freien Zeitfenster."
        )
        return False

    try:
        # Prepare data for prompt building
        prompt_data = {
            "semester_start": st.session_state.study_start,
            "semester_end": st.session_state.study_end,
            "leistungsnachweise": st.session_state.leistungsnachweise,
            "preferences": st.session_state.preferences,
            "free_slots": st.session_state.free_slots,
            "absences": st.session_state.get("absences", []),
            "busy_times": st.session_state.get("busy_times", []),
        }

        # Get prompts - check if manual mode is active
        if st.session_state.get("manual_prompts_active", False):
            # Use manual prompts
            system_message = st.session_state.manual_system_prompt

            # Build user message from template by replacing placeholders
            user_message = st.session_state.manual_user_prompt_template

            # Simple placeholder replacement
            user_message = user_message.replace(
                "{semester_start}", str(prompt_data["semester_start"])
            )
            user_message = user_message.replace(
                "{semester_end}", str(prompt_data["semester_end"])
            )
            user_message = user_message.replace(
                "{leistungsnachweise}",
                json.dumps(
                    prompt_data["leistungsnachweise"], indent=2, ensure_ascii=False
                ),
            )
            user_message = user_message.replace(
                "{preferences}",
                json.dumps(prompt_data["preferences"], indent=2, ensure_ascii=False),
            )
            user_message = user_message.replace(
                "{free_slots}",
                json.dumps(
                    [
                        {
                            "date": str(slot["date"]),
                            "start": slot["start"],
                            "end": slot["end"],
                            "hours": slot["hours"],
                        }
                        for slot in prompt_data["free_slots"]
                    ],
                    indent=2,
                    ensure_ascii=False,
                ),
            )
            user_message = user_message.replace(
                "{absences}",
                json.dumps(
                    [
                        {
                            "start": str(abs["start_date"]),
                            "end": str(abs["end_date"]),
                            "label": abs.get("label", "Abwesenheit"),
                        }
                        for abs in prompt_data["absences"]
                    ],
                    indent=2,
                    ensure_ascii=False,
                ),
            )
            user_message = user_message.replace(
                "{busy_times}",
                json.dumps(prompt_data["busy_times"], indent=2, ensure_ascii=False),
            )
        else:
            # Use prompts from selected version
            system_message = get_system_prompt()
            user_message = build_user_prompt(prompt_data)

        # Get model configuration
        model_provider = st.session_state.get("model_provider", "OpenAI")
        model_name = st.session_state.get("model_name", "gpt-4o-mini")

        # Use LLM Service with automatic retry and error handling
        try:
            llm = get_llm_provider(
                provider=model_provider,
                api_key=st.session_state.openai_key,
                model=model_name,
            )

            # Generate JSON response with automatic parsing
            plan = llm.generate_json(
                system_prompt=system_message, user_prompt=user_message
            )

        except LLMRateLimitError as e:
            st.error(f"❌ Rate Limit erreicht: {str(e)}")
            st.info("💡 Tipp: Warte ein paar Sekunden und versuche es erneut.")
            return False

        except LLMResponseError as e:
            st.error(f"❌ Fehler beim Parsen der KI-Antwort: {str(e)}")
            return False

        except LLMError as e:
            st.error(f"❌ LLM API Fehler: {str(e)}")
            return False

        # Validate that plan is a list
        if not isinstance(plan, list):
            st.error("❌ KI-Antwort ist keine gültige Liste von Lerneinheiten.")
            return False

        # Store in session state
        st.session_state.plan = plan

        return True

    except Exception as e:
        st.error(f"❌ Unerwarteter Fehler beim Generieren des Plans: {str(e)}")
        return False


def main():
    """
    Main application entry point.
    Sets up the page configuration, navigation, and routing.
    """
    # Initialize session state
    init_session_state(st.session_state)

    # Page configuration
    st.set_page_config(
        page_title="KI-Lernplaner",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Main title and description
    st.title("📚 KI-Lernplaner für Studierende")
    st.markdown(
        """
    Willkommen beim **KI-Lernplaner**! Diese Anwendung hilft dir, einen personalisierten,
    KI-generierten Lernplan basierend auf deinen Prüfungen, Leistungsnachweisen, Verfügbarkeit und Lernpräferenzen zu erstellen.
    """
    )

    st.markdown("---")

    # Sidebar navigation
    st.sidebar.title("Navigation")
    st.sidebar.markdown("Wähle einen Bereich aus:")

    page = st.sidebar.radio(
        "Gehe zu:", ["Einrichtung", "Lernplan", "Export"], label_visibility="collapsed"
    )

    st.sidebar.markdown("---")

    # MODEL SELECTION
    st.sidebar.subheader("🤖 Modell Konfiguration")

    model_provider = st.sidebar.selectbox(
        "LLM Provider",
        options=["OpenAI", "Google Gemini"],
        index=0,
        key="model_provider_selector",
    )

    api_key = st.sidebar.text_input(
        f"{model_provider} API Key",
        type="password",
        help=f"Gib deinen {model_provider} API Key ein",
        key="api_key_input",
    )

    # Update openai_key in session state for compatibility
    if api_key:
        st.session_state.openai_key = api_key

    if model_provider == "OpenAI":
        model_name = st.sidebar.selectbox(
            "Modell", options=OPENAI_MODELS, index=0, key="openai_model_selector"
        )
    else:  # Gemini
        model_name = st.sidebar.selectbox(
            "Modell", options=GEMINI_MODELS, index=0, key="gemini_model_selector"
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
        help="Vorlagen: Vordefinierte Prompt-Versionen | Manuell: Eigene Prompts schreiben",
    )

    if prompt_mode == "Vorlagen":
        selected_version = st.sidebar.selectbox(
            "Prompt-Version",
            options=list(AVAILABLE_VERSIONS.keys()),
            format_func=lambda x: AVAILABLE_VERSIONS[x],
            index=list(AVAILABLE_VERSIONS.keys()).index(ACTIVE_PROMPT_VERSION),
            key="prompt_version_selector",
            help="Wähle die Prompt-Engineering-Strategie für die KI",
        )

        # Version in Session State speichern
        if "selected_prompt_version" not in st.session_state:
            st.session_state.selected_prompt_version = ACTIVE_PROMPT_VERSION

        if selected_version != st.session_state.selected_prompt_version:
            st.session_state.selected_prompt_version = selected_version
            # Prompts neu laden
            from prompts.prompt_config import set_active_version

            set_active_version(selected_version)
            st.sidebar.success(
                f"✅ Gewechselt zu: {AVAILABLE_VERSIONS[selected_version]}"
            )

        # Manual prompts zurücksetzen
        if "manual_prompts_active" in st.session_state:
            del st.session_state.manual_prompts_active

    else:  # Manueller Modus
        st.sidebar.info("🖊️ **Experimentier-Modus**: Schreibe eigene Prompts ohne Code!")

        # Expander für manuelle Prompt-Bearbeitung
        with st.sidebar.expander("✏️ Prompts bearbeiten", expanded=True):
            # Initialisiere mit Vorlage falls noch nicht gesetzt
            if "manual_system_prompt" not in st.session_state:
                st.session_state.manual_system_prompt = get_system_prompt()

            # System Prompt Editor
            st.markdown("**System Prompt:**")
            manual_system = st.text_area(
                "System Prompt",
                value=st.session_state.manual_system_prompt,
                height=200,
                key="system_prompt_editor",
                label_visibility="collapsed",
                help="Definiert die Rolle und Regeln für die KI",
            )

            # User Prompt Template Editor
            st.markdown("**User Prompt Template:**")
            st.caption(
                "Platzhalter: {semester_start}, {semester_end}, {leistungsnachweise}, {preferences}, {free_slots}"
            )

            if "manual_user_prompt_template" not in st.session_state:
                # Baue Standard-Template
                sample_data = {
                    "semester_start": date.today(),
                    "semester_end": date.today() + timedelta(days=90),
                    "leistungsnachweise": [],
                    "preferences": {},
                    "free_slots": [],
                }
                st.session_state.manual_user_prompt_template = build_user_prompt(
                    sample_data
                )

            manual_user_template = st.text_area(
                "User Prompt Template",
                value=st.session_state.manual_user_prompt_template,
                height=250,
                key="user_prompt_editor",
                label_visibility="collapsed",
                help="Template für User-Prompt (wird mit Daten gefüllt)",
            )

            # Speichern Button
            if st.button(
                "💾 Prompts übernehmen", use_container_width=True, type="primary"
            ):
                st.session_state.manual_system_prompt = manual_system
                st.session_state.manual_user_prompt_template = manual_user_template
                st.session_state.manual_prompts_active = True
                st.success("✅ Manuelle Prompts gespeichert!")
                st.rerun()

            # Reset Button
            if st.button("🔄 Auf Vorlage zurücksetzen", use_container_width=True):
                st.session_state.manual_system_prompt = get_system_prompt()
                sample_data = {
                    "semester_start": date.today(),
                    "semester_end": date.today() + timedelta(days=90),
                    "leistungsnachweise": [],
                    "preferences": {},
                    "free_slots": [],
                }
                st.session_state.manual_user_prompt_template = build_user_prompt(
                    sample_data
                )
                if "manual_prompts_active" in st.session_state:
                    del st.session_state.manual_prompts_active
                st.success("✅ Zurückgesetzt!")
                st.rerun()

        # Export/Import Buttons
        col1, col2 = st.sidebar.columns(2)

        with col1:
            # Export Button
            if st.session_state.get("manual_prompts_active", False):
                prompt_export = {
                    "system_prompt": st.session_state.manual_system_prompt,
                    "user_prompt_template": st.session_state.manual_user_prompt_template,
                    "version": "manual",
                    "timestamp": datetime.now().isoformat(),
                }

                st.download_button(
                    label="📥 Export",
                    data=json.dumps(prompt_export, indent=2, ensure_ascii=False),
                    file_name=f"prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True,
                    help="Speichere deine Prompts als JSON-Datei",
                )

        with col2:
            # Import Button
            uploaded_prompt = st.file_uploader(
                "Import",
                type=["json"],
                key="prompt_import",
                label_visibility="collapsed",
                help="Lade gespeicherte Prompts",
            )

            if uploaded_prompt is not None:
                try:
                    imported_data = json.load(uploaded_prompt)
                    st.session_state.manual_system_prompt = imported_data.get(
                        "system_prompt", ""
                    )
                    st.session_state.manual_user_prompt_template = imported_data.get(
                        "user_prompt_template", ""
                    )
                    st.session_state.manual_prompts_active = True
                    st.success("✅ Prompts importiert!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Fehler beim Import: {str(e)}")

    st.sidebar.markdown("---")

    # TEST-MODUS
    st.sidebar.subheader("🧪 Test-Modus")

    with st.sidebar.expander("ℹ️ Was ist das?", expanded=False):
        st.markdown(
            """
        **Test-Daten** bieten vordefinierte Studenten-Profile:

        - **Fabian (BWL)**: Prüfungen im Winter (Dez/Jan)
        - **Lena (Wirtschaftsinformatik)**: Prüfungen im Sommer (Juni/Juli)

        Jedes Profil enthält:
        - 5 Leistungsnachweise
        - Vorlesungszeiten & Nebenjob
        - Abwesenheiten & Präferenzen

        Perfekt zum Testen der App!
        """
        )

    # Test profile selection
    selected_profile = st.sidebar.selectbox(
        "Testprofil auswählen",
        options=list(AVAILABLE_TEST_PROFILES.keys()),
        format_func=lambda x: AVAILABLE_TEST_PROFILES[x],
        key="test_profile_selector",
        help="Wähle ein Testprofil zum Laden",
    )

    if st.sidebar.button(
        "📋 Test-Daten laden", type="primary", use_container_width=True
    ):
        load_test_data_into_session_state(st, selected_profile)
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.info(
        "💡 Beginne mit **Einrichtung**, um deine Prüfungen und Leistungsnachweise zu erfassen."
    )

    # Route to the selected page
    if page == "Einrichtung":
        show_setup_page()
    elif page == "Lernplan":
        show_plan_page(calculate_free_slots, generate_plan_via_ai)
    elif page == "Export":
        show_export_page()


if __name__ == "__main__":
    main()
