"""
Plan Page - Lernplan-Generierung und Verwaltung
Ermöglicht das Erstellen und Anpassen des KI-gestützten Lernplans
"""

import streamlit as st
from datetime import datetime

# Import constants for weekday handling
from constants import WEEKDAY_NAMES_DE

# Import display functions
from ui.components.display_plan import display_plan_views


def show_plan_page(calculate_free_slots_func, generate_plan_via_ai_func):
    """
    Zeigt die Plan-Generierungs- und Anpassungsseite an.

    Funktionen:
    - LLM-basierte Lernplan-Generierung basierend auf Setup-Daten
    - Anzeige generierter Study Sessions in Kalender- und Listenform
    - Manuelle Anpassung einzelner Sessions (Zeit, Priorität, Aufwand)
    - Plan-Neuberechnung
    - Navigation zur Export-Seite

    Args:
        calculate_free_slots_func: Funktion zur Berechnung verfügbarer Zeitfenster
                                   (planning_service.calculate_free_slots_from_session)
        generate_plan_via_ai_func: Funktion zur KI-basierten Plan-Generierung
                                   (llm_service Provider)

    Verwendet:
        - services.llm_service für KI-Generierung
        - services.planning_service für Zeitfenster-Berechnung
        - display_plan.display_plan_views für Visualisierung
    """
    st.header("📅 Lernplan")
    st.markdown(
        "Hier kannst du deinen KI-gestützten Lernplan generieren, anzeigen und bei Bedarf feinjustieren."
    )

    # Check if setup is complete
    setup_complete = (
        len(st.session_state.leistungsnachweise) > 0
        and st.session_state.openai_key
        and st.session_state.study_end is not None
    )

    if not setup_complete:
        st.warning(
            """
        ⚠️ **Einrichtung unvollständig**

        Bitte vervollständige zuerst die Einrichtungs-Seite:
        - Füge mindestens einen Leistungsnachweis hinzu
        - Gib deinen API-Schlüssel ein (OpenAI oder Gemini)
        - Setze gültige Semester-Daten
        """
        )
        return

    st.markdown("---")

    # Check if plan already exists
    plan_exists = (
        "plan" in st.session_state
        and st.session_state.plan
        and len(st.session_state.plan) > 0
    )

    # ========== ZUSTAND 1: NOCH KEIN PLAN ==========
    if not plan_exists:
        st.subheader("Schritt 1: Lernplan generieren")
        st.markdown(
            """
        Basierend auf deinen Prüfungen, Leistungsnachweisen, belegten Zeiten und Lernpräferenzen
        erstellt die KI einen ersten Vorschlag für deinen Lernplan.
        """
        )

        st.info(
            """
        **ℹ️ Was passiert bei der Generierung?**

        Die KI wird:
        - Deine verfügbaren freien Zeitfenster berechnen
        - Alle Leistungsnachweise und deren Deadlines berücksichtigen
        - Einen optimalen Lernplan erstellen, der zu deinen Präferenzen passt

        Dies kann 30-60 Sekunden dauern.
        """
        )

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            if st.button(
                "🤖 Lernplan jetzt generieren",
                type="primary",
                use_container_width=True,
                key="generate_initial_plan",
            ):
                with st.spinner("🧠 KI erstellt deinen personalisierten Lernplan..."):
                    # Calculate free slots first
                    free_slots = calculate_free_slots_func()
                    st.session_state.free_slots = free_slots

                    if not free_slots:
                        st.error(
                            "❌ Keine freien Zeitfenster gefunden. Bitte überprüfe deine Einstellungen."
                        )
                    else:
                        # Calculate total available hours and check against estimated need
                        total_available_hours = sum(slot.get("hours", 0) for slot in free_slots)
                        
                        # Estimate needed hours based on leistungsnachweise
                        estimated_needed_hours = 0
                        for ln in st.session_state.leistungsnachweise:
                            effort = ln.get("effort", 3)
                            # Estimate: effort 1 = 5h, effort 5 = 25h
                            estimated_needed_hours += 5 + (effort - 1) * 5
                        
                        # Show warning if available hours are less than estimated need
                        if total_available_hours < estimated_needed_hours:
                            st.warning(
                                f"""⚠️ **Hinweis zu Lernzeit-Limits:**
                                
Die verfügbare Lernzeit ({total_available_hours:.1f}h) ist möglicherweise geringer als der geschätzte Bedarf ({estimated_needed_hours:.0f}h).

**Mögliche Anpassungen:**
- Max. Stunden pro Tag/Woche erhöhen
- Ruhetage reduzieren
- Abwesenheiten verkürzen
- Min. Session-Dauer verringern

Der Plan wird dennoch erstellt, aber möglicherweise nicht alle Themen abdecken."""
                            )
                        
                        # Generate plan via AI
                        success = generate_plan_via_ai_func()

                        if success:
                            st.success(
                                f"✅ Lernplan erfolgreich generiert! {len(st.session_state.plan)} Lerneinheiten gefunden."
                            )
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(
                                "❌ Plan-Generierung fehlgeschlagen. Bitte versuche es erneut."
                            )

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
            unique_assessments = len(
                set([session.get("module", "Unknown") for session in plan])
            )
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
        st.markdown(
            """
        Hier kannst du Prioritäten, Lernaufwand, belegte Zeiten und Lern-Limits anpassen.
        Anschliessend kannst du einen neuen Lernplan auf Basis deiner aktualisierten Einstellungen erstellen.
        """
        )

        # Create tabs for different adjustment categories
        adj_tabs = st.tabs(
            ["Prioritäten & Aufwand", "Belegte Zeiten", "Lernpräferenzen"]
        )

        # ========== TAB 1: PRIORITÄTEN & LERNAUFWAND ==========
        with adj_tabs[0]:
            st.markdown(
                "**Passe Prioritätslevel und Lernaufwand für jeden Leistungsnachweis an.**"
            )
            st.caption("Höhere Werte = mehr Lernzeit zugeteilt")

            if st.session_state.leistungsnachweise:
                for idx, ln in enumerate(st.session_state.leistungsnachweise):
                    with st.container():
                        col1, col2, col3 = st.columns([3, 2, 2])

                        with col1:
                            # Convert enum to string if needed
                            ln_type_display = (
                                ln["type"].value
                                if hasattr(ln["type"], "value")
                                else ln["type"]
                            )
                            st.markdown(f"**{ln['title']}** ({ln_type_display})")
                            if ln.get("deadline"):
                                st.caption(
                                    f"Fällig: {ln['deadline'].strftime('%d.%m.%Y')}"
                                )
                            if ln.get("module"):
                                st.caption(f"Modul: {ln['module']}")

                        with col2:
                            new_priority = st.slider(
                                "Priorität",
                                min_value=1,
                                max_value=5,
                                value=ln.get("priority", 3),
                                key=f"priority_adjust_{idx}",
                                help="1 = niedrige Priorität, 5 = hohe Priorität",
                            )
                            st.session_state.leistungsnachweise[idx][
                                "priority"
                            ] = new_priority

                        with col3:
                            new_effort = st.slider(
                                "Lernaufwand",
                                min_value=1,
                                max_value=5,
                                value=ln.get("effort", 3),
                                key=f"effort_adjust_{idx}",
                                help="1 = wenig Aufwand, 5 = sehr viel Aufwand",
                            )
                            st.session_state.leistungsnachweise[idx][
                                "effort"
                            ] = new_effort

                    if idx < len(st.session_state.leistungsnachweise) - 1:
                        st.markdown("")

                st.success("✅ Änderungen werden automatisch gespeichert")
            else:
                st.info("Keine Leistungsnachweise vorhanden.")

        # ========== TAB 2: BELEGTE ZEITEN ==========
        with adj_tabs[1]:
            st.markdown(
                "**Verwalte deine wiederkehrenden wöchentlichen Verpflichtungen.**"
            )
            st.caption("Tipp: Setze ein Gültigkeits-Enddatum für Vorlesungen, die vor den Prüfungen enden.")

            # Display existing busy times with edit functionality
            if st.session_state.busy_times:
                st.markdown("**Aktuelle belegte Zeiten:**")

                for idx, busy in enumerate(st.session_state.busy_times):
                    days_str = ", ".join(busy["days"])
                    valid_from = busy.get("valid_from")
                    valid_until = busy.get("valid_until")
                    validity_str = ""
                    if valid_until:
                        validity_str = f" (bis {valid_until.strftime('%d.%m.%Y')})"
                    
                    with st.expander(
                        f"• **{busy['label']}**: {days_str}, {busy['start']}-{busy['end']}{validity_str}",
                        expanded=False
                    ):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            edit_label = st.text_input(
                                "Bezeichnung",
                                value=busy["label"],
                                key=f"plan_edit_busy_label_{idx}",
                            )
                            edit_days = st.multiselect(
                                "Tage",
                                WEEKDAY_NAMES_DE,
                                default=busy["days"],
                                key=f"plan_edit_busy_days_{idx}",
                            )
                        
                        with col2:
                            try:
                                current_start = datetime.strptime(busy["start"], "%H:%M").time()
                            except:
                                current_start = None
                            edit_start = st.time_input(
                                "Startzeit",
                                value=current_start,
                                key=f"plan_edit_busy_start_{idx}",
                            )
                            try:
                                current_end = datetime.strptime(busy["end"], "%H:%M").time()
                            except:
                                current_end = None
                            edit_end = st.time_input(
                                "Endzeit",
                                value=current_end,
                                key=f"plan_edit_busy_end_{idx}",
                            )
                        
                        st.markdown("**Gültigkeitszeitraum:**")
                        col_v1, col_v2 = st.columns(2)
                        with col_v1:
                            edit_valid_from = st.date_input(
                                "Gültig ab",
                                value=valid_from if valid_from else st.session_state.study_start,
                                format="DD.MM.YYYY",
                                key=f"plan_edit_busy_valid_from_{idx}",
                            )
                        with col_v2:
                            edit_valid_until = st.date_input(
                                "Gültig bis",
                                value=valid_until,
                                format="DD.MM.YYYY",
                                key=f"plan_edit_busy_valid_until_{idx}",
                            )
                        
                        col_save, col_delete = st.columns(2)
                        with col_save:
                            if st.button(
                                "💾 Speichern",
                                key=f"plan_save_busy_{idx}",
                                use_container_width=True,
                            ):
                                if edit_label and edit_days and edit_start and edit_end:
                                    st.session_state.busy_times[idx] = {
                                        "label": edit_label,
                                        "days": edit_days,
                                        "start": edit_start.strftime("%H:%M"),
                                        "end": edit_end.strftime("%H:%M"),
                                        "valid_from": edit_valid_from,
                                        "valid_until": edit_valid_until,
                                    }
                                    st.success("Belegte Zeit aktualisiert!")
                                    st.rerun()
                                else:
                                    st.error("Bitte alle Pflichtfelder ausfüllen.")
                        
                        with col_delete:
                            if st.button(
                                "🗑️ Entfernen",
                                key=f"plan_remove_busy_{idx}",
                                use_container_width=True,
                                type="secondary",
                            ):
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
                        new_busy_label = st.text_input(
                            "Bezeichnung", placeholder="z.B. Vorlesung, Meeting"
                        )
                        # Use German weekday names for consistency with setup_page
                        new_busy_days = st.multiselect(
                            "Tage",
                            WEEKDAY_NAMES_DE,
                            help="Wähle alle Tage aus, an denen diese belegte Zeit auftritt",
                        )

                    with col2:
                        new_busy_start = st.time_input("Startzeit", value=None)
                        new_busy_end = st.time_input("Endzeit", value=None)
                    
                    st.markdown("**Gültigkeitszeitraum (optional):**")
                    col_v1, col_v2 = st.columns(2)
                    with col_v1:
                        new_valid_from = st.date_input(
                            "Gültig ab",
                            value=st.session_state.study_start,
                            format="DD.MM.YYYY",
                        )
                    with col_v2:
                        new_valid_until = st.date_input(
                            "Gültig bis (leer = Semester-Ende)",
                            value=None,
                            format="DD.MM.YYYY",
                        )

                    if st.form_submit_button("Hinzufügen", use_container_width=True):
                        if (
                            new_busy_label
                            and new_busy_days
                            and new_busy_start
                            and new_busy_end
                        ):
                            st.session_state.busy_times.append(
                                {
                                    "label": new_busy_label,
                                    "days": new_busy_days,
                                    "start": new_busy_start.strftime("%H:%M"),
                                    "end": new_busy_end.strftime("%H:%M"),
                                    "valid_from": new_valid_from,
                                    "valid_until": new_valid_until,
                                }
                            )
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
                    help="Verteile Lerneinheiten über mehrere Tage mit steigenden Intervallen",
                )
                st.session_state.preferences["spacing"] = spacing

                interleaving = st.checkbox(
                    "Interleaving von Fächern",
                    value=st.session_state.preferences.get("interleaving", False),
                    key="adjust_interleaving",
                    help="Mische verschiedene Leistungsnachweise innerhalb eines Tages",
                )
                st.session_state.preferences["interleaving"] = interleaving

                deep_work = st.checkbox(
                    "Deep Work (lange Fokusblöcke)",
                    value=st.session_state.preferences.get("deep_work", False),
                    key="adjust_deep_work",
                    help="Nutze längere Sessions (2-3h) für komplexe Themen",
                )
                st.session_state.preferences["deep_work"] = deep_work

                short_sessions = st.checkbox(
                    "Kurze Sessions für Theorie",
                    value=st.session_state.preferences.get("short_sessions", False),
                    key="adjust_short_sessions",
                    help="Nutze kürzere Sessions (45-60 Min) für theorielastige Inhalte",
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
                    help="Maximale Lernstunden pro Tag",
                )
                st.session_state.preferences["max_hours_day"] = max_hours_day

                max_hours_week = st.number_input(
                    "Max. Stunden pro Woche",
                    min_value=5,
                    max_value=80,
                    value=st.session_state.preferences.get("max_hours_week", 30),
                    key="adjust_max_hours_week",
                    help="Maximale Lernstunden pro Woche (0 = unbegrenzt)",
                )
                st.session_state.preferences["max_hours_week"] = (
                    max_hours_week if max_hours_week > 0 else None
                )

                min_session_duration = st.number_input(
                    "Min. Session-Dauer (Minuten)",
                    min_value=15,
                    max_value=120,
                    value=st.session_state.preferences.get("min_session_duration", 60),
                    step=15,
                    key="adjust_min_session_duration",
                    help="Minimale Länge einer Lerneinheit",
                )
                st.session_state.preferences["min_session_duration"] = (
                    min_session_duration
                )

        # ========== NEU-GENERIERUNG BUTTON ==========
        st.markdown("---")

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            if st.button(
                "🔄 Lernplan mit aktualisierten Einstellungen neu generieren",
                type="primary",
                use_container_width=True,
                key="regenerate_plan",
            ):
                with st.spinner("🧠 KI erstellt deinen aktualisierten Lernplan..."):
                    # Recalculate free slots with updated settings
                    free_slots = calculate_free_slots_func()
                    st.session_state.free_slots = free_slots

                    if not free_slots:
                        st.error(
                            "❌ Keine freien Zeitfenster gefunden. Bitte überprüfe deine Einstellungen."
                        )
                    else:
                        # Regenerate plan
                        success = generate_plan_via_ai_func()

                        if success:
                            st.success(
                                f"✅ Lernplan erfolgreich neu generiert! {len(st.session_state.plan)} Lerneinheiten gefunden."
                            )
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ Plan-Generierung fehlgeschlagen.")
