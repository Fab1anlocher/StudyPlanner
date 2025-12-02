"""
Export Page - Export des Lernplans
Ermöglicht den Download des Lernplans in verschiedenen Formaten
"""

import streamlit as st
from datetime import datetime

# Import export service
from services import (
    create_pdf_export,
    create_excel_export,
    get_plan_statistics,
)


def show_export_page():
    """
    Zeigt die Export-Seite an mit verschiedenen Export-Formaten.

    Unterstützte Formate:
    - Excel (.xlsx): Editierbare Arbeitsmappe mit 5 Sheets (PRIMÄR)
    - PDF: Druckbares Dokument mit Kalender und Session-Liste

    Excel-Export enthält:
    - Sheet 1: Lernplan (alle Sessions mit Datum, Zeit, Modul, Thema, etc.)
    - Sheet 2: Leistungsnachweise (alle Prüfungen/Abgaben mit Details)
    - Sheet 3: Abwesenheiten (Urlaub, Events, etc.)
    - Sheet 4: Verpflichtungen (regelmäßige busy times)
    - Sheet 5: Übersicht (Statistiken und Metadaten)

    Zeigt außerdem Plan-Statistiken:
    - Gesamt-Sessions
    - Gesamte Lernstunden
    - Anzahl Module
    - Lerntage

    Verwendet:
        - services.export_service für alle Export-Funktionen
        - services.export_service.get_plan_statistics für Statistiken
    """
    st.header("📄 Export")
    st.markdown(
        "Lade deinen personalisierten Lernplan in verschiedenen Formaten herunter."
    )

    st.markdown("---")

    # Check if plan exists
    if "plan" not in st.session_state or not st.session_state.plan:
        st.warning(
            """
        ⚠️ **Kein Lernplan vorhanden**

        Bitte generiere zuerst einen Lernplan:
        1. Vervollständige die **Einrichtung**-Seite
        2. Gehe zur **Lernplan**-Seite
        3. Klicke auf "KI-Plan generieren"

        Sobald du einen Plan hast, kannst du ihn hier exportieren.
        """
        )
        return

    plan = st.session_state.plan

    # Plan summary using statistics helper
    st.subheader("📊 Plan-Übersicht")

    stats = get_plan_statistics(plan)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Einheiten gesamt", stats["total_sessions"])

    with col2:
        st.metric("Module", stats["unique_modules"])

    with col3:
        st.metric("Stunden gesamt", f"{stats['total_hours']:.1f}h")

    with col4:
        st.metric("Lerntage", stats["unique_dates"])

    st.markdown("---")

    # Sort plan chronologically for export
    sorted_plan = sorted(plan, key=lambda x: (x.get("date", ""), x.get("start", "")))

    # Export options
    st.subheader("💾 Export-Optionen")

    # Excel Export (NEW - Editable Format)
    st.markdown("### 📊 Excel-Export (Editierbar)")
    st.markdown(
        """
    Exportiere deinen Lernplan als **Excel-Datei (.xlsx)** zur Weiterbearbeitung:
    - ✏️ **Editierbar:** Passe Zeiten, Themen und Beschreibungen direkt in Excel an
    - 📋 **5 Arbeitsblätter:** Lernplan, Leistungsnachweise, Abwesenheiten, Verpflichtungen, Übersicht
    - 📊 **Formatiert:** Professionelle Formatierung mit Farben und Rahmen
    - 🔢 **Berechnungen:** Automatische Dauer-Berechnung pro Session
    """
    )

    try:
        # Generate Excel
        study_start = st.session_state.study_start
        study_end = st.session_state.study_end
        excel_bytes = create_excel_export(
            plan=sorted_plan,
            leistungsnachweise=st.session_state.get("leistungsnachweise", []),
            preferences=st.session_state.get("preferences", {}),
            study_start=study_start,
            study_end=study_end,
            busy_times=st.session_state.get("busy_times", []),
            absences=st.session_state.get("absences", []),
        )

        # Download button
        col1, col2 = st.columns([2, 1])

        with col1:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label="📥 Lernplan als Excel herunterladen",
                data=excel_bytes,
                file_name=f"lernplan_{timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="secondary",
                use_container_width=True,
            )

        with col2:
            excel_size_kb = len(excel_bytes) / 1024
            st.metric("Dateigrösse", f"{excel_size_kb:.1f} KB")

        st.success("✅ Excel bereit zum Download!")

    except Exception as e:
        st.error(f"❌ Fehler beim Excel-Generieren: {str(e)}")

    st.markdown("---")

    # PDF Export
    st.markdown("### 📑 PDF-Export (Druckversion)")
    st.markdown(
        "Lade deinen vollständigen Lernplan als professionell formatiertes PDF-Dokument herunter."
    )

    try:
        # Generate PDF using export service
        study_start = st.session_state.study_start
        study_end = st.session_state.study_end
        pdf_bytes = create_pdf_export(
            sorted_plan, 
            study_start, 
            study_end,
            busy_times=st.session_state.get("busy_times", []),
            absences=st.session_state.get("absences", []),
            preferences=st.session_state.get("preferences", {}),
        )

        # Download button
        col1, col2 = st.columns([2, 1])

        with col1:
            st.download_button(
                label="📥 Lernplan als PDF herunterladen",
                data=pdf_bytes,
                file_name="lernplan.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )

        with col2:
            pdf_size_kb = len(pdf_bytes) / 1024
            st.metric("Dateigrösse", f"{pdf_size_kb:.1f} KB")

        st.success("✅ PDF bereit zum Download!")

    except Exception as e:
        st.error(f"❌ Fehler beim PDF-Generieren: {str(e)}")
        st.info(
            "Bitte versuche, deinen Plan neu zu generieren oder kontaktiere den Support, falls das Problem weiterhin besteht."
        )
