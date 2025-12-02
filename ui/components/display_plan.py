"""
display_plan.py
---------------
Functions for displaying study plans in various formats.
Handles all Streamlit UI rendering for study plans.
"""

import streamlit as st
from datetime import datetime, timedelta

from constants import WEEKDAY_EN_CAPITALIZED_TO_DE, DATE_FORMAT_DISPLAY


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
            date_str = session_date.strftime("%d.%m.%Y")
        except:
            date_str = session.get("date", "Unknown")

        table_data.append(
            {
                "Datum": date_str,
                "Zeit": f"{session.get('start', 'N/A')} - {session.get('end', 'N/A')}",
                "Thema": session.get("topic", "N/A"),
                "Beschreibung": session.get("description", "N/A"),
            }
        )

    st.dataframe(table_data, use_container_width=True, hide_index=True)


def display_plan_views(plan):
    """
    Display the study plan in multiple view formats.

    Args:
        plan (list): List of study session dicts
    """

    if not plan:
        st.info(
            "📭 Noch kein Lernplan vorhanden. Generiere einen Plan mit dem Button oben."
        )
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
    Shows weeks with navigation (prev/next) for better usability.
    Also displays busy times and absences to show the complete daily schedule.

    Args:
        sorted_plan (list): Sorted list of study session dicts
    """

    if not sorted_plan:
        st.info("Keine Lerneinheiten geplant.")
        return

    # Get semester date range from session state
    semester_start = st.session_state.study_start
    semester_end = st.session_state.study_end

    # Ensure they are date objects
    if isinstance(semester_start, datetime):
        semester_start = semester_start.date()
    if isinstance(semester_end, datetime):
        semester_end = semester_end.date()

    # Get busy times and absences from session state
    busy_times = st.session_state.get("busy_times", [])
    absences = st.session_state.get("absences", [])

    # Pre-compute busy times grouped by weekday index (0=Monday, 6=Sunday)
    # Now including validity period for filtering per-date
    # Note: busy times use German weekday names from the UI
    weekday_names_de = [
        "montag", "dienstag", "mittwoch", "donnerstag",
        "freitag", "samstag", "sonntag"
    ]
    busy_times_by_weekday = {i: [] for i in range(7)}
    for busy in busy_times:
        busy_days_lower = {d.lower() for d in busy.get("days", [])}
        for day_idx, weekday_name in enumerate(weekday_names_de):
            if weekday_name in busy_days_lower:
                busy_times_by_weekday[day_idx].append({
                    "label": busy.get("label", "Belegt"),
                    "start": busy.get("start", ""),
                    "end": busy.get("end", ""),
                    "valid_from": busy.get("valid_from"),
                    "valid_until": busy.get("valid_until"),
                })

    # Pre-compute exams/deadlines by date for O(1) lookup
    leistungsnachweise = st.session_state.get("leistungsnachweise", [])
    exams_by_date = {}
    for ln in leistungsnachweise:
        deadline = ln.get("deadline")
        if deadline:
            if deadline not in exams_by_date:
                exams_by_date[deadline] = []
            exams_by_date[deadline].append({
                "title": ln.get("title", "Prüfung"),
                "type": ln.get("type", "Prüfung"),
            })

    # Initialize all weeks in the semester
    weeks = {}
    current_date = semester_start

    while current_date <= semester_end:
        iso_year, iso_week, _ = current_date.isocalendar()
        week_key = f"{iso_year}-W{iso_week:02d}"

        if week_key not in weeks:
            # Find Monday of this week
            week_start = current_date - timedelta(days=current_date.weekday())
            week_end = week_start + timedelta(days=6)

            weeks[week_key] = {
                "week_number": iso_week,
                "start": week_start,
                "end": week_end,
                "sessions": [],
            }

        # Move to next week
        current_date += timedelta(days=7 - current_date.weekday())

    # Now add sessions to the appropriate weeks
    for session in sorted_plan:
        try:
            session_date = datetime.fromisoformat(session.get("date", "")).date()
            iso_year, iso_week, _ = session_date.isocalendar()
            week_key = f"{iso_year}-W{iso_week:02d}"

            if week_key in weeks:
                weeks[week_key]["sessions"].append(session)
        except:
            continue

    if not weeks:
        st.info("Keine gültigen Einheiten zum Anzeigen.")
        return

    # Sort weeks chronologically
    sorted_weeks = sorted(weeks.items(), key=lambda x: x[1]["start"])
    total_weeks = len(sorted_weeks)

    # German weekday abbreviations
    day_names_short = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

    # Week navigation state
    if "current_week_index" not in st.session_state:
        st.session_state.current_week_index = 0
    
    # Ensure index is within bounds
    if st.session_state.current_week_index >= total_weeks:
        st.session_state.current_week_index = total_weeks - 1
    if st.session_state.current_week_index < 0:
        st.session_state.current_week_index = 0

    # Navigation controls
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns([1, 1, 2, 1, 1])
    
    with nav_col1:
        if st.button("⏮️ Erste", key="first_week", use_container_width=True, disabled=st.session_state.current_week_index == 0):
            st.session_state.current_week_index = 0
            st.rerun()
    
    with nav_col2:
        if st.button("◀️ Zurück", key="prev_week", use_container_width=True, disabled=st.session_state.current_week_index == 0):
            st.session_state.current_week_index -= 1
            st.rerun()
    
    with nav_col3:
        current_week = st.session_state.current_week_index + 1
        st.markdown(f"<div style='text-align: center; padding: 8px;'><strong>Woche {current_week} von {total_weeks}</strong></div>", unsafe_allow_html=True)
    
    with nav_col4:
        if st.button("Weiter ▶️", key="next_week", use_container_width=True, disabled=st.session_state.current_week_index >= total_weeks - 1):
            st.session_state.current_week_index += 1
            st.rerun()
    
    with nav_col5:
        if st.button("Letzte ⏭️", key="last_week", use_container_width=True, disabled=st.session_state.current_week_index >= total_weeks - 1):
            st.session_state.current_week_index = total_weeks - 1
            st.rerun()

    st.markdown("---")

    # Display current week
    week_key, week_data = sorted_weeks[st.session_state.current_week_index]
    week_start = week_data["start"]
    week_end = week_data["end"]
    week_num = week_data["week_number"]

    st.markdown(
        f"### 📅 Woche {week_num} ({week_start.strftime('%d.%m.')} - {week_end.strftime('%d.%m.%Y')})"
    )

    # Group sessions by weekday
    days_sessions = {i: [] for i in range(7)}  # 0=Monday, 6=Sunday

    for session in week_data["sessions"]:
        try:
            session_date = datetime.fromisoformat(session.get("date", "")).date()
            weekday = session_date.weekday()
            days_sessions[weekday].append(session)
        except:
            continue

    # Check for absences for each day in this week
    days_absences = {i: [] for i in range(7)}
    for day_idx in range(7):
        day_date = week_start + timedelta(days=day_idx)
        for absence in absences:
            absence_start = absence.get("start_date")
            absence_end = absence.get("end_date")
            if absence_start and absence_end:
                if absence_start <= day_date <= absence_end:
                    days_absences[day_idx].append(
                        absence.get("label", "Abwesenheit")
                    )

    # Filter busy times by validity period for each day
    # We need to check if the busy time is valid for the specific date
    days_busy = {i: [] for i in range(7)}
    for day_idx in range(7):
        day_date = week_start + timedelta(days=day_idx)
        for busy_item in busy_times_by_weekday[day_idx]:
            valid_from = busy_item.get("valid_from")
            valid_until = busy_item.get("valid_until")
            
            # Check if this busy time is valid for the current date
            if valid_from is not None and day_date < valid_from:
                # Busy time hasn't started yet
                continue
            if valid_until is not None and day_date > valid_until:
                # Busy time has ended (e.g., lectures ended mid-December)
                continue
            
            # Busy time is valid for this date
            days_busy[day_idx].append(busy_item)

    # Check for exams/deadlines on each day using pre-computed lookup (O(1) per day)
    days_exams = {i: [] for i in range(7)}
    for day_idx in range(7):
        day_date = week_start + timedelta(days=day_idx)
        if day_date in exams_by_date:
            # Use list copy to avoid modifying original data
            days_exams[day_idx] = list(exams_by_date[day_date])

    # Sort sessions within each day by start time
    for day_idx in range(7):
        days_sessions[day_idx] = sorted(
            days_sessions[day_idx], key=lambda x: x.get("start", "")
        )

    # Create 7 columns for days of the week
    cols = st.columns(7)

    for day_idx, col in enumerate(cols):
        with col:
            # Calculate the actual date for this day
            day_date = week_start + timedelta(days=day_idx)
            st.markdown(f"**{day_names_short[day_idx]}**")
            st.caption(day_date.strftime("%d.%m."))

            sessions_today = days_sessions[day_idx]
            absences_today = days_absences[day_idx]
            busy_today = days_busy[day_idx]
            exams_today = days_exams[day_idx]

            # Check if day is completely absent (vacation, etc.)
            if absences_today:
                for absence_label in absences_today:
                    st.markdown(
                        f"""
                    <div style="background-color: #ffe6e6; padding: 8px; border-radius: 4px; margin-bottom: 8px; border-left: 3px solid #cc0000;">
                        <div style="font-size: 0.75em; font-weight: bold; color: #cc0000;">🚫 Ganzer Tag</div>
                        <div style="font-size: 0.8em; margin-top: 4px; font-weight: 600;">{absence_label}</div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

            # Show busy times (job, lectures, etc.) - only valid ones for this date
            if busy_today:
                for busy_item in busy_today:
                    start = busy_item.get("start", "N/A")
                    end = busy_item.get("end", "N/A")
                    label = busy_item.get("label", "Belegt")
                    label_display = label[:20] + "..." if len(label) > 20 else label

                    st.markdown(
                        f"""
                    <div style="background-color: #fff3e6; padding: 8px; border-radius: 4px; margin-bottom: 8px; border-left: 3px solid #ff9900;">
                        <div style="font-size: 0.75em; font-weight: bold; color: #ff9900;">⛔ {start}-{end}</div>
                        <div style="font-size: 0.8em; margin-top: 4px; font-weight: 600; color: #663300;">{label_display}</div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

            # Show exams/deadlines (IMPORTANT - show first!)
            if exams_today:
                for exam in exams_today:
                    title = exam.get("title", "Prüfung")
                    exam_type_raw = exam.get("type", "Prüfung")
                    # Convert enum to string if needed
                    exam_type = (
                        exam_type_raw.value
                        if hasattr(exam_type_raw, "value")
                        else exam_type_raw
                    )
                    title_display = title[:18] + "..." if len(title) > 18 else title

                    st.markdown(
                        f"""
                    <div style="background-color: #ffe6f0; padding: 10px; border-radius: 4px; margin-bottom: 8px; border-left: 4px solid #cc0066; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <div style="font-size: 0.75em; font-weight: bold; color: #cc0066;">🎯 {exam_type}</div>
                        <div style="font-size: 0.85em; margin-top: 4px; font-weight: 700; color: #990050;">{title_display}</div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

            # Show learning sessions
            if sessions_today:
                for session in sessions_today:
                    # Create a compact card for each session
                    start = session.get("start", "N/A")
                    end = session.get("end", "N/A")
                    module = session.get("module", "Unknown")
                    topic = session.get("topic", "N/A")

                    # Truncate long titles for display
                    module_display = (
                        module[:20] + "..." if len(module) > 20 else module
                    )
                    topic_display = topic[:25] + "..." if len(topic) > 25 else topic

                    # Use a container with custom styling
                    st.markdown(
                        f"""
                    <div style="background-color: #e6f3ff; padding: 8px; border-radius: 4px; margin-bottom: 8px; border-left: 3px solid #0066cc;">
                        <div style="font-size: 0.75em; font-weight: bold; color: #0066cc;">📖 {start}-{end}</div>
                        <div style="font-size: 0.8em; margin-top: 4px; font-weight: 600; color: #003366;">{module_display}</div>
                        <div style="font-size: 0.7em; color: #666; margin-top: 2px;">{topic_display}</div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

            # Show message if completely empty day
            if (
                not sessions_today
                and not busy_today
                and not absences_today
                and not exams_today
            ):
                st.markdown(
                    "<div style='color: #999; font-size: 0.75em; font-style: italic; padding: 4px;'>Frei</div>",
                    unsafe_allow_html=True,
                )


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
            # Get English weekday name and translate to German
            weekday_en = session_date.strftime("%A")
            weekday_de = WEEKDAY_EN_CAPITALIZED_TO_DE.get(weekday_en, weekday_en)
            date_display = f"{weekday_de}, {session_date.strftime(DATE_FORMAT_DISPLAY)}"
        except:
            date_display = date_str

        st.markdown(f"### 📅 {date_display}")

        sessions = sessions_by_date[date_str]

        # Sort sessions by start time
        sessions = sorted(sessions, key=lambda x: x.get("start", ""))

        for session in sessions:
            start = session.get("start", "N/A")
            end = session.get("end", "N/A")
            module = session.get("module", "Unknown")
            topic = session.get("topic", "N/A")
            description = session.get("description", "")

            # Create formatted session entry
            col1, col2 = st.columns([1, 4])

            with col1:
                st.markdown(f"**{start} - {end}**")

            with col2:
                st.markdown(f"**{module}**")
                st.markdown(f"📖 {topic}")
                if description:
                    st.caption(f"📝 {description}")

        st.markdown("---")
