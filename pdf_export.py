"""
pdf_export.py
-------------
Functions for exporting study plans to PDF format.
"""

import streamlit as st
from datetime import datetime
from fpdf import FPDF


# Weekday translation mapping (English → German)
WEEKDAY_MAP_DE = {
    "Monday": "Montag",
    "Tuesday": "Dienstag",
    "Wednesday": "Mittwoch",
    "Thursday": "Donnerstag",
    "Friday": "Freitag",
    "Saturday": "Samstag",
    "Sunday": "Sonntag"
}


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
    pdf.cell(0, 10, "Personalisierter Lernplan", ln=True, align="C")
    pdf.ln(5)
    
    # Study plan dates
    pdf.set_font("Helvetica", "", 12)
    study_start = st.session_state.study_start.strftime("%d. %B %Y")
    study_end = st.session_state.study_end.strftime("%d. %B %Y") if st.session_state.study_end else "N/A"
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
        # Parse and format date with German weekday
        try:
            session_date = datetime.fromisoformat(date_str).date()
            weekday_en = session_date.strftime("%A")
            weekday_de = WEEKDAY_MAP_DE.get(weekday_en, weekday_en)
            date_display = f"{weekday_de}, {session_date.strftime('%d. %B %Y')}"
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
            pdf.cell(35, 6, f"{start} - {end}", ln=False)
            
            # Module
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 6, module, ln=True)
            
            # Topic (indented)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_x(45)
            pdf.cell(0, 5, f"Thema: {topic}", ln=True)
            
            # Description (indented, smaller font)
            if description:
                pdf.set_font("Helvetica", "", 9)
                pdf.set_x(45)
                pdf.multi_cell(0, 5, description)
            
            pdf.ln(2)
        
        pdf.ln(5)
    
    # Footer with generation info
    pdf.set_y(-30)
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 5, f"Generated on {datetime.now().strftime('%d %B %Y at %H:%M')}", ln=True, align="C")
    pdf.cell(0, 5, "Created with AI Study Planner", ln=True, align="C")
    
    # Return PDF as bytes
    return bytes(pdf.output())
