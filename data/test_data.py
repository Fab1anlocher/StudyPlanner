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

from constants import LeistungsnachweisType, ExamFormat, DEFAULT_PREFERENCES


def get_test_data():
    """
    Gibt vollständige Testdaten für einen busy BWL-Studenten zurück.

    Returns:
        dict: Dictionary mit allen Session-State Daten
    """

    # Semester-Zeitraum
    study_start = date(2025, 12, 2)
    study_end = date(2026, 1, 14)  # Ende basierend auf letzter Prüfung

    # ==========================================
    # LEISTUNGSNACHWEISE (5 Prüfungen/Arbeiten)
    # ==========================================
    leistungsnachweise = [
        {
            "title": "Marketing Grundlagen",
            "type": LeistungsnachweisType.PRUEFUNG,
            "deadline": date(2025, 12, 18),
            "module": "Marketing",
            "topics": [
                "Kapitel 1: Einführung in Marketing - Definition, Konzepte und Marketing-Mix",
                "Kapitel 2: 4Ps (Product, Price, Place, Promotion) - Detaillierte Strategien",
                "Kapitel 3: Marktforschung - Primär- und Sekundärforschung, Befragungsmethoden",
                "Kapitel 4: Zielgruppenanalyse - Segmentierung, Targeting, Positioning (STP)",
                "Kapitel 5: Produktlebenszyklus - Einführung, Wachstum, Reife, Sättigung",
                "Kapitel 6: Marketingstrategien - Push vs. Pull, Online vs. Offline Marketing",
                "Kapitel 7: Markenmanagement - Brand Equity, Markenpositionierung",
                "Kapitel 8: Kundenverhalten - Kaufentscheidungsprozess, Einflussfaktoren",
                "Kapitel 9: Werbung und Kommunikation - AIDA-Modell, Mediaplanung",
                "Übungsaufgaben und Fallstudien - Praxisbeispiele aus der Schweiz und International",
            ],
            "priority": 5,  # Sehr wichtig
            "effort": 4,  # Hoher Aufwand
            "exam_format": ExamFormat.MULTIPLE_CHOICE,
            "exam_details": "60 Minuten, 40 Fragen, Closed Book. Fokus: Definitionen, Konzepte und Modelle auswendig können.",
        },
        {
            "title": "Rechnungswesen Prüfung",
            "type": LeistungsnachweisType.PRUEFUNG,
            "deadline": date(2026, 1, 22),
            "module": "Rechnungswesen",
            "topics": [
                "Teil 1: Grundlagen der Buchhaltung - Doppelte Buchführung, Kontenrahmen",
                "Teil 2: Bilanzierung - Aktiva, Passiva, Bilanzstruktur nach OR",
                "Teil 3: GuV (Gewinn- und Verlustrechnung) - Aufwand, Ertrag, Betriebsergebnis",
                "Teil 4: Buchungssätze erstellen - T-Konten, Hauptbuch, Journal",
                "Teil 5: Kostenrechnung - Fixkosten, variable Kosten, Deckungsbeitrag",
                "Teil 6: Kalkulation - Zuschlagskalkulation, Divisionskalkulation",
                "Teil 7: Abschreibungen - Lineare, degressive Abschreibung, Buchwert",
                "Teil 8: Jahresabschluss - Inventur, Rechnungsabgrenzung, Rückstellungen",
                "Teil 9: Kennzahlenanalyse - Liquidität, Rentabilität, Cash-Flow",
                "Teil 10: Übungsklausuren - Musterlösungen durcharbeiten, typische Fehler vermeiden",
            ],
            "priority": 5,
            "effort": 5,  # Sehr hoher Aufwand (Mathefach!)
            "exam_format": ExamFormat.RECHENAUFGABEN,
            "exam_details": "120 Minuten, 6 komplexe Aufgaben, Taschenrechner erlaubt, Formelsammlung (1 A4 Blatt). Fokus: Übungsaufgaben rechnen, Lösungswege verstehen.",
        },
        {
            "title": "Unternehmensführung Präsentation",
            "type": LeistungsnachweisType.PRAESENTATION,
            "deadline": date(2025, 12, 28),
            "module": "Unternehmensführung",
            "topics": [
                "Thema 1: Führungsstile - Autoritär, demokratisch, Laissez-faire, situativ",
                "Thema 2: Motivation - Maslow, Herzberg, Erwartungstheorie, Anreizsysteme",
                "Thema 3: Organisationsstrukturen - Funktional, divisional, Matrix, Netzwerk",
                "Thema 4: Change Management - Phasenmodelle (Lewin, Kotter), Widerstände überwinden",
                "Thema 5: Strategisches Management - SWOT, Porter's Five Forces, Wettbewerbsstrategien",
                "Thema 6: Unternehmenskultur - Werte, Normen, Symbole, kulturelle Transformation",
                "Präsentationsvorbereitung - PowerPoint erstellen, Handout, Zeitmanagement (15 Min)",
                "Praxisbeispiel recherchieren - Schweizer KMU oder internationale Konzerne analysieren",
            ],
            "priority": 4,
            "effort": 3,
        },
        {
            "title": "VWL Hausarbeit",
            "type": LeistungsnachweisType.HAUSARBEIT,
            "deadline": date(2026, 1, 8),
            "module": "Volkswirtschaftslehre",
            "topics": [
                "Einleitung: Fragestellung und Relevanz - Literaturrecherche, Problemstellung",
                "Hauptteil 1: Angebot und Nachfrage - Preismechanismus, Elastizität, Marktgleichgewicht",
                "Hauptteil 2: Marktformen - Monopol, Oligopol, vollständige Konkurrenz",
                "Hauptteil 3: Marktversagen - Externe Effekte, öffentliche Güter, asymmetrische Information",
                "Hauptteil 4: Wirtschaftspolitische Instrumente - Fiskal-, Geld-, Strukturpolitik",
                "Hauptteil 5: Konjunkturzyklen - BIP, Inflation, Arbeitslosigkeit, Stabilitätsgesetz",
                "Hauptteil 6: Internationale Wirtschaft - Aussenhandel, Wechselkurse, Globalisierung",
                "Schluss: Zusammenfassung und Fazit - Erkenntnisse, Empfehlungen",
                "Formales: Zitierweise (APA/Harvard), Literaturverzeichnis, Formatierung (15 Seiten)",
            ],
            "priority": 3,
            "effort": 4,
        },
        {
            "title": "Statistik Projektarbeit",
            "type": LeistungsnachweisType.PROJEKTARBEIT,
            "deadline": date(2026, 1, 14),
            "module": "Statistik",
            "topics": [
                "Phase 1: Datenerhebung - Fragebogen erstellen, Stichprobe definieren (n>100)",
                "Phase 2: Deskriptive Statistik - Mittelwert, Median, Standardabweichung, Varianz",
                "Phase 3: Grafische Darstellung - Histogramme, Boxplots, Streudiagramme in Excel/SPSS",
                "Phase 4: Wahrscheinlichkeitstheorie - Normalverteilung, Binomialverteilung, Z-Werte",
                "Phase 5: Hypothesentests - t-Test, Chi-Quadrat, ANOVA, Signifikanzniveau α=0.05",
                "Phase 6: Regression und Korrelation - Lineare Regression, R², Pearson-Korrelation",
                "Phase 7: SPSS Auswertung - Datenimport, Variablen definieren, Syntax schreiben",
                "Phase 8: Interpretation der Ergebnisse - Statistische vs. praktische Signifikanz",
                "Phase 9: Projektbericht schreiben - Methodik, Ergebnisse, Diskussion (20 Seiten)",
                "Phase 10: Präsentation vorbereiten - Kernerkenntnisse visualisieren, Vortrag üben (10 Min)",
            ],
            "priority": 4,
            "effort": 5,
        },
    ]

    # ==========================================
    # BELEGTE ZEITEN (Arbeit, Vorlesungen, Fussball)
    # ==========================================
    # Format: Wiederkehrende wöchentliche Termine
    busy_times = [
        {
            "label": "Arbeit (Teilzeit-Job)",
            "days": ["Montag", "Dienstag"],
            "start": "09:00",
            "end": "17:00",
        },
        {
            "label": "Fussballtraining",
            "days": ["Montag", "Mittwoch"],
            "start": "18:30",
            "end": "20:30",
        },
        {
            "label": "Vorlesungen (Marketing, VWL)",
            "days": ["Mittwoch"],
            "start": "08:00",
            "end": "12:00",
        },
        {
            "label": "Vorlesungen (Rechnungswesen, Statistik)",
            "days": ["Donnerstag"],
            "start": "08:00",
            "end": "13:00",
        },
        {
            "label": "Vorlesung (Unternehmensführung)",
            "days": ["Freitag"],
            "start": "09:00",
            "end": "12:00",
        },
        {
            "label": "Freunde treffen / Sport",
            "days": ["Samstag"],
            "start": "10:00",
            "end": "13:00",
        },
    ]

    # ==========================================
    # FERIEN & ABWESENHEITEN
    # ==========================================
    absences = [
        {
            "label": "Weihnachtsferien in New York",
            "start_date": date(2025, 12, 20),
            "end_date": date(2026, 1, 5),
            "description": "Zuhause bei Familie",
        },
    ]

    # ==========================================
    # PRÄFERENZEN
    # ==========================================
    preferences = {
        "spacing": True,  # Spaced Repetition - Ja!
        "interleaving": True,  # Fächer mischen - Ja!
        "deep_work": True,  # Längere Deep-Work Sessions
        "short_sessions": False,  # Keine kurzen Sessions bevorzugt
        "rest_days": ["Sonntag"],  # Sonntag = Ruhetag (DEUTSCH!)
        "max_hours_day": 5,  # Max 5h Lernen pro Tag (ist schon busy!)
        "max_hours_week": 25,  # Max 25h pro Woche
        "min_session_duration": 90,  # Mindestens 90 Min Sessions
        "earliest_study_time": "08:00",
        "latest_study_time": "22:00",
        "preferred_times_of_day": [
            "afternoon",
            "evening",
        ],  # Nachmittag/Abend bevorzugt
    }

    # ==========================================
    # KOMPLETTER SESSION STATE
    # ==========================================
    return {
        "study_start": study_start,
        "study_end": study_end,
        "leistungsnachweise": leistungsnachweise,
        "busy_times": busy_times,
        "absences": absences,
        "preferences": preferences,
        # UI State
        "current_page": "setup",
        "plan_generated": False,
        "study_plan": None,
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
    st.success(
        """
    ✅ **Test-Daten geladen!**
    
    **Profil: Max, 22 Jahre, BWL-Student**
    - 🏢 Arbeit: Montag & Dienstag (09:00-17:00)
    - ⚽ Fussball: Montag & Mittwoch Abend
    - 📚 Vorlesungen: Mittwoch, Donnerstag, Freitag
    - 🏖️ Ferien: Weihnachten (20.12. - 05.01.)
    - 📝 5 Prüfungen/Arbeiten im Semester
    """
    )

    st.info("💡 Wechsle jetzt zur **Lernplan**-Seite, um deinen KI-Lernplan zu generieren!")
