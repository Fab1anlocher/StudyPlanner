"""
Test-Daten für verschiedene Studenten-Profile

Verfügbare Profile:
1. Fabian (BWL-Student) - Prüfungen im Dezember/Januar
2. Lena (Wirtschaftsinformatik-Studentin) - Prüfungen im Juni/Juli
"""

from datetime import date, time, timedelta

from constants import LeistungsnachweisType, ExamFormat, DEFAULT_PREFERENCES


# ════════════════════════════════════════════════════════════════
# AVAILABLE TEST PROFILES
# ════════════════════════════════════════════════════════════════

AVAILABLE_TEST_PROFILES = {
    "fabian": "Fabian (BWL, Winter)",
    "lena": "Lena (Wirtschaftsinformatik, Sommer)",
}


def get_fabian_test_data():
    """
    Testdaten für Fabian: BWL-Student, Prüfungen im Dezember/Januar.
    
    Profil: Fabian, 22 Jahre, BWL-Student im 5. Semester
    - Arbeitet Montag & Dienstag (09:00-17:00) im Teilzeit-Job
    - Fussballtraining: Montag & Mittwoch Abend (18:30-20:30)
    - Vorlesungen: Mittwoch, Donnerstag, Freitag Vormittag
    - Wochenende: Samstag teilweise frei, Sonntag Ruhetag
    - Weihnachtsferien: 20.12.2025 - 05.01.2026

    Returns:
        dict: Dictionary mit allen Session-State Daten
    """

    # Semester-Zeitraum
    study_start = date(2025, 12, 2)
    study_end = date(2026, 1, 22)  # Ende basierend auf letzter Prüfung (Rechnungswesen)

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
    # Format: Wiederkehrende wöchentliche Termine mit Gültigkeitszeitraum
    # Vorlesungen enden Mitte Dezember, danach ist mehr Zeit zum Lernen!
    busy_times = [
        {
            "label": "Arbeit (Teilzeit-Job)",
            "days": ["Montag", "Dienstag"],
            "start": "09:00",
            "end": "17:00",
            "valid_from": date(2025, 12, 2),
            "valid_until": None,  # Durchgehend
        },
        {
            "label": "Fussballtraining",
            "days": ["Montag", "Mittwoch"],
            "start": "18:30",
            "end": "20:30",
            "valid_from": date(2025, 12, 2),
            "valid_until": None,  # Durchgehend
        },
        {
            "label": "Vorlesungen (Marketing, VWL)",
            "days": ["Mittwoch"],
            "start": "08:00",
            "end": "12:00",
            "valid_from": date(2025, 12, 2),
            "valid_until": date(2025, 12, 18),  # Vorlesungen enden vor Weihnachten
        },
        {
            "label": "Vorlesungen (Rechnungswesen, Statistik)",
            "days": ["Donnerstag"],
            "start": "08:00",
            "end": "13:00",
            "valid_from": date(2025, 12, 2),
            "valid_until": date(2025, 12, 18),  # Vorlesungen enden vor Weihnachten
        },
        {
            "label": "Vorlesung (Unternehmensführung)",
            "days": ["Freitag"],
            "start": "09:00",
            "end": "12:00",
            "valid_from": date(2025, 12, 2),
            "valid_until": date(2025, 12, 19),  # Letzte Vorlesung
        },
        {
            "label": "Freunde treffen / Sport",
            "days": ["Samstag"],
            "start": "10:00",
            "end": "13:00",
            "valid_from": date(2025, 12, 2),
            "valid_until": None,  # Durchgehend
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
        "profile_name": "Fabian",
    }


def get_lena_test_data():
    """
    Testdaten für Lena: Wirtschaftsinformatik-Studentin, Prüfungen im Juni/Juli.
    
    Profil: Lena, 24 Jahre, Wirtschaftsinformatik-Studentin im 4. Semester
    - Vorlesungen: Montag bis Freitag (08:00-14:00)
    - Nebenjob: Samstag (10:00-16:00)
    - Sonntag: Ruhetag
    - Pfingstferien: 07.06.2025 - 15.06.2025
    
    Returns:
        dict: Dictionary mit allen Session-State Daten
    """

    # Semester-Zeitraum (Sommersemester)
    study_start = date(2025, 5, 1)
    study_end = date(2025, 7, 18)  # Ende basierend auf letzter Prüfung

    # ==========================================
    # LEISTUNGSNACHWEISE (5 Prüfungen/Arbeiten)
    # ==========================================
    leistungsnachweise = [
        {
            "title": "Datenbanken Prüfung",
            "type": LeistungsnachweisType.PRUEFUNG,
            "deadline": date(2025, 6, 20),
            "module": "Datenbanken",
            "topics": [
                "Kapitel 1: Einführung in Datenbanken - DBMS, Relationale Modelle",
                "Kapitel 2: SQL Grundlagen - SELECT, INSERT, UPDATE, DELETE",
                "Kapitel 3: Erweiterte SQL - Joins, Subqueries, Aggregatfunktionen",
                "Kapitel 4: Normalisierung - 1NF, 2NF, 3NF, BCNF",
                "Kapitel 5: ER-Modellierung - Entities, Relationships, Attribute",
                "Kapitel 6: Transaktionen - ACID, Isolation Levels",
                "Kapitel 7: Indexierung und Performance - B-Trees, Hash-Index",
                "Übungsaufgaben - SQL-Queries und ER-Diagramme",
            ],
            "priority": 5,
            "effort": 4,
            "exam_format": ExamFormat.RECHENAUFGABEN,
            "exam_details": "90 Minuten, SQL-Queries schreiben, ER-Diagramme zeichnen, Normalisierung durchführen",
        },
        {
            "title": "Software Engineering Projekt",
            "type": LeistungsnachweisType.PROJEKTARBEIT,
            "deadline": date(2025, 7, 5),
            "module": "Software Engineering",
            "topics": [
                "Phase 1: Anforderungsanalyse - Use Cases, User Stories",
                "Phase 2: Systemdesign - UML-Diagramme, Architektur",
                "Phase 3: Implementierung - Clean Code, Design Patterns",
                "Phase 4: Testing - Unit Tests, Integration Tests",
                "Phase 5: Dokumentation - README, API-Docs",
                "Präsentation - Demo und Verteidigung (15 Min)",
            ],
            "priority": 5,
            "effort": 5,
        },
        {
            "title": "Algorithmen und Datenstrukturen",
            "type": LeistungsnachweisType.PRUEFUNG,
            "deadline": date(2025, 6, 28),
            "module": "Algorithmen",
            "topics": [
                "Teil 1: Komplexitätsanalyse - Big-O, Omega, Theta",
                "Teil 2: Sortieralgorithmen - QuickSort, MergeSort, HeapSort",
                "Teil 3: Suchalgorithmen - Binäre Suche, Hashtables",
                "Teil 4: Graphen - BFS, DFS, Dijkstra, Kruskal",
                "Teil 5: Dynamische Programmierung - Prinzipien, Beispiele",
                "Teil 6: Bäume - Binärbäume, AVL, B-Bäume",
                "Übungsblätter 1-10 durcharbeiten",
            ],
            "priority": 4,
            "effort": 5,
            "exam_format": ExamFormat.RECHENAUFGABEN,
            "exam_details": "120 Minuten, Pseudocode schreiben, Komplexität analysieren, Closed Book",
        },
        {
            "title": "Webentwicklung Hausarbeit",
            "type": LeistungsnachweisType.HAUSARBEIT,
            "deadline": date(2025, 7, 12),
            "module": "Webentwicklung",
            "topics": [
                "Kapitel 1: HTML5 und CSS3 - Moderne Webtechnologien",
                "Kapitel 2: JavaScript - DOM, Events, Async/Await",
                "Kapitel 3: React/Vue Framework - Komponenten, State Management",
                "Kapitel 4: REST APIs - Design, Implementation",
                "Kapitel 5: Sicherheit - XSS, CSRF, Authentication",
                "Praktische Arbeit - Full-Stack Webanwendung entwickeln",
            ],
            "priority": 3,
            "effort": 4,
        },
        {
            "title": "Betriebssysteme Prüfung",
            "type": LeistungsnachweisType.PRUEFUNG,
            "deadline": date(2025, 7, 18),
            "module": "Betriebssysteme",
            "topics": [
                "Kapitel 1: Prozesse und Threads - Scheduling, Synchronisation",
                "Kapitel 2: Speicherverwaltung - Paging, Segmentierung",
                "Kapitel 3: Dateisysteme - Struktur, Zugriffsmethoden",
                "Kapitel 4: I/O-Management - Gerätetreiber, Buffering",
                "Kapitel 5: Deadlocks - Erkennung, Vermeidung, Recovery",
                "Kapitel 6: Virtualisierung - VMs, Container",
                "Übungsklausuren durcharbeiten",
            ],
            "priority": 4,
            "effort": 4,
            "exam_format": ExamFormat.GEMISCHT,
            "exam_details": "90 Minuten, Multiple Choice + Rechenaufgaben, 1 A4 Formelblatt erlaubt",
        },
    ]

    # ==========================================
    # BELEGTE ZEITEN (Vorlesungen, Nebenjob)
    # ==========================================
    # Vorlesungen enden Mitte Juni, aber Prüfungen sind bis Ende Juli
    busy_times = [
        {
            "label": "Vorlesungen (Datenbanken, Algorithmen)",
            "days": ["Montag", "Mittwoch"],
            "start": "08:00",
            "end": "14:00",
            "valid_from": date(2025, 5, 1),
            "valid_until": date(2025, 6, 20),  # Vorlesungen enden vor Prüfungsphase
        },
        {
            "label": "Vorlesungen (Software Engineering)",
            "days": ["Dienstag"],
            "start": "08:00",
            "end": "12:00",
            "valid_from": date(2025, 5, 1),
            "valid_until": date(2025, 6, 20),  # Vorlesungen enden vor Prüfungsphase
        },
        {
            "label": "Vorlesungen (Webentwicklung, Betriebssysteme)",
            "days": ["Donnerstag", "Freitag"],
            "start": "08:00",
            "end": "14:00",
            "valid_from": date(2025, 5, 1),
            "valid_until": date(2025, 6, 20),  # Vorlesungen enden vor Prüfungsphase
        },
        {
            "label": "Nebenjob IT-Support",
            "days": ["Samstag"],
            "start": "10:00",
            "end": "16:00",
            "valid_from": date(2025, 5, 1),
            "valid_until": None,  # Durchgehend
        },
    ]

    # ==========================================
    # FERIEN & ABWESENHEITEN
    # ==========================================
    absences = [
        {
            "label": "Pfingstferien",
            "start_date": date(2025, 6, 7),
            "end_date": date(2025, 6, 15),
            "description": "Familienbesuch",
        },
    ]

    # ==========================================
    # PRÄFERENZEN
    # ==========================================
    preferences = {
        "spacing": True,
        "interleaving": False,  # Fokus auf ein Fach pro Block
        "deep_work": True,  # Längere Sessions für Coding
        "short_sessions": False,
        "rest_days": ["Sonntag"],
        "max_hours_day": 6,  # Max 6h Lernen pro Tag
        "max_hours_week": 30,  # Max 30h pro Woche
        "min_session_duration": 60,  # Mindestens 60 Min Sessions
        "earliest_study_time": "14:00",  # Nach den Vorlesungen
        "latest_study_time": "21:00",
        "preferred_times_of_day": [
            "afternoon",
        ],  # Nachmittag bevorzugt
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
        "profile_name": "Lena",
    }


# Alias for backward compatibility
def get_test_data():
    """
    Gibt Testdaten für Fabian zurück (Standard-Profil für Abwärtskompatibilität).
    
    Returns:
        dict: Dictionary mit allen Session-State Daten
    """
    return get_fabian_test_data()


def get_test_data_by_profile(profile_key: str):
    """
    Gibt Testdaten für ein bestimmtes Profil zurück.
    
    Args:
        profile_key: Der Schlüssel des Profils ("fabian" oder "lena")
        
    Returns:
        dict: Dictionary mit allen Session-State Daten
    """
    if profile_key == "lena":
        return get_lena_test_data()
    else:
        return get_fabian_test_data()


def load_test_data_into_session_state(st, profile_key: str = "fabian"):
    """
    Lädt Test-Daten direkt in den Streamlit Session State.

    Args:
        st: Streamlit module
        profile_key: Der Schlüssel des Profils ("fabian" oder "lena")
    """
    test_data = get_test_data_by_profile(profile_key)

    # Alle Daten in Session State laden
    for key, value in test_data.items():
        st.session_state[key] = value

    profile_name = test_data.get("profile_name", profile_key.capitalize())
    
    if profile_key == "fabian":
        st.success(
            f"""
        ✅ **Test-Daten geladen: {profile_name}**
        
        **Profil: Fabian, 22 Jahre, BWL-Student**
        - 🏢 Arbeit: Montag & Dienstag (09:00-17:00)
        - ⚽ Fussball: Montag & Mittwoch Abend
        - 📚 Vorlesungen: Mittwoch, Donnerstag, Freitag
        - 🏖️ Ferien: Weihnachten (20.12. - 05.01.)
        - 📝 5 Prüfungen/Arbeiten im Semester (Dez/Jan)
        """
        )
    else:  # lena
        st.success(
            f"""
        ✅ **Test-Daten geladen: {profile_name}**
        
        **Profil: Lena, 24 Jahre, Wirtschaftsinformatik-Studentin**
        - 📚 Vorlesungen: Mo-Fr (08:00-14:00)
        - 💼 Nebenjob: Samstag (10:00-16:00)
        - 🏖️ Ferien: Pfingsten (07.06. - 15.06.)
        - 📝 5 Prüfungen/Arbeiten im Sommersemester (Juni/Juli)
        """
        )

    st.info("💡 Wechsle jetzt zur **Lernplan**-Seite, um deinen KI-Lernplan zu generieren!")
