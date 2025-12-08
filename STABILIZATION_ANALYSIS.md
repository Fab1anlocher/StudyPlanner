# Non-Destructive Code Stabilization Analysis
**Date:** 2025-12-08  
**Role:** Senior Lead Engineer - Audit & Stabilization  
**Objective:** Non-Destructive Stabilization - Make code robust without changing logic

---

## 1. Prompt Review – Kommentare

### A) System Prompt (prompts/v4_few_shot_cot.py, lines 10-148)

**⚠️ AMBIGUITÄT: Exam Format Handling**
- **Zeile 25-34**: Liste von exam_formats ist vollständig, ABER:
  - RISIKO: LLM könnte eigene Formate erfinden bei ungültigen Eingaben
  - EMPFEHLUNG: Prompt explizit machen: "VERWENDE NUR diese exam_formats aus den Eingangsdaten. ERFINDE KEINE NEUEN."

**✅ GUT: Klare Constraints**
- Zeile 51: "Nutze nur die vom Studenten angegebenen freien Zeitfenster" - klar und eindeutig
- Zeile 56: "Wenn möglich nicht mehr als 2–3 fokussierte Lerneinheiten pro Tag" - realistisch

**⚠️ PRÄZISIERUNGSBEDARF: Implizite Annahmen**
- **Zeile 54-56**: "45–120 Minuten" Sessions
  - IMPLIZITE ANNAHME: Was bei sehr kurzen Slots (<45min)? Soll LLM diese ignorieren oder nutzen?
  - EMPFEHLUNG: Ergänze Regel: "Bei Slots <45min: Nutze sie nur wenn dringend nötig, gruppiere zu längeren Blöcken wo möglich"

**⚠️ HALLUZINATIONS-RISIKO: Deadline-Violations**
- **Zeile 44**: "Werden alle relevanten Deadlines sinnvoll vorbereitet?"
  - RISIKO: Keine explizite Warnung wenn nicht genug Zeit für alle Deadlines
  - EMPFEHLUNG: Ergänze: "WENN nicht genug Zeit für alle Module: Priorisiere nach deadline UND priority, markiere kritische Zeitnot"

### B) User Prompt Template (prompts/v4_few_shot_cot.py, lines 203-242)

**✅ EXZELLENT: Vollständige Datenreferenz**
- Zeilen 204-236: Alle Inputs werden klar strukturiert übergeben (semester, leistungsnachweise, free_slots, preferences, absences, busy_times)
- JSON-Format mit ensure_ascii=False - gut für deutsche Umlaute

**⚠️ VERBESSERUNGSPOTENTIAL: Kontext bei Abwesenheiten & Busy Times**
- **Zeilen 224-235**: Labels werden übergeben ("Urlaub", "Vorlesung Marketing")
  - GUT: Prompt erklärt den Kontext (Zeilen 225-234)
  - RISIKO: LLM könnte Kontext ignorieren bei hoher Systemlast
  - EMPFEHLUNG: Verstärke in System-Prompt: "BEACHTE ZWINGEND die Labels von absences und busy_times für intelligente Planung"

**⚠️ EDGE CASE: Leere Listen**
- RISIKO: Was wenn free_slots = [] oder leistungsnachweise = []?
- FEHLT: Guard im Prompt wie "WENN keine freien Slots: Gib Fehlermeldung zurück"
- EMPFEHLUNG: Ergänze Validation-Regel im System-Prompt

---

## 2. Code Review – Kommentare

### A) app.py

**Line 72-75: API Key Validation**
```python
if not st.session_state.openai_key:
    st.error("❌ API-Schlüssel fehlt...")
```
**✅ GUT**: Frühe Validation

**Lines 92-100: Prompt Data Preparation**
```python
prompt_data = {
    "semester_start": st.session_state.study_start,
    "semester_end": st.session_state.study_end,
    ...
}
```
**// REVIEW: Keine Validation ob study_start/study_end None sind**
- RISIKO: KeyError wenn Daten nicht initialisiert
- EMPFEHLUNG: Ergänze Guard:
  ```python
  if not st.session_state.get("study_start") or not st.session_state.get("study_end"):
      st.error("❌ Semester-Zeitraum fehlt")
      return False
  ```

**Lines 111-161: Manual Prompt Placeholder Replacement**
```python
user_message = user_message.replace("{semester_start}", str(prompt_data["semester_start"]))
```
**// REVIEW: Einfache String-Ersetzung anfällig bei fehlenden Platzhaltern**
- RISIKO: Wenn Template {semester_start} nicht enthält, keine Warnung
- RISIKO: JSON-Serialisierung könnte fehlschlagen bei komplexen Objekten
- EMPFEHLUNG: Ergänze try/except um json.dumps() calls mit klarer Fehlermeldung

**Lines 183-200: LLM Response Validation**
```python
if not isinstance(plan, list):
    st.error("❌ KI-Antwort ist keine gültige Liste")
    return False
```
**✅ GUT**: Type-Check vorhanden
**// REVIEW: Aber keine Validation der List-Inhalte**
- RISIKO: LLM könnte leere Liste oder falsche Objekte zurückgeben
- EMPFEHLUNG: Ergänze:
  ```python
  if not plan:
      st.warning("⚠️ KI hat leeren Plan generiert. Versuche es mit mehr freien Zeitfenstern.")
      return False
  
  # Validate first element has required fields
  required_fields = ["date", "start", "end", "module", "topic", "description"]
  if plan and not all(field in plan[0] for field in required_fields):
      st.error("❌ KI-Antwort hat ungültiges Format")
      return False
  ```

### B) planning.py

**Lines 46-50: Input Validation**
```python
if not study_start or not study_end:
    return None, "Semester-Start und Semester-Ende müssen gesetzt sein."
if study_start >= study_end:
    return None, "Semester-Start muss vor Semester-Ende liegen."
```
**✅ EXZELLENT**: Frühe Guards vorhanden

**// REVIEW: Fehlende Validation für extreme Zeiträume**
- Lines 46-50
- RISIKO: User könnte 10-Jahres-Zeitraum eingeben → Performance-Problem
- EMPFEHLUNG: Ergänze:
  ```python
  if (study_end - study_start).days > 365:
      return None, "Planungszeitraum darf maximal 1 Jahr betragen."
  ```

**Lines 53-62: Absence Lookup Building**
```python
for absence in absences:
    absence_start_date = absence.get("start")
    absence_end_date = absence.get("end")
    if absence_start_date and absence_end_date:
        # ... build lookup
```
**// REVIEW: Keine Validation ob start < end**
- RISIKO: Ungültige Abwesenheiten (end vor start) könnten System verwirren
- EMPFEHLUNG: Ergänze Guard:
  ```python
  if absence_start_date > absence_end_date:
      # Skip invalid absence oder return error
      continue
  ```

**Lines 105-112: Busy Time Validity Check** (NEUE FEATURE entdeckt!)
```python
if valid_from is not None and current_date < valid_from:
    continue  # Busy time hasn't started yet
if valid_until is not None and current_date > valid_until:
    continue  # Busy time has ended
```
**✅ EXZELLENT**: Validity-Periode-Feature ist vorhanden!
**// REVIEW: Aber nicht dokumentiert im Prompt**
- RISIKO: LLM kennt dieses Feature nicht → kann es nicht nutzen
- EMPFEHLUNG: Ergänze in User-Prompt Dokumentation über valid_from/valid_until

**Lines 149-186: subtract_time_interval() Edge Cases**
```python
def subtract_time_interval(free_start, free_end, busy_start, busy_end):
    if busy_end <= free_start or busy_start >= free_end:
        return [(free_start, free_end)]  # No overlap
```
**✅ GUT**: Alle Overlap-Fälle abgedeckt
**// REVIEW: Keine Prüfung ob Zeiten gültig (busy_start < busy_end)**
- RISIKO: Ungültige Eingaben könnten zu falschen Berechnungen führen
- EMPFEHLUNG: Ergänze Assertion am Anfang:
  ```python
  assert free_start < free_end, "Invalid free interval"
  assert busy_start < busy_end, "Invalid busy interval"
  ```

### C) services/llm_service.py

**Lines 106-126: Retry Logic mit Exponential Backoff**
```python
for attempt in range(retry_attempts):
    try:
        return self._generate_raw(...)
    except LLMRateLimitError as e:
        if attempt < retry_attempts - 1:
            delay = retry_delay * (2**attempt)
            time.sleep(delay)
```
**✅ EXZELLENT**: Robuste Retry-Strategie

**// REVIEW: Keine maximale Delay-Grenze**
- RISIKO: Bei retry_attempts=10 könnte delay = 1 * 2^9 = 512 Sekunden
- EMPFEHLUNG: Ergänze Max-Delay Cap:
  ```python
  delay = min(retry_delay * (2**attempt), 60)  # Max 60 Sekunden
  ```

**Lines 146-177: JSON Extraction aus Markdown**
```python
if "```json" in response_text:
    start_idx = response_text.find("```json") + 7
    end_idx = response_text.find("```", start_idx)
```
**✅ GUT**: Mehrere Fallbacks (json, ```json, ```)
**// REVIEW: Aber keine Behandlung von mehreren Code-Blocks**
- RISIKO: Wenn LLM mehrere JSON-Blöcke zurückgibt, nur erster wird genommen
- RISIKO: Wenn LLM Text VOR dem JSON-Block schreibt, könnte Parsing fehlschlagen
- EMPFEHLUNG: Ergänze Logging für Debugging:
  ```python
  import logging
  logger.warning(f"JSON nicht direkt parsebar, extrahiere aus Markdown. Response-Preview: {response_text[:100]}")
  ```

**Lines 199-215: OpenAI Provider Error Handling**
```python
except OpenAIRateLimitError as e:
    raise LLMRateLimitError(f"OpenAI Rate Limit: {repr(e)}") from e
except Exception as e:
    raise LLMError(f"OpenAI API Error: {repr(e)}") from e
```
**✅ GUT**: Spezifische Exception-Hierarchie
**// REVIEW: repr(e) könnte sensitive Info enthalten (API Keys in Error-Messages?)**
- RISIKO: Bei Logging könnten API-Fehler mit sensiblen Daten geloggt werden
- EMPFEHLUNG: Prüfe ob OpenAI errors API-Key enthalten, sonst OK

### D) services/planning_service.py

**Lines 69-76: Date Type Conversion**
```python
if isinstance(study_start, datetime):
    study_start = study_start.date()
elif not isinstance(study_start, date):
    return [], "Ungültiges Startdatum-Format."
```
**✅ EXZELLENT**: Defensive Type-Handling

**Lines 89-90: Time Boundaries Determination**
```python
earliest_study_time, latest_study_time = _get_time_boundaries(preferred_times)
```
**// REVIEW: Funktion benutzt pre-computed constants (_TIME_07_00, etc.)**
- ✅ PERFORMANCE-OPTIMIERUNG: Sehr gut!
- Lines 19-25: Module-Level-Konstanten vermeiden wiederholtes datetime.strptime()

**Lines 193-201: Busy Times Conversion mit Validity**
```python
converted.append({
    "day": english_day,
    "start": datetime.strptime(busy["start"], TIME_FORMAT).time(),
    "end": datetime.strptime(busy["end"], TIME_FORMAT).time(),
    "label": label,
    "valid_from": valid_from,
    "valid_until": valid_until,
})
```
**✅ GUT**: Label und Validity werden korrekt weitergegeben
**// REVIEW: Keine Exception-Handling bei strptime()**
- RISIKO: Wenn TIME_FORMAT nicht passt (z.B. "14:30:00" statt "14:30"), ValueError
- EMPFEHLUNG: Ergänze try/except:
  ```python
  try:
      start_time = datetime.strptime(busy["start"], TIME_FORMAT).time()
  except ValueError:
      # Log warning and skip this busy time
      continue
  ```

### E) prompts/v4_few_shot_cot.py

**Lines 163-201: Date Serialization**
```python
for ln in leistungsnachweise:
    ln_copy = ln.copy()
    if "deadline" in ln_copy and hasattr(ln_copy["deadline"], "isoformat"):
        ln_copy["deadline"] = ln_copy["deadline"].isoformat()
```
**✅ GUT**: Defensive hasattr() Check
**// REVIEW: Aber keine Prüfung ob isoformat() fehlschlägt**
- RISIKO: Theoretisch könnte hasattr True sein, aber isoformat() trotzdem Exception werfen
- EMPFEHLUNG: Ergänze try/except als zusätzlicher Guard (Best Practice)

**Lines 169-173: Exam Format Enum Conversion**
```python
if "exam_format" in ln_copy and ln_copy["exam_format"] is not None:
    if hasattr(ln_copy["exam_format"], "value"):
        ln_copy["exam_format"] = ln_copy["exam_format"].value
```
**✅ GUT**: Null-Check und hasattr
**// REVIEW: Was wenn exam_format ein String ist (kein Enum)?**
- RISIKO: Bei manuell erstellten Dicts könnte exam_format bereits String sein
- EMPFEHLUNG: Ergänze elif-Zweig:
  ```python
  elif isinstance(ln_copy["exam_format"], str):
      pass  # Already a string, no conversion needed
  ```

---

## 3. Validierungs-Check Lernplan

### Zeitlimits & Pausen

| Check | Status | Details |
|-------|--------|---------|
| **Max Hours/Day Respected** | ✅ | planning.py Lines 123-124: truncate_intervals_to_max_hours() |
| **Max Hours/Week Respected** | ✅ | planning.py Lines 143-145: apply_weekly_limit() |
| **Min Session Duration** | ✅ | planning.py Lines 126-127: filter_by_min_duration() |
| **Rest Days Excluded** | ✅ | planning.py Lines 90-93: rest_days_set lookup |

### Pausen & Erholung

| Check | Status | Details |
|-------|--------|---------|
| **Ruhetage werden respektiert** | ✅ | Über rest_days konfigurierbar |
| **Pausen zwischen Sessions** | ⚠️ | **FEHLT: LLM hat keinen expliziten Pause-Befehl** |
| **Pause nach langer Session** | ⚠️ | **FEHLT: Keine 15-Min-Pause-Regel nach 90+ Min Sessions** |
| **Kein Lernen nach 22:00** | ⚠️ | **Konfigurierbar über latest_study_time, aber kein Hard-Limit** |

**EMPFEHLUNG (Pausen):**
- Ergänze in System-Prompt (v4_few_shot_cot.py):
  ```
  PAUSENREGELN:
  • Nach Sessions >90 Min: Mindestens 15 Min Pause vor nächster Session
  • Nicht mehr als 3 Sessions hintereinander ohne längere Pause (30+ Min)
  • Letztes Zeitfenster des Tages sollte vor 22:00 enden (gesunder Schlaf)
  ```

### Deadlines & Priorisierung

| Check | Status | Details |
|-------|--------|---------|
| **Deadlines in Eingangsdaten** | ✅ | leistungsnachweis.deadline vorhanden |
| **Priorität pro Leistungsnachweis** | ✅ | leistungsnachweis.priority (1-5) |
| **Prüfungsformat berücksichtigt** | ✅ | exam_format in Prompt, Lines 25-34 |
| **Deadline-Violations erkannt** | ❌ | **FEHLT: Kein automatischer Check ob genug Zeit** |

**EMPFEHLUNG (Deadlines):**
- Ergänze Pre-Check in app.py vor LLM-Call:
  ```python
  def validate_deadlines_realistic(leistungsnachweise, total_available_hours):
      """Check if there's enough time for all assessments"""
      total_required_hours = sum(ln.get("effort", 3) * 10 for ln in leistungsnachweise)
      if total_required_hours > total_available_hours * 0.8:
          return False, "⚠️ Warnung: Möglicherweise nicht genug Zeit für alle Leistungsnachweise"
      return True, None
  ```

### Kognitive Last & Monotonie

| Check | Status | Details |
|-------|--------|---------|
| **Fächer-Interleaving** | ⚠️ | Über preferences.interleaving steuerbar, aber LLM-Freiheit |
| **Spaced Repetition** | ⚠️ | Über preferences.spacing steuerbar, aber keine explizite Regel |
| **Deep Work Blöcke** | ⚠️ | Über preferences.deep_work steuerbar |
| **Variation der Lernmethoden** | ✅ | exam_format steuert Methoden (Line 25-34 in prompt) |

**RISIKO: Monotone Sessions**
- LLM könnte trotz interleaving=True 5 Tage nur Marketing planen
- FEHLT: Explizite Regel wie "Maximal 2 Tage hintereinander gleiches Modul"

**EMPFEHLUNG (Monotonie):**
- Ergänze in System-Prompt:
  ```
  ANTI-MONOTONIE-REGEL:
  • Wenn interleaving=True: Wechsle Module alle 1-2 Tage
  • Wenn spacing=True: Wiederhole Themen nach 2-3 Tagen (Forgetting Curve)
  • Vermeide >3 Sessions desselben Moduls an einem Tag
  ```

---

## 4. Risiken & Absicherungspunkte

| Risiko | Level | Maßnahme |
|--------|-------|----------|
| **LLM ignoriert freie Zeitfenster** | HIGH | • Prompt verstärken: "NUTZE AUSSCHLIESSLICH diese Slots"<br>• Post-Processing: Validiere dass jede Session in free_slots liegt |
| **Unrealistischer Plan (zu viel Lernzeit)** | MEDIUM | • Pre-Check: total_required_hours vs. available_hours<br>• Warnung wenn >80% Auslastung |
| **Deadline wird übersehen** | HIGH | • Sortiere leistungsnachweise nach deadline in Prompt<br>• Markiere "DRINGEND" für Deadlines <14 Tage |
| **Leere/Fehlerhafte LLM-Response** | MEDIUM | ✅ Bereits abgesichert durch generate_json() Fallbacks |
| **Extreme Zeiträume (>1 Jahr)** | LOW | • Ergänze Validation in planning.py<br>• Max 365 Tage |
| **Ungültige busy_times Format** | LOW | • Ergänze try/except in planning_service.py strptime() |
| **API Key Leak in Logs** | MEDIUM | ✅ Bereits gut: repr(e) statt str(e) in LLM errors |
| **Sehr kurze free_slots (<45min)** | LOW | • LLM-Regel: "Nutze <45min Slots nur wenn nötig"<br>• Gruppiere zu längeren Blöcken |
| **Keine Pausen zwischen Sessions** | MEDIUM | • Ergänze Pausenregeln im System-Prompt<br>• 15 Min nach 90+ Min Sessions |
| **User verliert Vertrauen bei unrealistischem Plan** | HIGH | • Zeige Auslastungs-Warnung<br>• "Plan ist mit 85% Auslastung sehr intensiv" |

### Kritische Absicherungspunkte (Priorität 1)

1. **Slot-Validation nach LLM-Generierung**
   ```python
   def validate_plan_uses_only_free_slots(plan, free_slots):
       """Ensure every study session is within free_slots"""
       for session in plan:
           session_date = session["date"]
           session_start = session["start"]
           session_end = session["end"]
           
           # Check if this session matches any free slot
           matching_slot = next(
               (slot for slot in free_slots 
                if slot["date"].isoformat() == session_date 
                and slot["start"] <= session_start 
                and slot["end"] >= session_end),
               None
           )
           if not matching_slot:
               raise ValueError(f"Session {session} nicht in freien Zeitfenstern!")
   ```

2. **Deadline-Proximity Highlighting**
   - In User-Prompt: Sortiere nach deadline
   - Markiere Deadlines <14 Tage als "❗URGENT"

3. **Workload-Realism-Check**
   ```python
   total_hours_available = sum(slot["hours"] for slot in free_slots)
   total_hours_required = sum(ln["effort"] * 10 for ln in leistungsnachweise)
   utilization = total_hours_required / total_hours_available
   
   if utilization > 0.8:
       st.warning("⚠️ Plan erfordert 80%+ Ihrer freien Zeit. Reduzieren Sie Module oder erhöhen Sie Zeitfenster.")
   ```

---

## 5. Code-Cleanup Empfehlungen

### A) Kommentare hinzufügen (Non-Destructive)

**app.py**
- Line 92: Ergänze Kommentar: `# ASSUMPTION: study_start and study_end are set in session_state`
- Line 103: `# Manual prompt mode: Replace placeholders with actual data`
- Line 198: `# VALIDATION: Ensure plan is non-empty and has correct structure`

**planning.py**
- Line 53: `# OPTIMIZATION: Build absence lookup set for O(1) membership testing`
- Line 104: `# FEATURE: Support for time-limited busy times (valid_from/valid_until)`
- Line 149: `# ALGORITHM: Handle all possible overlap cases between intervals`

**services/llm_service.py**
- Line 106: `# RETRY STRATEGY: Exponential backoff for rate limit errors`
- Line 153: `# FALLBACK: Extract JSON from markdown code blocks if direct parsing fails`

### B) Tote Code-Prüfung

**Analyse:** Keine toten Code-Segmente gefunden ✅
- Alle Funktionen werden verwendet
- Alle imports sind notwendig
- Keine auskommentierten Code-Blöcke

### C) Fehlermeldungen verbessern

**Aktuell (app.py Line 73):**
```python
st.error("❌ API-Schlüssel fehlt. Bitte konfiguriere ihn auf der Einrichtungs-Seite")
```

**Verbessert:**
```python
st.error(
    "❌ API-Schlüssel fehlt.\n"
    "👉 Gehe zu Sidebar → 'Modell Konfiguration' und gib deinen API Key ein.\n"
    "💡 Tipp: OpenAI Keys beginnen mit 'sk-', Gemini Keys sind 39 Zeichen lang."
)
```

---

## 6. Zusammenfassung & Prioritäten

### Kritische Fixes (Priorität 1) ⚠️

1. **Slot-Validation nach LLM** (Risiko: HIGH)
   - Datei: app.py, nach Line 203
   - Validiere dass jede Session in free_slots liegt

2. **Deadline-Realism-Check** (Risiko: HIGH)
   - Datei: app.py, vor LLM-Call
   - Warne wenn nicht genug Zeit für alle Deadlines

3. **Pausenregeln im Prompt** (Risiko: MEDIUM, Pädagogik)
   - Datei: prompts/v4_few_shot_cot.py
   - Ergänze Pausenregeln nach Line 56

### Defensive Guards (Priorität 2) 🛡️

4. **Extreme Zeitraum-Validation** (Risiko: LOW, Performance)
   - Datei: planning.py, Line 50
   - Max 365 Tage Check

5. **strptime Exception-Handling** (Risiko: LOW)
   - Datei: services/planning_service.py, Lines 195-196
   - try/except um datetime.strptime()

6. **LLM Retry Max-Delay Cap** (Risiko: LOW)
   - Datei: services/llm_service.py, Line 117
   - Max 60 Sekunden Delay

### Prompt-Verbesserungen (Priorität 3) 📝

7. **Exam-Format-Enforcement**
   - Datei: prompts/v4_few_shot_cot.py, System-Prompt
   - "ERFINDE KEINE NEUEN exam_formats"

8. **Anti-Monotonie-Regeln**
   - Datei: prompts/v4_few_shot_cot.py, System-Prompt
   - Interleaving-Regeln expliziter

9. **Busy-Time-Kontext verstärken**
   - Datei: prompts/v4_few_shot_cot.py, System-Prompt
   - "BEACHTE ZWINGEND Labels von busy_times"

---

## 7. Testplan (Defensive Testing)

### Edge Cases zu testen:

1. **Leere Eingaben**
   - [ ] leistungsnachweise = []
   - [ ] free_slots = []
   - [ ] absences = [], busy_times = []

2. **Extreme Werte**
   - [ ] Zeitraum: 1 Tag vs. 365 Tage
   - [ ] max_hours_day = 1 vs. 16
   - [ ] Sehr viele Leistungsnachweise (>20)

3. **Ungültige Daten**
   - [ ] study_start > study_end
   - [ ] busy_time start > end
   - [ ] Deadline in Vergangenheit

4. **LLM-Response-Varianten**
   - [ ] JSON mit ```json``` Block
   - [ ] JSON mit ``` Block
   - [ ] Direktes JSON
   - [ ] Ungültiges JSON
   - [ ] Leere Response

---

**Ende der Analyse**

**NEXT STEPS:**
1. Implementiere Priorität-1-Fixes (Slot-Validation, Deadline-Check, Pausen)
2. Ergänze Defensive Guards (Priorität 2)
3. Verbessere Prompts (Priorität 3)
4. Teste Edge Cases
5. Code Review & CodeQL Security Scan
