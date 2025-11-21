"""
Test-Daten für einen realistischen BWL-Studenten

Profil: Max, 22 Jahre, BWL-Student im 5. Semester
- Arbeitet Montag & Dienstag (09:00-17:00) im Teilzeit-Job
- Fussballtraining: Montag & Mittwoch Abend (18:30-20:30)
- Vorlesungen: Mittwoch, Donnerstag, Freitag Vormittag
- Wochenende: Samstag teilweise frei, Sonntag Ruhetag
- Weihnachtsferien: 20.12.2025 - 05.01.2026
"""

from datetime import date, time, timedelta


def get_test_data():
    """
    Gibt vollständige Testdaten für einen busy BWL-Studenten zurück.
    
    Returns:
        dict: Dictionary mit allen Session-State Daten
    """
    
    # Semester-Zeitraum
    study_start = date(2025, 11, 15)
    study_end = date(2026, 2, 14)  # Ende basierend auf letzter Prüfung
    
    # ==========================================
    # LEISTUNGSNACHWEISE (5 Prüfungen/Arbeiten)
    # ==========================================
    leistungsnachweise = [
        {
            "title": "Marketing Grundlagen",
            "type": "Prüfung",
            "deadline": date(2025, 12, 18),
            "module": "Marketing",
            "topics": [
                "4Ps (Product, Price, Place, Promotion)",
                "Marktforschung und Zielgruppenanalyse",
                "Produktlebenszyklus",
                "Marketingstrategien"
            ],
            "priority": 5,  # Sehr wichtig
            "effort": 4     # Hoher Aufwand
        },
        {
            "title": "Rechnungswesen Prüfung",
            "type": "Prüfung", 
            "deadline": date(2026, 1, 22),
            "module": "Rechnungswesen",
            "topics": [
                "Bilanzierung",
                "GuV (Gewinn- und Verlustrechnung)",
                "Kostenrechnung",
                "Buchungssätze erstellen"
            ],
            "priority": 5,
            "effort": 5  # Sehr hoher Aufwand (Mathefach!)
        },
        {
            "title": "Unternehmensführung Präsentation",
            "type": "Präsentation",
            "deadline": date(2025, 11, 28),
            "module": "Unternehmensführung",
            "topics": [
                "Führungsstile und Motivation",
                "Organisationsstrukturen",
                "Change Management"
            ],
            "priority": 4,
            "effort": 3
        },
        {
            "title": "VWL Hausarbeit",
            "type": "Hausarbeit",
            "deadline": date(2026, 1, 8),
            "module": "Volkswirtschaftslehre",
            "topics": [
                "Angebot und Nachfrage",
                "Marktformen (Monopol, Oligopol)",
                "Wirtschaftspolitische Instrumente"
            ],
            "priority": 3,
            "effort": 4
        },
        {
            "title": "Statistik Projektarbeit",
            "type": "Projektarbeit",
            "deadline": date(2026, 2, 14),
            "module": "Statistik",
            "topics": [
                "Deskriptive Statistik",
                "Hypothesentests",
                "Regression und Korrelation",
                "SPSS Auswertung"
            ],
            "priority": 4,
            "effort": 5
        }
    ]
    
    # ==========================================
    # BELEGTE ZEITEN (Arbeit, Vorlesungen, Fussball)
    # ==========================================
    # Format: Wiederkehrende wöchentliche Termine
    busy_times = [
        {
            'label': 'Arbeit (Teilzeit-Job)',
            'days': ['Monday', 'Tuesday'],
            'start': '09:00',
            'end': '17:00'
        },
        {
            'label': 'Fussballtraining',
            'days': ['Monday', 'Wednesday'],
            'start': '18:30',
            'end': '20:30'
        },
        {
            'label': 'Vorlesungen (Marketing, VWL)',
            'days': ['Wednesday'],
            'start': '08:00',
            'end': '12:00'
        },
        {
            'label': 'Vorlesungen (Rechnungswesen, Statistik)',
            'days': ['Thursday'],
            'start': '08:00',
            'end': '13:00'
        },
        {
            'label': 'Vorlesung (Unternehmensführung)',
            'days': ['Friday'],
            'start': '09:00',
            'end': '12:00'
        },
        {
            'label': 'Freunde treffen / Sport',
            'days': ['Saturday'],
            'start': '10:00',
            'end': '13:00'
        }
    ]
    
    # ==========================================
    # FERIEN & ABWESENHEITEN
    # ==========================================
    absences = [
        {
            'label': 'Weihnachtsferien',
            'start_date': date(2025, 12, 20),
            'end_date': date(2026, 1, 5),
            'description': 'Zuhause bei Familie'
        },
        {
            'label': 'Kurztrip Berlin',
            'start_date': date(2025, 10, 20),
            'end_date': date(2025, 10, 22),
            'description': 'Städtetrip mit Freunden'
        }
    ]
    
    # ==========================================
    # PRÄFERENZEN
    # ==========================================
    preferences = {
        'spacing': True,           # Spaced Repetition - Ja!
        'interleaving': True,      # Fächer mischen - Ja!
        'deep_work': True,         # Längere Deep-Work Sessions
        'short_sessions': False,   # Keine kurzen Sessions bevorzugt
        'rest_days': ['Sonntag'],  # Sonntag = Ruhetag (DEUTSCH!)
        'max_hours_day': 5,        # Max 5h Lernen pro Tag (ist schon busy!)
        'max_hours_week': 25,      # Max 25h pro Woche
        'min_session_duration': 90,  # Mindestens 90 Min Sessions
        'earliest_study_time': '08:00',
        'latest_study_time': '22:00',
        'preferred_times_of_day': ['afternoon', 'evening']  # Nachmittag/Abend bevorzugt
    }
    
    # ==========================================
    # KOMPLETTER SESSION STATE
    # ==========================================
    return {
        'study_start': study_start,
        'study_end': study_end,
        'leistungsnachweise': leistungsnachweise,
        'busy_times': busy_times,
        'absences': absences,
        'preferences': preferences,
        # UI State
        'current_page': 'setup',
        'plan_generated': False,
        'study_plan': None
    }


def load_test_data_into_session_state(st):
    """
    Lädt Test-Daten direkt in den Streamlit Session State.
    
    Args:
        st: Streamlit module
    """
    test_data = get_test_data()
    
    # Alle Daten in Session State laden
    for key, value in test_data.items():
        st.session_state[key] = value
    
    # Success Message
    st.success("""
    ✅ **Test-Daten geladen!**
    
    **Profil: Max, 22 Jahre, BWL-Student**
    - 🏢 Arbeit: Montag & Dienstag (09:00-17:00)
    - ⚽ Fussball: Montag & Mittwoch Abend
    - 📚 Vorlesungen: Mittwoch, Donnerstag, Freitag
    - 🏖️ Ferien: Weihnachten (20.12. - 05.01.)
    - 📝 5 Prüfungen/Arbeiten im Semester
    """)
    
    st.info("💡 Gehe jetzt zu **'Plan erstellen'** um den Lernplan zu generieren!")
