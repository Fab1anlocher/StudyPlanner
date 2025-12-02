# 🎓 AI Study Planner - KI-basierter Lernplaner

<div align="center">

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.29.0-red.svg)

**Ein intelligenter Lernplaner für Studierende mit KI-Unterstützung (OpenAI & Google Gemini)**

[🚀 Demo](#demo) • [📖 Features](#features) • [⚡ Quick Start](#quick-start) • [📚 Dokumentation](#dokumentation)

</div>

---

## 📖 Über das Projekt

Der **AI Study Planner** hilft Studierenden, ihre Lernzeit optimal zu organisieren. Du gibst deine Prüfungstermine, Arbeitszeiten und Präferenzen ein - die KI generiert einen personalisierten Lernplan basierend auf wissenschaftlichen Lernstrategien.

### ✨ Features

#### 🤖 KI-Powered Planning
- **Multi-LLM Support**: OpenAI (GPT-4o, GPT-4o-mini, GPT-3.5) oder Google Gemini
- **Prompt Engineering**: 4 vordefinierte Strategien + manueller Editor
- **Prüfungsformat-Awareness**: Unterschiedliche Lernmethoden für Multiple Choice, Coding, Essays, etc.

#### 📅 Intelligente Zeitplanung
- **Automatische Berechnung** freier Zeitfenster
- Berücksichtigt Vorlesungen, Arbeit, Hobbys
- **Spaced Repetition**, Interleaving, Deep Work
- Ruhetage und Abwesenheiten

#### 🎨 Flexible Darstellung
- **Wochenansicht**: Kalender mit Prüfungsterminen (🎯)
- **Listenansicht**: Chronologische Übersicht
- **PDF-Export**: Für Offline-Nutzung

#### 🧪 Experimentier-Modus
- **Manueller Prompt-Editor**: Eigene Prompts ohne Code schreiben
- **Export/Import**: Prompts als JSON speichern und teilen
- **5 Template-Prompts** für verschiedene Strategien
- **Test-Modus**: Vordefinierte Daten zum Ausprobieren

---

## ⚡ Quick Start

### 1️⃣ Installation

```bash
# Repository klonen
git clone https://github.com/Fab1anlocher/StudyPlanner.git
cd StudyPlanner

# Virtual Environment erstellen (empfohlen)
python -m venv .venv

# Virtual Environment aktivieren
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Abhängigkeiten installieren
pip install -r requirements.txt
```

### 2️⃣ App starten

```bash
streamlit run app.py
```

Die App öffnet sich automatisch im Browser unter `http://localhost:8501`

### 3️⃣ API Key konfigurieren

**Option A: OpenAI**
1. Account erstellen auf [platform.openai.com](https://platform.openai.com/)
2. API Key generieren unter "API Keys"
3. In der App: Sidebar → **Provider: OpenAI** → Key eingeben

**Option B: Google Gemini**
1. Account erstellen auf [ai.google.dev](https://ai.google.dev/)
2. API Key generieren
3. In der App: Sidebar → **Provider: Gemini** → Key eingeben

> 💡 **Tipp**: Gemini hat ein großzügiges kostenloses Kontingent!

---

## 🎯 Verwendung

### Schritt 1: Einrichtung (Seite "Einrichtung")

1. **API-Konfiguration**
   - Wähle Provider (OpenAI/Gemini) und Modell
   - Trage API Key ein

2. **Semester-Daten**
   - Start- und Enddatum

3. **Leistungsnachweise hinzufügen**
   - Typ (Prüfung, Hausarbeit, Präsentation, Projektarbeit)
   - Deadline und Prüfungsformat
   - Themen und Priorität

4. **Belegte Zeiten** (optional)
   - Vorlesungen, Arbeit, Sport, etc.

5. **Abwesenheiten** (optional)
   - Ferien, Militär, etc.

6. **Lernpräferenzen**
   - Ruhetage, maximale Lernzeit
   - Spaced Repetition, Deep Work, etc.

> 💡 **Quick-Test**: Klicke auf **"📋 Test-Daten laden"** für ein vordefiniertes BWL-Student-Profil!

### Schritt 2: Plan generieren (Seite "Lernplan")

1. **Zeitfenster berechnen**
   - Klicke auf **"⏰ Freie Zeitfenster berechnen"**
   - System berechnet verfügbare Lernzeiten

2. **KI-Plan erstellen**
   - Klicke auf **"🤖 Plan mit KI generieren"**
   - KI erstellt optimierten Lernplan

3. **Plan anzeigen**
   - **Wochenansicht**: Kalender mit farbcodierten Sessions
   - **Listenansicht**: Chronologische Übersicht

4. **PDF exportieren** (optional)
   - Klicke auf **"📥 Plan als PDF herunterladen"**

---

## 🧪 Prompt Engineering

### Vordefinierte Versionen

Sidebar → **Prompt Konfiguration** → **"Vorlagen"**

| Version | Strategie | Beschreibung |
|---------|-----------|--------------|
| **V1: Zero-Shot** | Baseline | Direkte Anweisungen ohne Beispiele |
| **V2: Few-Shot** | Beispiele | Zeigt konkrete Beispiele |
| **V3: Chain-of-Thought** | Reasoning | Schrittweises Denken |
| **V4: Few-Shot + CoT** | Hybrid | Kombination aus V2 & V3 |

### Manueller Modus (Experimentieren)

Sidebar → **Prompt Konfiguration** → **"Manuell"**

1. **Prompts bearbeiten**
   - System Prompt: Rolle & Regeln der KI
   - User Prompt Template: Verwendet Platzhalter wie `{leistungsnachweise}`

2. **Speichern**
   - Klicke **"💾 Prompts übernehmen"**

3. **Export/Import**
   - **Export**: Speichere als JSON für Dokumentation
   - **Import**: Lade gespeicherte Prompts

4. **Templates nutzen**
   - `data/prompt_templates/` Ordner enthält 5 fertige Templates
   - `minimal_prompt.json` - Minimalistisch
   - `balanced_prompt.json` - Ausgewogen
   - `ultra_detailed_prompt.json` - Maximal detailliert
   - `english_prompt.json` - Englische Version
   - `example_custom_prompt.json` - Standard-Template

---

## 📁 Projektstruktur

```
StudyPlanner/
├── app.py                      # 🎯 Hauptanwendung & Router
│
├── constants.py                # 📋 Zentrale Konstanten & Enums
├── planning.py                 # ⏱️ Core Zeitfenster-Berechnungen
│
├── config/                     # ⚙️ Konfiguration
│   ├── __init__.py
│   └── settings.py            # App-weite Einstellungen
│
├── models/                     # 📊 Pydantic Datenmodelle
│   ├── __init__.py
│   ├── leistungsnachweis.py   # Prüfungen & Assessments
│   ├── study_session.py       # Lernsessions & Free Slots
│   ├── busy_time.py           # Belegte Zeiten
│   ├── absence.py             # Abwesenheiten
│   └── preferences.py         # Benutzerpräferenzen
│
├── services/                   # 🔧 Business Logic Layer
│   ├── __init__.py
│   ├── llm_service.py         # LLM Provider Abstraction (OpenAI/Gemini)
│   ├── planning_service.py    # Zeitfenster-Berechnung Wrapper
│   ├── session_manager.py     # Session State Management
│   └── export_service.py      # PDF & Excel Export
│
├── ui/                         # 🎨 UI Layer
│   ├── __init__.py
│   ├── components/
│   │   ├── __init__.py
│   │   └── display_plan.py    # Plan-Visualisierung
│   └── pages/
│       ├── __init__.py
│       ├── setup_page.py      # Einrichtungs-Seite
│       ├── plan_page.py       # Lernplan-Seite
│       └── export_page.py     # Export-Seite
│
├── prompts/                    # 📝 Vordefinierte Prompt-Versionen
│   ├── __init__.py
│   ├── prompt_config.py       # Prompt-Version Konfiguration
│   ├── v1_zero_shot.py
│   ├── v2_few_shot.py
│   ├── v3_chain_of_thought.py
│   └── v4_few_shot_cot.py
│
├── data/                       # 📂 Daten & Templates
│   ├── __init__.py
│   ├── test_data.py           # Test-Daten für Entwicklung
│   └── prompt_templates/      # Experimentelle JSON-Templates
│       ├── minimal_prompt.json
│       ├── balanced_prompt.json
│       ├── ultra_detailed_prompt.json
│       ├── english_prompt.json
│       └── example_custom_prompt.json
│
├── .streamlit/                 # 🎨 Streamlit Config
│   └── config.toml
│
├── requirements.txt            # 📦 Dependencies
├── .gitignore                 # 🚫 Git Exclusions
├── ARCHITECTURE.md            # 📐 Architektur-Dokumentation
└── README.md                  # 📖 Diese Datei
```

### 🏗️ Architektur-Übersicht

```
┌─────────────────────────────────────────────┐
│           Streamlit UI Layer                │
│  (ui/pages/setup|plan|export_page.py)      │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│         Service Layer (Business Logic)      │
│  ┌──────────────────────────────────────┐  │
│  │ LLM Service (OpenAI/Gemini Adapter)  │  │
│  ├──────────────────────────────────────┤  │
│  │ Planning Service (Time Calculations) │  │
│  ├──────────────────────────────────────┤  │
│  │ Session Manager (State Management)   │  │
│  ├──────────────────────────────────────┤  │
│  │ Export Service (PDF/iCal/JSON)       │  │
│  └──────────────────────────────────────┘  │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│      Data Layer (Pydantic Models)           │
│  Leistungsnachweis | StudySession | ...     │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│         Constants & Configuration           │
│    Enums | Formats | Settings               │
└─────────────────────────────────────────────┘
```

**Layer-Verantwortlichkeiten:**
- **UI Layer**: Streamlit Widgets, User Input, Display
- **Service Layer**: Business Logic, API Calls, Berechnungen
- **Data Layer**: Type Safety, Validation, Schema
- **Config Layer**: Constants, Settings, Environment

---

## 🚀 Deployment

### Streamlit Cloud (Empfohlen)

1. **Repository vorbereiten**
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

2. **Streamlit Cloud**
   - Gehe zu [share.streamlit.io](https://share.streamlit.io)
   - Verbinde GitHub Account
   - Wähle Repository: `Fab1anlocher/StudyPlanner`
   - Main file: `app.py`
   - Deploy!

3. **Secrets konfigurieren** (optional)
   - App Settings → Secrets
   - Füge API Keys hinzu (nicht empfohlen für Multi-User Apps)

### Lokales Deployment

```bash
# Production-Modus
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

---

## 💰 API Kosten

### OpenAI
- **gpt-4o-mini**: ~$0.01-0.05 pro Plan (empfohlen)
- **gpt-4o**: ~$0.10-0.30 pro Plan
- **gpt-3.5-turbo**: ~$0.01-0.03 pro Plan

Prüfe Nutzung: [platform.openai.com/usage](https://platform.openai.com/usage)

### Google Gemini
- **gemini-1.5-flash**: Großzügiges kostenloses Kontingent ⭐
- **gemini-1.5-pro**: Ähnlich wie GPT-4o
- **gemini-pro**: Ähnlich wie GPT-3.5

Prüfe Nutzung: [ai.google.dev](https://ai.google.dev/)

---

## 📚 Dokumentation

| Datei | Beschreibung |
|-------|--------------|
| **README.md** | Diese Datei - Übersicht & Quick Start |
| **ARCHITECTURE.md** | Technische Architektur-Dokumentation |

---

## 🛠️ Technologie-Stack

- **Framework**: [Streamlit](https://streamlit.io/) 1.29.0
- **LLM-Provider**: 
  - [OpenAI](https://openai.com/) (GPT-4o, GPT-4o-mini, GPT-3.5-turbo)
  - [Google Gemini](https://ai.google.dev/) (gemini-1.5-flash, gemini-1.5-pro)
- **Data Validation**: [Pydantic](https://docs.pydantic.dev/) 2.x
- **Export Formate**: 
  - PDF via [fpdf2](https://pyfpdf.github.io/fpdf2/)
  - Excel (.xlsx) via [openpyxl](https://openpyxl.readthedocs.io/)
- **Sprache**: Python 3.8+

---

## 👥 Autoren

- **Locher, Wirth & Heiniger**
- Projekt: StudyPlanner
- GitHub: [@Fab1anlocher](https://github.com/Fab1anlocher)

---

<div align="center">

**Viel Erfolg beim Lernen! 🎓📚**

Made with ❤️ for students

</div>
