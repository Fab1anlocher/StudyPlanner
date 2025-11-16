# AI Lernplaner für Studierende

Ein intelligenter Lernplaner für Studierende, der mithilfe von künstlicher Intelligenz (OpenAI) einen personalisierten Lernplan für dein Semester erstellt.

## Projektbeschreibung

Diese Streamlit-App hilft dir, deine Lernzeit optimal zu organisieren. Du gibst deine Module, Prüfungstermine, Arbeitszeiten und Abwesenheiten ein, und die KI generiert einen detaillierten, auf deine Bedürfnisse zugeschnittenen Lernplan. Der Plan berücksichtigt wissenschaftliche Lernstrategien wie Spaced Repetition, Interleaving und Deep Work.

## Features

- ✅ **Modulverwaltung**: Erfasse deine Module mit Prüfungsterminen, Themen und Prioritäten
- ✅ **Zeiterfassung**: Trage deine wiederkehrenden Verpflichtungen ein (Arbeit, Vorlesungen, Sport)
- ✅ **Abwesenheiten**: Plane Ferien, Militär oder andere Abwesenheiten ein
- ✅ **Lernpräferenzen**: Wähle aus verschiedenen Lernstrategien:
  - Spaced Repetition (verteiltes Wiederholen)
  - Interleaving (Themenwechsel)
  - Deep Work (fokussierte Lernblöcke)
  - Kurze Sessions für theorielastige Fächer
- ✅ **Automatische Berechnung**: Die App berechnet alle verfügbaren freien Zeitfenster im Semester
- ✅ **KI-generierter Lernplan**: OpenAI erstellt einen optimierten Lernplan basierend auf deinen Eingaben
- ✅ **Flexible Ansichten**: 
  - Wochenansicht (Kalender-Darstellung)
  - Listenansicht (chronologische Übersicht)
- ✅ **Anpassungen**: Ändere Prioritäten und Einstellungen und generiere den Plan neu
- ✅ **PDF-Export**: Lade deinen Lernplan als PDF herunter

## Installation

1. Repository klonen:
```bash
git clone https://github.com/Fab1anlocher/SmartStudyAssistant.git
cd SmartStudyAssistant
```

2. Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
```

## Anwendung starten

Starte die App mit folgendem Befehl:

```bash
streamlit run app.py
```

Die App öffnet sich automatisch im Browser unter `http://localhost:8501`.

### OpenAI API Key

**Wichtig**: Du benötigst einen eigenen OpenAI API Key, um die KI-Funktionen zu nutzen.

1. Erstelle einen Account auf [platform.openai.com](https://platform.openai.com/)
2. Generiere einen API Key unter "API Keys"
3. Gib den Key in der App auf der "Einrichtung"-Seite unter "OpenAI API-Konfiguration" ein

Der API Key wird nur in deiner Browser-Session gespeichert und nie auf einem Server abgelegt.

## Projekt-Struktur

```
StudyPlanner/
├── app.py              # Hauptanwendung mit UI und Logik
├── prompts.py          # LLM-Prompt-Vorlagen (getrennt für einfache Anpassung)
├── requirements.txt    # Python-Abhängigkeiten
├── README.md           # Diese Datei
└── .gitignore         # Git-Ausschlüsse
```

## Verwendung

### 1. Einrichtung
- **Semester-Daten**: Wähle Start- und Enddatum deines Semesters
- **Module**: Füge alle Module mit Prüfungsdatum, Themen und Priorität hinzu
- **API-Schlüssel**: Trage deinen OpenAI API Key ein
- **Belegte Zeiten**: Erfasse wiederkehrende Termine (z.B. Arbeit Mo-Fr 08:00-17:00)
- **Abwesenheiten**: Trage Ferien und andere Abwesenheiten ein
- **Ruhetage**: Wähle deine Ruhetage (z.B. Sonntag)
- **Lern-Limits**: Setze maximale Lernstunden pro Tag und Woche
- **Lernpräferenzen**: Aktiviere gewünschte Lernstrategien

### 2. Lernplan generieren
- **Schritt 1**: Berechne freie Zeitfenster (berücksichtigt alle deine Einschränkungen)
- **Schritt 2**: Lasse die KI einen optimierten Lernplan erstellen
- Betrachte den Plan in Wochen- oder Listenansicht

### 3. Anpassungen
- Ändere Modul-Prioritäten
- Passe belegte Zeiten an
- Modifiziere Lernpräferenzen
- Generiere den Plan mit den neuen Einstellungen neu

### 4. Export
- Lade deinen Lernplan als PDF herunter
- Drucke ihn aus oder importiere ihn in deinen Kalender

## Hinweise

### Datenspeicherung
- Alle Daten werden nur in der aktuellen Browser-Session gespeichert (Streamlit Session State)
- Beim Neuladen der Seite gehen die Daten verloren
- Es gibt keine Datenbank oder Benutzerkonten
- Deine Daten verlassen deinen Browser nur für die OpenAI API-Anfrage

### Anpassung der Prompts
Die KI-Prompts können in der Datei `prompts.py` angepasst werden:
- `get_system_prompt()`: Definiert die Rolle und Verhaltensweise der KI
- `build_user_prompt(data)`: Erstellt den Kontext für die Plan-Generierung

Du kannst diese Funktionen bearbeiten, um die KI-Ausgabe zu beeinflussen (z.B. mehr Pausen, kürzere Sessions, andere Lernstrategien).

### Kosten
Die Verwendung der OpenAI API verursacht Kosten. Das verwendete Modell (`gpt-4o-mini`) ist sehr günstig:
- Eine Plan-Generierung kostet ca. $0.01-0.05
- Prüfe deine API-Nutzung regelmässig auf [platform.openai.com](https://platform.openai.com/usage)

## Technische Details

- **Framework**: Streamlit 1.29.0
- **KI-Modell**: OpenAI GPT-4o-mini
- **PDF-Generierung**: fpdf2
- **Sprache**: Python 3.8+

## Lizenz

Dieses Projekt wurde als Studienprojekt entwickelt und steht für Bildungszwecke zur Verfügung.

## Support

Bei Fragen oder Problemen öffne ein Issue auf GitHub oder kontaktiere den Entwickler.

---

**Viel Erfolg beim Lernen!** 🎓📚
