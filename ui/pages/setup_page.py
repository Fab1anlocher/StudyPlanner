"""
Setup Page - Einrichtung des Lernplaners
Sammelt alle notwendigen Daten für die KI-gestützte Planung
"""

import streamlit as st
from datetime import datetime

# Import constants
from constants import (
    WEEKDAY_NAMES_DE,
    LEISTUNGSNACHWEIS_TYPES,
    EXAM_FORMATS,
    MIN_PRIORITY,
    MAX_PRIORITY,
    MIN_EFFORT,
    MAX_EFFORT,
)


def show_setup_page():
    """
    Zeigt die Setup-Seite an, auf der Benutzer ihre Lernplan-Konfiguration vornehmen.

    Sammelt folgende Daten:
    - Lernplan-Startzeitpunkt
    - Leistungsnachweise (Prüfungen, Präsentationen, etc.)
    - Feste Termine (Vorlesungen, Arbeit, etc.)
    - Abwesenheiten (Urlaub, Events, etc.)
    - Benutzerpräferenzen (LLM-Provider, Modell, Lernstrategien)

    Speichert alle Daten in st.session_state für die Plan-Generierung.
    """
    # ========== SECTION 1: STUDY PLAN START DATE ==========
    st.subheader("1️⃣ Start deines Lernplans")
    st.markdown("Ab wann möchtest du aktiv mit dem Lernen beginnen?")

    study_start = st.date_input(
        "Lernplan-Start",
        value=st.session_state.study_start,
        format="DD.MM.YYYY",
        help="Ab wann möchtest du mit dem Lernplan beginnen?",
    )
    st.session_state.study_start = study_start

    # Automatically calculate study_end from latest deadline
    if st.session_state.leistungsnachweise:
        deadlines = [
            ln["deadline"]
            for ln in st.session_state.leistungsnachweise
            if ln.get("deadline")
        ]
        if deadlines:
            st.session_state.study_end = max(deadlines)
            st.info(
                f"ℹ️ Der Lernplan endet automatisch am Tag deines letzten Leistungsnachweises: **{st.session_state.study_end.strftime('%d.%m.%Y')}**"
            )
        else:
            st.session_state.study_end = None
    else:
        st.session_state.study_end = None

    st.markdown("---")

    # ========== SECTION 2: LEISTUNGSNACHWEISE ==========
    st.subheader("2️⃣ Prüfungen & Leistungsnachweise")
    st.markdown(
        "Füge alle Prüfungen, Hausarbeiten, Projekte oder Präsentationen hinzu, die du in diesem Semester abschliessen musst."
    )

    # Form to add new Leistungsnachweis
    # Typ-Auswahl AUSSERHALB des Formulars für dynamische UI
    st.markdown("**Neuen Leistungsnachweis hinzufügen:**")

    ln_type_preview = st.selectbox(
        "Typ",
        LEISTUNGSNACHWEIS_TYPES,
        help="Art des Leistungsnachweises",
        key="ln_type_preview",
    )

    with st.form("add_leistungsnachweis_form", clear_on_submit=True):
        col1, col2 = st.columns([2, 1])

        with col1:
            ln_title = st.text_input(
                "Titel des Leistungsnachweises",
                placeholder="z.B. Prüfung Data Science, Seminararbeit, Präsentation",
                help="Der Titel deiner Prüfung, Arbeit oder Präsentation",
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
                help="Wann findet die Prüfung statt oder ist die Abgabe fällig?",
            )

        with col4:
            ln_module = st.text_input(
                "Zugehöriges Modul (optional)",
                placeholder="z.B. Höhere Mathematik I",
                help="Falls dieser Leistungsnachweis zu einem bestimmten Kurs/Modul gehört",
            )

        ln_topics_input = st.text_area(
            "Themen / Inhalte (optional)",
            placeholder="Gib ein Thema pro Zeile ein, z.B.:\nKapitel 1: Analysis\nKapitel 2: Lineare Algebra\nAbschlussprojekt",
            help="Liste die Hauptthemen oder Aufgaben für diesen Leistungsnachweis auf (eines pro Zeile)",
            height=100,
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
                    EXAM_FORMATS,
                    help="Welches Format hat die Prüfung? Wichtig für die Lernstrategie!",
                )

            with col_details:
                ln_exam_details = st.text_input(
                    "Weitere Details (optional)",
                    placeholder="z.B. '90 Min, Closed Book' oder 'Open Book, Laptop erlaubt'",
                    help="Weitere Details wie Dauer, erlaubte Hilfsmittel, Anzahl Fragen etc.",
                )

        col5, col6 = st.columns(2)

        with col5:
            ln_priority = st.slider(
                "Prioritätsstufe",
                min_value=MIN_PRIORITY,
                max_value=MAX_PRIORITY,
                value=3,
                help="Wie wichtig ist dieser Leistungsnachweis? (1=niedrig, 5=hoch)",
            )

        with col6:
            ln_effort = st.slider(
                "Lernaufwand",
                min_value=MIN_EFFORT,
                max_value=MAX_EFFORT,
                value=3,
                help="Wie viel Lernaufwand braucht dieser Leistungsnachweis? (1 = wenig, 5 = sehr viel)",
            )

        submitted = st.form_submit_button(
            "➕ Leistungsnachweis hinzufügen", use_container_width=True
        )

        if submitted:
            if ln_title.strip():
                # Parse topics from textarea (one per line, filter empty lines)
                topics_list = [
                    t.strip() for t in ln_topics_input.split("\n") if t.strip()
                ]

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
                    "exam_details": (
                        ln_exam_details if ln_exam_details.strip() else None
                    ),
                }

                # Add to session state
                st.session_state.leistungsnachweise.append(new_ln)
                st.success(
                    f"✅ Leistungsnachweis '{ln_title}' erfolgreich hinzugefügt!"
                )
                st.rerun()
            else:
                st.error("⚠️ Bitte gib einen Titel für den Leistungsnachweis ein.")

    # Display existing Leistungsnachweise
    if st.session_state.leistungsnachweise:
        st.markdown("---")
        st.markdown("**📚 Deine Leistungsnachweise:**")

        for idx, ln in enumerate(st.session_state.leistungsnachweise):
            # Convert enum to string if needed (backward compatibility)
            ln_type_display = (
                ln["type"].value if hasattr(ln["type"], "value") else ln["type"]
            )

            # Build expander title
            expander_title = f"**{ln['title']}** ({ln_type_display}) - Priorität: {ln.get('priority', 3)}/5, Lernaufwand: {ln.get('effort', 3)}/5"

            with st.expander(expander_title, expanded=False):
                col1, col2 = st.columns([3, 1])

                with col1:
                    if ln["deadline"]:
                        st.write(
                            f"📅 **Fälligkeitsdatum:** {ln['deadline'].strftime('%d. %B %Y')}"
                        )
                    else:
                        st.write("📅 **Fälligkeitsdatum:** Nicht angegeben")

                    if ln.get("module"):
                        st.write(f"📚 **Zugehöriges Modul:** {ln['module']}")

                    # Prüfungsformat nur bei Typ "Prüfung" anzeigen
                    if ln_type_display == "Prüfung" and ln.get("exam_format"):
                        exam_format_display = (
                            ln["exam_format"].value
                            if hasattr(ln["exam_format"], "value")
                            else ln["exam_format"]
                        )
                        exam_info = f"📋 **Prüfungsformat:** {exam_format_display}"
                        if ln.get("exam_details"):
                            exam_info += f" - {ln['exam_details']}"
                        st.write(exam_info)

                    if ln["topics"]:
                        st.write(f"📝 **Themen ({len(ln['topics'])}):**")
                        for topic in ln["topics"]:
                            st.write(f"  • {topic}")
                    else:
                        st.write("📝 **Themen:** Keine angegeben")

                with col2:
                    if st.button(
                        "🗑️ Entfernen", key=f"remove_ln_{idx}", use_container_width=True
                    ):
                        st.session_state.leistungsnachweise.pop(idx)
                        st.success(f"Leistungsnachweis '{ln['title']}' entfernt.")
                        st.rerun()

        # Summary
        st.info(
            f"📊 Total Leistungsnachweise: {len(st.session_state.leistungsnachweise)}"
        )
    else:
        st.info(
            "ℹ️ Noch keine Leistungsnachweise hinzugefügt. Nutze das Formular oben, um deinen ersten Leistungsnachweis hinzuzufügen."
        )

    st.markdown("---")

    # ========== SECTION 3: API KEY (INFO ONLY) ==========
    st.subheader("3️⃣ LLM API-Konfiguration")
    st.markdown(
        "Gib deinen API-Schlüssel in der **Sidebar unter 'Modell-Konfiguration'** ein. "
        "Du kannst zwischen **OpenAI** (GPT-4, GPT-3.5) und **Google Gemini** wählen."
    )

    # Zeige nur Status an, kein Input-Feld mehr
    if st.session_state.openai_key:
        st.success("✅ API-Schlüssel konfiguriert")
    else:
        st.info(
            "💡 **Hinweis:** API-Schlüssel in der Sidebar eingeben → Modell-Konfiguration"
        )

    st.markdown("---")

    # ========== SECTION 4: BUSY TIMES (RECURRING WEEKLY SCHEDULE) ==========
    st.subheader("4️⃣ Belegte Zeiten (wöchentliche Verpflichtungen)")
    st.markdown(
        "Definiere deine regelmässigen wöchentlichen Verpflichtungen (Arbeit, Vorlesungen, Sport etc.), damit der Planer weiss, wann du nicht verfügbar bist."
    )

    # Form to add busy interval
    with st.form("add_busy_time_form", clear_on_submit=True):
        st.markdown("**Neue belegte Zeit hinzufügen:**")

        col1, col2 = st.columns([2, 1])

        with col1:
            busy_label = st.text_input(
                "Bezeichnung",
                placeholder="z.B. Arbeit, Vorlesung, Fitnessstudio, Nebenjob",
                help="z.B. Arbeit, Vorlesung, Fitnessstudio, Nebenjob",
            )

            busy_days = st.multiselect(
                "Wochentage",
                WEEKDAY_NAMES_DE,
                help="Wähle alle Tage aus, an denen diese belegte Zeit auftritt",
            )

        with col2:
            busy_start = st.time_input(
                "Startzeit", value=None, help="Wann beginnt diese Verpflichtung?"
            )

            busy_end = st.time_input(
                "Endzeit", value=None, help="Wann endet diese Verpflichtung?"
            )

        # Validity period for the busy time
        st.markdown("**Gültigkeitszeitraum (optional):**")
        st.caption("Lasse leer, wenn die Verpflichtung während des gesamten Semesters gilt (z.B. Arbeit). Setze ein Enddatum für zeitlich begrenzte Verpflichtungen (z.B. Vorlesungen enden Mitte Dezember).")
        
        col_valid1, col_valid2 = st.columns(2)
        with col_valid1:
            busy_valid_from = st.date_input(
                "Gültig ab",
                value=st.session_state.study_start,
                format="DD.MM.YYYY",
                help="Ab wann gilt diese Verpflichtung? (Standard: Lernplan-Start)",
            )
        with col_valid2:
            busy_valid_until = st.date_input(
                "Gültig bis",
                value=None,
                format="DD.MM.YYYY",
                help="Bis wann gilt diese Verpflichtung? Leer = bis Semester-Ende",
            )

        submitted_busy = st.form_submit_button(
            "➕ Neue belegte Zeit hinzufügen", use_container_width=True
        )

        if submitted_busy:
            if busy_label.strip() and busy_days and busy_start and busy_end:
                # Convert time objects to string format for storage
                new_busy_time = {
                    "label": busy_label,
                    "days": busy_days,
                    "start": busy_start.strftime("%H:%M"),
                    "end": busy_end.strftime("%H:%M"),
                    "valid_from": busy_valid_from,
                    "valid_until": busy_valid_until,  # Can be None
                }

                st.session_state.busy_times.append(new_busy_time)
                st.success(f"✅ Belegte Zeit '{busy_label}' hinzugefügt!")
                st.rerun()
            else:
                st.error(
                    "⚠️ Bitte fülle alle Felder aus (Bezeichnung, Tage, Startzeit und Endzeit)."
                )

    st.info(
        "💡 Diese Zeiten werden bei der Berechnung deiner freien Lernfenster automatisch ausgeschlossen. Nach dem Gültigkeitszeitraum werden sie nicht mehr blockiert."
    )

    # Display existing busy times with edit functionality
    if st.session_state.busy_times:
        st.markdown("**📅 Deine belegten Zeiten:**")

        for idx, busy in enumerate(st.session_state.busy_times):
            days_str = ", ".join(busy["days"])
            
            # Build expander title with validity info
            valid_from = busy.get("valid_from")
            valid_until = busy.get("valid_until")
            validity_str = ""
            if valid_from or valid_until:
                from_str = valid_from.strftime("%d.%m.%Y") if valid_from else "Start"
                until_str = valid_until.strftime("%d.%m.%Y") if valid_until else "Ende"
                validity_str = f" | Gültig: {from_str} - {until_str}"
            
            with st.expander(
                f"🔸 **{busy['label']}**: {days_str}, {busy['start']}-{busy['end']}{validity_str}",
                expanded=False
            ):
                # Edit form for this busy time
                col1, col2 = st.columns(2)
                
                with col1:
                    new_label = st.text_input(
                        "Bezeichnung",
                        value=busy["label"],
                        key=f"edit_busy_label_{idx}",
                    )
                    new_days = st.multiselect(
                        "Wochentage",
                        WEEKDAY_NAMES_DE,
                        default=busy["days"],
                        key=f"edit_busy_days_{idx}",
                    )
                    # Get current time values or parse from string
                    try:
                        current_start = datetime.strptime(busy["start"], "%H:%M").time()
                    except:
                        current_start = None
                    new_start = st.time_input(
                        "Startzeit",
                        value=current_start,
                        key=f"edit_busy_start_{idx}",
                    )
                
                with col2:
                    try:
                        current_end = datetime.strptime(busy["end"], "%H:%M").time()
                    except:
                        current_end = None
                    new_end = st.time_input(
                        "Endzeit",
                        value=current_end,
                        key=f"edit_busy_end_{idx}",
                    )
                    new_valid_from = st.date_input(
                        "Gültig ab",
                        value=busy.get("valid_from", st.session_state.study_start),
                        format="DD.MM.YYYY",
                        key=f"edit_busy_valid_from_{idx}",
                    )
                    new_valid_until = st.date_input(
                        "Gültig bis (leer = Semester-Ende)",
                        value=busy.get("valid_until"),
                        format="DD.MM.YYYY",
                        key=f"edit_busy_valid_until_{idx}",
                    )
                
                col_save, col_delete = st.columns(2)
                
                with col_save:
                    if st.button("💾 Speichern", key=f"save_busy_{idx}", use_container_width=True):
                        if new_label.strip() and new_days and new_start and new_end:
                            st.session_state.busy_times[idx] = {
                                "label": new_label,
                                "days": new_days,
                                "start": new_start.strftime("%H:%M"),
                                "end": new_end.strftime("%H:%M"),
                                "valid_from": new_valid_from,
                                "valid_until": new_valid_until,
                            }
                            st.success("Belegte Zeit aktualisiert!")
                            st.rerun()
                        else:
                            st.error("Bitte alle Pflichtfelder ausfüllen.")
                
                with col_delete:
                    if st.button("🗑️ Entfernen", key=f"remove_busy_{idx}", use_container_width=True, type="secondary"):
                        st.session_state.busy_times.pop(idx)
                        st.success("Belegte Zeit entfernt.")
                        st.rerun()

        st.info(f"📊 Total belegte Zeitfenster: {len(st.session_state.busy_times)}")
    else:
        st.info(
            "ℹ️ Noch keine belegten Zeiten hinzugefügt. Nutze das Formular oben, um deine Verpflichtungen hinzuzufügen."
        )

    st.markdown("---")

    # ========== SECTION 5: ABSENCES / EXCEPTIONS ==========
    st.subheader("5️⃣ Abwesenheiten & Ausnahmen")
    st.markdown(
        "Definiere Zeiträume, in denen du komplett nicht verfügbar bist (Ferien, Militärdienst, Events etc.)."
    )

    # Form to add absence
    with st.form("add_absence_form", clear_on_submit=True):
        st.markdown("**Neue Abwesenheitsperiode hinzufügen:**")

        col1, col2, col3 = st.columns([2, 2, 2])

        with col1:
            absence_start = st.date_input(
                "Startdatum",
                value=None,
                format="DD.MM.YYYY",
                help="Erster Tag deiner Abwesenheit",
            )

        with col2:
            absence_end = st.date_input(
                "Enddatum",
                value=None,
                format="DD.MM.YYYY",
                help="Letzter Tag deiner Abwesenheit",
            )

        with col3:
            absence_label = st.text_input(
                "Bezeichnung (optional)",
                placeholder="z.B. Ferien, Militär, Konferenz",
                help="Beschreibung dieser Abwesenheit",
            )

        submitted_absence = st.form_submit_button(
            "➕ Abwesenheit hinzufügen", use_container_width=True
        )

        if submitted_absence:
            if absence_start and absence_end:
                if absence_end >= absence_start:
                    new_absence = {
                        "start_date": absence_start,
                        "end_date": absence_end,
                        "label": (
                            absence_label if absence_label.strip() else "Abwesenheit"
                        ),
                    }

                    st.session_state.absences.append(new_absence)
                    st.success(f"✅ Abwesenheitsperiode hinzugefügt!")
                    st.rerun()
                else:
                    st.error("⚠️ Enddatum muss gleich oder nach dem Startdatum liegen.")
            else:
                st.error("⚠️ Bitte wähle Start- und Enddatum aus.")

    # Display existing absences with edit functionality
    if st.session_state.absences:
        st.markdown("**🚫 Deine Abwesenheitsperioden:**")

        for idx, absence in enumerate(st.session_state.absences):
            days_count = (absence["end_date"] - absence["start_date"]).days + 1
            
            # Check for conflicts with exams
            has_conflict = False
            conflict_exams = []
            for ln in st.session_state.leistungsnachweise:
                deadline = ln.get("deadline")
                if deadline and absence["start_date"] <= deadline <= absence["end_date"]:
                    has_conflict = True
                    conflict_exams.append(ln.get("title", "Unbekannt"))
            
            with st.expander(
                f"{'⚠️ ' if has_conflict else ''}🔸 {absence['label']}: {absence['start_date'].strftime('%d.%m.%Y')} - {absence['end_date'].strftime('%d.%m.%Y')} ({days_count} Tage)",
                expanded=False
            ):
                if has_conflict:
                    st.error(f"⚠️ **Konflikt mit Prüfungen/Abgaben:** {', '.join(conflict_exams)}")
                
                # Edit form for this absence
                col1, col2 = st.columns(2)
                
                with col1:
                    new_start = st.date_input(
                        "Startdatum",
                        value=absence["start_date"],
                        format="DD.MM.YYYY",
                        key=f"edit_absence_start_{idx}",
                    )
                    new_label = st.text_input(
                        "Bezeichnung",
                        value=absence["label"],
                        key=f"edit_absence_label_{idx}",
                    )
                
                with col2:
                    new_end = st.date_input(
                        "Enddatum",
                        value=absence["end_date"],
                        format="DD.MM.YYYY",
                        key=f"edit_absence_end_{idx}",
                    )
                
                col_save, col_delete = st.columns(2)
                
                with col_save:
                    if st.button("💾 Speichern", key=f"save_absence_{idx}", use_container_width=True):
                        if new_end >= new_start:
                            st.session_state.absences[idx] = {
                                "start_date": new_start,
                                "end_date": new_end,
                                "label": new_label if new_label.strip() else "Abwesenheit",
                            }
                            st.success("Abwesenheit aktualisiert!")
                            st.rerun()
                        else:
                            st.error("Enddatum muss nach Startdatum liegen.")
                
                with col_delete:
                    if st.button("🗑️ Entfernen", key=f"remove_absence_{idx}", use_container_width=True, type="secondary"):
                        st.session_state.absences.pop(idx)
                        st.success("Abwesenheit entfernt.")
                        st.rerun()

        st.info(f"📊 Total Abwesenheitsperioden: {len(st.session_state.absences)}")
    else:
        st.info(
            "ℹ️ Noch keine Abwesenheiten hinzugefügt. Füge Perioden hinzu, in denen du nicht verfügbar bist."
        )

    st.markdown("---")

    # ========== SECTION 6: REST DAYS & STUDY LIMITS ==========
    st.subheader("6️⃣ Ruhetage & Lern-Limits")
    st.markdown(
        "Konfiguriere deine bevorzugten Ruhetage und maximale tägliche/wöchentliche Lernstunden."
    )

    col1, col2 = st.columns(2)

    with col1:
        rest_days = st.multiselect(
            "Ruhetage (kein Lernen)",
            WEEKDAY_NAMES_DE,
            default=st.session_state.preferences.get("rest_days", []),
            help="Tage, an denen du komplett ruhen möchtest (keine Lerneinheiten werden eingeplant)",
        )

        max_hours_day = st.number_input(
            "Max. Lernstunden pro Tag",
            min_value=1,
            max_value=24,
            value=st.session_state.preferences.get("max_hours_day", 8),
            help="Maximale Anzahl Stunden, die du an einem Tag lernen möchtest",
        )

    with col2:
        max_hours_week = st.number_input(
            "Max. Lernstunden pro Woche (optional)",
            min_value=0,
            max_value=168,
            value=st.session_state.preferences.get("max_hours_week", 40),
            help="Maximale totale Lernstunden pro Woche (0 = kein Limit)",
        )

        min_session_duration = st.number_input(
            "Minimale Einheiten-Dauer (Minuten)",
            min_value=15,
            max_value=240,
            value=st.session_state.preferences.get("min_session_duration", 60),
            step=15,
            help="Kürzeste akzeptable Lerneinheit-Länge",
        )

    st.markdown("**ℹ️ Hinweis zu Lernzeiten:**")
    st.info(
        "Die KI plant Lernzeiten intelligent basierend auf deinen bevorzugten Tageszeiten (siehe unten). Es werden keine unmöglichen Zeiten gewählt (z.B. nachts oder sehr früh morgens)."
    )

    # Update preferences in session state
    st.session_state.preferences.update(
        {
            "rest_days": rest_days,
            "max_hours_day": max_hours_day,
            "max_hours_week": max_hours_week if max_hours_week > 0 else None,
            "min_session_duration": min_session_duration,
        }
    )

    st.success("✅ Einstellungen automatisch gespeichert")

    st.markdown("---")

    # ========== SECTION 7: LEARNING PREFERENCES ==========
    st.subheader("7️⃣ Lernpräferenzen")
    st.markdown(
        "Hier kannst du festlegen, wie dein Lernplan aufgebaut werden soll. Wenn du unsicher bist, kannst du auch einfach die empfohlenen Einstellungen verwenden."
    )

    col1, col2 = st.columns(2)

    with col1:
        spacing = st.checkbox(
            "Wiederholen mit Abständen (Spaced Repetition)",
            value=st.session_state.preferences.get("spacing", True),
            help="Der Stoff wird mehrmals über mehrere Tage/Wochen verteilt wiederholt, statt alles kurz vor der Prüfung zu lernen. Gut für Fächer mit viel Theorie und Definitionen.",
        )

        interleaving = st.checkbox(
            "Fächer mischen (Interleaving)",
            value=st.session_state.preferences.get("interleaving", False),
            help="Verschiedene Fächer oder Themen werden innerhalb einer Woche gemischt statt in grossen Blöcken gelernt. Hilft, Inhalte besser zu unterscheiden – sinnvoll, wenn du mehrere ähnliche Fächer parallel hast.",
        )

    with col2:
        deep_work = st.checkbox(
            "Längere Fokus-Blöcke für schwierige Themen (Deep Work)",
            value=st.session_state.preferences.get("deep_work", True),
            help="Plane längere, ungestörte Lernblöcke für anspruchsvolle Module, Projekte oder rechenintensive Aufgaben. Empfohlen für Programmierung, Mathe, Projektarbeiten usw.",
        )

        short_sessions = st.checkbox(
            "Kürzere Einheiten für theorielastige Fächer",
            value=st.session_state.preferences.get("short_sessions", False),
            help="Teilt lernintensive Theorie-Fächer in kürzere, besser verdauliche Einheiten (z.B. 30–45 Minuten) auf. Hilft, Überforderung zu vermeiden und konzentriert zu bleiben.",
        )

    # Update learning preferences in session state
    st.session_state.preferences.update(
        {
            "spacing": spacing,
            "interleaving": interleaving,
            "deep_work": deep_work,
            "short_sessions": short_sessions,
        }
    )

    st.markdown("---")

    # Time-of-day preferences
    st.markdown("**Wann lernst du am liebsten?**")
    st.markdown(
        "Diese Angabe ist eine Präferenz. Die KI versucht, deinen Lernplan eher in diesen Zeiten zu platzieren, kann aber bei Bedarf davon abweichen."
    )

    col_tod1, col_tod2, col_tod3 = st.columns(3)

    current_preferred_times = st.session_state.preferences.get(
        "preferred_times_of_day", []
    )

    with col_tod1:
        prefer_morning = st.checkbox(
            "Morgens (ca. 06:00–11:00)",
            value="morning" in current_preferred_times,
            help="Du bevorzugst es, morgens zu lernen",
        )

    with col_tod2:
        prefer_afternoon = st.checkbox(
            "Nachmittags (ca. 12:00–17:00)",
            value="afternoon" in current_preferred_times,
            help="Du bevorzugst es, nachmittags zu lernen",
        )

    with col_tod3:
        prefer_evening = st.checkbox(
            "Abends (ca. 18:00–22:00)",
            value="evening" in current_preferred_times,
            help="Du bevorzugst es, abends zu lernen",
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
        st.markdown(
            """
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
        """
        )

        st.info(
            "💡 **Empfehlung für den Start:** Wenn du unsicher bist, aktiviere **Wiederholen mit Abständen** + **Längere Fokus-Blöcke für schwierige Themen**. Du kannst die Einstellungen später jederzeit auf der Lernplan-Seite ändern."
        )

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
            duration_days = (
                st.session_state.study_end - st.session_state.study_start
            ).days
            st.metric("Lernplan-Dauer", f"{duration_days} Tage")
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
        st.metric(
            "Min. Einheit (Min.)",
            st.session_state.preferences.get("min_session_duration", 60),
        )

    # Detailed Leistungsnachweise list
    if num_leistungsnachweise > 0:
        with st.expander("📚 Details zu deinen Leistungsnachweisen"):
            for ln in st.session_state.leistungsnachweise:
                deadline_str = (
                    f" - Fällig: {ln['deadline'].strftime('%d.%m.%Y')}"
                    if ln.get("deadline")
                    else ""
                )
                module_str = f" [{ln['module']}]" if ln.get("module") else ""
                topics_count = len(ln["topics"]) if ln["topics"] else 0
                
                # Format type display (remove LeistungsnachweisType prefix if present)
                type_display = ln['type']
                if '.' in type_display:
                    type_display = type_display.split('.')[-1]
                
                # Convert to readable format
                type_names = {
                    'PRUEFUNG': 'Prüfung',
                    'HAUSARBEIT': 'Hausarbeit',
                    'PROJEKTARBEIT': 'Projektarbeit',
                    'PRAESENTATION': 'Präsentation',
                    'SEMINARARBEIT': 'Seminararbeit',
                    'ANDERE': 'Andere'
                }
                type_display = type_names.get(type_display, type_display)
                
                st.write(
                    f"• **{ln['title']}** ({type_display}){module_str} (Priorität {ln['priority']}/5, Aufwand {ln['effort']}/5{deadline_str}) - {topics_count} Themen"
                )

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
    st.info(
        """
    **💡 So funktioniert's:**

    Der KI-Planer nutzt:
    - Deine **belegten Zeiten**, um Lerneinheiten nicht während Arbeit/Vorlesungen zu planen
    - Deine **Abwesenheiten**, um diese Zeiträume komplett zu überspringen
    - Deine **Ruhetage**, damit du Zeit zum Erholen hast
    - Deine **Lern-Limits**, um einen nachhaltigen, ausgewogenen Zeitplan zu erstellen
    - Deine **Lernpräferenzen**, um die Lernstrategie zu optimieren

    All diese Informationen werden kombiniert, um optimale freie Zeitfenster zu berechnen, wenn du deinen Plan generierst.
    """
    )

    st.markdown("---")

    # ========== NEXT STEPS ==========

    # Check if minimum requirements are met
    setup_complete = (
        num_leistungsnachweise > 0
        and has_api_key
        and st.session_state.study_end is not None
    )

    if setup_complete:
        st.success(
            """
        **✅ Einrichtung abgeschlossen!**

        Du hast alle notwendigen Informationen konfiguriert. Du bist bereit, deinen KI-gestützten Lernplan zu generieren!
        """
        )

        st.info(
            "👉 **Nächster Schritt:** Wechsle zur **'Lernplan'**-Seite im Navigations-Menü, um deinen KI-basierten Lernplan zu generieren."
        )
    else:
        st.warning(
            """
        **⚠️ Einrichtung unvollständig**

        Bitte vervollständige Folgendes, bevor du den Plan generierst:
        """
        )

        if num_leistungsnachweise == 0:
            st.write("• Füge mindestens einen Leistungsnachweis hinzu")
        if not has_api_key:
            st.write(
                "• Gib deinen API-Schlüssel ein (OpenAI oder Gemini in der Sidebar wählbar)"
            )
        if st.session_state.study_end is None:
            st.write(
                "• Füge mindestens einen Leistungsnachweis mit Fälligkeitsdatum hinzu"
            )
