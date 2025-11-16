# Projekt-Struktur: KI-Lernplaner

## Übersicht

Dieses Projekt ist ein **AI-basierter Lernplaner für Studierende**, entwickelt mit Streamlit und OpenAI.

---

## Datei-Struktur

```
StudyPlanner/
│
├── app.py                      # Hauptanwendung (1763 Zeilen)
│   ├── calculate_free_slots()  # Berechnet verfügbare Lernzeiten
│   ├── generate_plan_via_ai()  # Ruft OpenAI API auf
│   ├── init_session_state()    # Initialisiert Session-Variablen
│   ├── create_plan_pdf()       # Generiert PDF-Export
│   ├── show_setup_page()       # Einrichtungs-Seite (7 Abschnitte)
│   ├── show_plan_page()        # Plan-Generierung und Ansicht
│   ├── show_adjustments_page() # Anpassungen und Neu-Generierung
│   ├── show_export_page()      # PDF-Download
│   ├── display_plan_views()    # Wochen- und Listenansicht
│   └── main()                  # Haupt-Entry-Point
│
├── prompts.py                  # LLM-Prompt-Vorlagen
│   ├── get_system_prompt()     # System-Nachricht für OpenAI
│   └── build_user_prompt()     # User-Prompt mit Kontext-Daten
│
├── requirements.txt            # Python-Dependencies
│   ├── streamlit==1.29.0
│   ├── openai==1.6.1
│   └── fpdf2==2.7.6
│
├── README.md                   # Projekt-Dokumentation (Deutsch)
├── .gitignore                  # Git-Ausschlüsse
└── PROJEKTSTRUKTUR.md          # Diese Datei
```

---

## Haupt-Komponenten

### 1. **Einrichtung** (Setup)
**Datei**: `app.py` → `show_setup_page()`

**7 Abschnitte**:
1. Semester-Daten (Start/Ende)
2. Module & Prüfungen
3. OpenAI API-Konfiguration
4. Belegte Zeiten (Arbeit, Vorlesungen, etc.)
5. Abwesenheiten (Ferien, Militär)
6. Ruhetage & Lern-Limits
7. Lernpräferenzen (Spaced Repetition, Interleaving, Deep Work)

**Session State Variablen**:
- `semester_start`, `semester_end`
- `modules` (Liste von Dicts)
- `openai_key`
- `busy_times` (wiederkehrende wöchentliche Zeiten)
- `absences` (spezifische Zeiträume)
- `preferences` (Dict mit Lernstrategien und Limits)

---

### 2. **Lernplan** (Plan Generation)
**Datei**: `app.py` → `show_plan_page()`

**Workflow**:
1. **Freie Zeitfenster berechnen**:
   - `calculate_free_slots()` iteriert durch Semester
   - Subtrahiert busy_times und absences
   - Berücksichtigt Ruhetage und max. Stunden/Tag

2. **KI-Plan generieren**:
   - `generate_plan_via_ai()` ruft OpenAI API auf
   - Nutzt `get_system_prompt()` und `build_user_prompt()`
   - Parst JSON-Response in `st.session_state.plan`

3. **Plan anzeigen**:
   - `display_plan_views()` zeigt Wochen- oder Listenansicht
   - `display_weekly_view()`: Kalender-Darstellung
   - `display_list_view()`: Chronologische Liste

---

### 3. **Anpassungen** (Adjustments)
**Datei**: `app.py` → `show_adjustments_page()`

**Funktionen**:
- Modul-Prioritäten anpassen (Slider 1-5)
- Belegte Zeiten hinzufügen/entfernen
- Lernpräferenzen ändern
- Plan neu generieren mit aktualisierten Settings

---

### 4. **Export** (PDF Download)
**Datei**: `app.py` → `show_export_page()`

**Funktionen**:
- `create_plan_pdf()`: Generiert PDF mit fpdf2
- Download-Button für `lernplan.pdf`
- Vorschau der ersten 5 Sessions
- Plan-Statistiken (Sessions, Module, Stunden, Tage)

---

## Datenfluss

```
1. User Input (Setup)
   ↓
2. Session State speichert Daten
   ↓
3. calculate_free_slots() → freie Zeitfenster
   ↓
4. generate_plan_via_ai() → OpenAI API Call
   ↓
5. JSON-Response → st.session_state.plan
   ↓
6. Display in Wochen-/Listenansicht
   ↓
7. Optional: Anpassungen → Neu-Generierung
   ↓
8. Export als PDF
```

---

## Session State Struktur

```python
st.session_state = {
    # Semester
    "semester_start": date,
    "semester_end": date,
    
    # Module
    "modules": [
        {
            "name": str,
            "exam_date": date,
            "topics": [str],
            "priority": int (1-5)
        }
    ],
    
    # API
    "openai_key": str,
    
    # Belegte Zeiten
    "busy_times": [
        {
            "label": str,
            "days": [str],  # ["Montag", "Dienstag", ...]
            "start": str,   # "08:00"
            "end": str      # "17:00"
        }
    ],
    
    # Abwesenheiten
    "absences": [
        {
            "label": str,
            "start_date": date,
            "end_date": date
        }
    ],
    
    # Präferenzen
    "preferences": {
        "rest_days": [str],           # ["Sonntag"]
        "max_hours_day": int,         # 8
        "max_hours_week": int | None, # 40 oder None
        "min_session_duration": int,  # 60 (Minuten)
        "spacing": bool,              # Spaced Repetition
        "interleaving": bool,         # Themenwechsel
        "deep_work": bool,            # Lange fokussierte Sessions
        "short_sessions": bool        # Kurze Sessions für Theorie
    },
    
    # Berechnete Daten
    "free_slots": [
        {
            "date": date,
            "start": str,  # "08:00"
            "end": str,    # "12:00"
            "hours": float # 4.0
        }
    ],
    
    # Generierter Plan
    "plan": [
        {
            "date": str,         # "2024-03-15"
            "start": str,        # "09:00"
            "end": str,          # "11:00"
            "module": str,       # "Mathematik"
            "topic": str,        # "Lineare Algebra"
            "description": str   # "Wiederholung Matrizen..."
        }
    ]
}
```

---

## Prompt-Strategie

**Datei**: `prompts.py`

### System Prompt
- Definiert die Rolle: "Expert educational planner assistant"
- Spezifiziert Output-Format: JSON array
- Keine zusätzlichen Erklärungen erlaubt

### User Prompt
- Semester-Daten
- Module mit Exam-Dates und Topics
- Lernpräferenzen
- Verfügbare Zeitfenster (JSON)
- Detaillierte Instruktionen für:
  - Prioritäts-Logik
  - Spaced Repetition
  - Interleaving
  - Deep Work vs. Short Sessions
  - Zeitlimits

**Warum getrennt?**
→ Einfache Anpassung ohne UI-Code zu ändern
→ Experimentelles Prompt Engineering
→ A/B-Testing verschiedener Prompts möglich

---

## Wichtige Algorithmen

### 1. Free Slot Calculation
```python
calculate_free_slots()
├── Iteriere durch alle Tage (semester_start bis semester_end)
├── Prüfe Abwesenheiten → skip day
├── Prüfe Ruhetage → skip day
├── Initialisiere Tages-Intervall (06:00 - 23:00)
├── Subtrahiere busy_times für diesen Wochentag
│   └── subtract_time_interval()
├── Truncate auf max_hours_day
│   └── truncate_intervals_to_max_hours()
└── Sammle alle Intervalle > min_session_duration
```

### 2. Time Interval Subtraction
```python
subtract_time_interval(intervals, busy_start, busy_end)
├── Für jedes Intervall:
│   ├── Kein Overlap → behalten
│   ├── Busy umschliesst Intervall → löschen
│   ├── Busy am Anfang → kürzen
│   ├── Busy am Ende → kürzen
│   └── Busy in der Mitte → split in 2 Intervalle
└── Return neue Intervall-Liste
```

### 3. PDF Generation
```python
create_plan_pdf(plan)
├── FPDF initialisieren
├── Titel-Seite mit Statistiken
├── Gruppiere Sessions nach Datum
├── Für jeden Tag:
│   ├── Datum-Header
│   └── Tabelle mit Sessions
└── Output als BytesIO
```

---

## Deutsche UI-Texte

**Konsistente Terminologie**:
- ✅ Einrichtung (nicht "Setup")
- ✅ Lernplan (nicht "Studienplan")
- ✅ Anpassungen (nicht "Einstellungen")
- ✅ Belegte Zeiten (nicht "Busy Times")
- ✅ Ruhetage (nicht "Freie Tage")
- ✅ Lernpräferenzen (nicht "Lerneinstellungen")

**Keine ß, sondern ss** (Schweizer Hochdeutsch):
- ✅ "Grösse" statt "Größe"
- ✅ "muss" statt "muß"
- ✅ "Schlüssel" statt "Schlüßel"

---

## Erweiterungs-Möglichkeiten

### Kurzfristig
- [ ] Kalender-Export (iCal/ICS)
- [ ] Excel-Export
- [ ] E-Mail-Versand des Plans
- [ ] Persistierung (JSON-Download/Upload)
- [ ] Session-Tracking (erledigte Sessions abhaken)

### Mittelfristig
- [ ] Datenbank-Integration (PostgreSQL/SQLite)
- [ ] User-Accounts und Login
- [ ] Sharing-Funktionen (Plan mit Kommilitonen teilen)
- [ ] Statistiken und Fortschritts-Tracking
- [ ] Mobile App (React Native mit Streamlit Backend)

### Langfristig
- [ ] Multi-Semester-Planung
- [ ] KI-Empfehlungen basierend auf Lernfortschritt
- [ ] Integration mit Canvas/Moodle
- [ ] Gamification (Punkte, Streaks, Achievements)
- [ ] Kollaborative Lerngruppen-Planung

---

## Performance-Optimierungen

**Bereits implementiert**:
- Session State für Daten-Persistenz
- Lazy Loading von Plan-Generierung
- Effiziente Zeitfenster-Berechnung (O(n) pro Tag)

**Mögliche Verbesserungen**:
- Caching von free_slots bei unveränderter Config
- Batch-Processing für grosse Semester (>200 Tage)
- Async API-Calls für schnellere Response
- Client-seitiges Caching (Browser LocalStorage)

---

## Troubleshooting

### App startet nicht
```bash
# Lösung 1: Dependencies neu installieren
pip install -r requirements.txt --upgrade

# Lösung 2: Python-Version prüfen (min. 3.8)
python --version

# Lösung 3: Streamlit-Version prüfen
streamlit --version
```

### API-Fehler
- OpenAI API Key prüfen
- API-Credits checken: platform.openai.com/usage
- Netzwerk-Verbindung testen

### PDF-Generation schlägt fehl
- fpdf2 installiert? `pip install fpdf2`
- Schreibrechte im Verzeichnis vorhanden?
- Plan-Daten valide? (JSON-Struktur prüfen)

---

## Kontakt & Support

- **GitHub**: https://github.com/Fab1anlocher/SmartStudyAssistant
- **Issues**: https://github.com/Fab1anlocher/SmartStudyAssistant/issues
- **Email**: (bei Bedarf ergänzen)

---

**Viel Erfolg mit dem KI-Lernplaner!** 🎓📚✨
