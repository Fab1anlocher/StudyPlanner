# 🏗️ StudyPlanner Architecture Documentation

## 📋 Table of Contents
- [Overview](#overview)
- [Architecture Principles](#architecture-principles)
- [Layer Documentation](#layer-documentation)
- [Service Layer Details](#service-layer-details)
- [Data Flow](#data-flow)
- [Design Patterns](#design-patterns)
- [Testing Strategy](#testing-strategy)

---

## 🎯 Overview

StudyPlanner follows a **layered architecture** pattern with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                   Presentation Layer                    │
│         (Streamlit UI - app.py & ui/pages/)            │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                   Service Layer                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │ LLM Service        │ Planning Service             │  │
│  ├───────────────────────────────────────────────────┤  │
│  │ Session Manager    │ Export Service               │  │
│  └───────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                   Data Layer                            │
│         (Pydantic Models - models/)                     │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│           Configuration & Constants Layer               │
│      (constants.py, config/settings.py)                 │
└─────────────────────────────────────────────────────────┘
```

**Key Metrics:**
- **Total Lines of Code**: ~3,800 LOC (excluding tests)
- **App.py Reduction**: 1,610 → 427 lines (-73%)
- **Service Layer**: 4 services, 1,039 LOC
- **Test Coverage**: 118 tests, 16.84% overall coverage
  - Export Service: 91.59%
  - Session Manager: 85.96%

---

## 🏛️ Architecture Principles

### 1. **Separation of Concerns**
Each layer has a single, well-defined responsibility:
- **UI Layer**: User interaction & display only
- **Service Layer**: All business logic
- **Data Layer**: Type safety & validation
- **Config Layer**: Constants & settings

### 2. **Dependency Inversion**
- High-level modules (UI) don't depend on low-level modules (LLM APIs)
- Both depend on abstractions (LLMProviderBase)
- Enables easy testing & provider switching

### 3. **Single Responsibility Principle**
- Each module, class, and function has ONE reason to change
- Example: `export_service.py` only handles exports (PDF/iCal/JSON)

### 4. **Don't Repeat Yourself (DRY)**
- Common logic extracted to services
- Session state management centralized in `session_manager.py`
- Time calculations unified in `planning_service.py`

### 5. **Testability First**
- All services designed for unit testing
- Dependencies injected, not hardcoded
- Pure functions where possible

---

## 📚 Layer Documentation

### 🎨 Presentation Layer

**Location**: `app.py`, `ui/pages/`

**Responsibility**: 
- Streamlit UI rendering
- User input collection
- Event handling
- Display formatting

**Key Files**:
```
ui/
├── pages/
│   ├── setup_page.py (714 LOC)    # Setup workflow
│   ├── plan_page.py (344 LOC)     # Plan generation & adjustment
│   └── export_page.py (185 LOC)   # Multi-format export
```

**Design Decisions**:
- **Page Pattern**: Each major workflow is a separate page module
- **No Business Logic**: UI only calls services, never implements logic
- **State-Driven**: All UI state in `st.session_state`, managed via `session_manager`

**Example Flow**:
```python
# setup_page.py - Collecting user input
def render_setup_page():
    # 1. Initialize state (via service)
    session_manager.init_session_state()
    
    # 2. Collect input (UI only)
    ln_type = st.selectbox("Typ", LEISTUNGSNACHWEIS_TYPES)
    
    # 3. Validate & store (via model)
    ln = Leistungsnachweis(type=ln_type, ...)
    
    # 4. Save to session (via service)
    st.session_state.leistungsnachweise.append(ln)
```

---

### 🔧 Service Layer

**Location**: `services/`

**Responsibility**:
- Business logic implementation
- External API interactions
- Complex calculations
- State management

**Key Services**:
```
services/
├── llm_service.py (280 LOC)        # LLM abstraction
├── planning_service.py (254 LOC)   # Time calculations
├── session_manager.py (168 LOC)    # State management
└── export_service.py (337 LOC)     # Export formats
```

**Why Services?**
- **Testability**: Can mock/test without UI
- **Reusability**: Services used by multiple pages
- **Maintainability**: Business logic in one place
- **Performance**: Can optimize independently

---

### 📊 Data Layer

**Location**: `models/`

**Responsibility**:
- Data structure definition
- Type validation
- Schema enforcement
- Data transformation

**Key Models**:
```python
models/
├── leistungsnachweis.py   # Exam/assessment definition
├── study_session.py       # Generated study sessions
├── busy_time.py           # Blocked time slots
├── absence.py             # User absences
└── preferences.py         # User preferences
```

**Pydantic Benefits**:
```python
class Leistungsnachweis(BaseModel):
    type: LeistungsnachweisType  # Enum validation
    title: str = Field(min_length=1)  # Required, non-empty
    date: date  # Type safety
    priority: int = Field(ge=1, le=10)  # Range validation
    
    @field_validator('date')
    @classmethod
    def date_must_be_future(cls, v):
        if v < date.today():
            raise ValueError('Date must be in the future')
        return v
```

**Validation Catches**:
- Invalid date ranges
- Missing required fields
- Type mismatches
- Business rule violations

---

### ⚙️ Configuration Layer

**Location**: `constants.py`, `config/settings.py`

**Responsibility**:
- App-wide constants
- Enum definitions
- Default values
- Environment config

**Key Files**:
```python
# constants.py (247 LOC)
LEISTUNGSNACHWEIS_TYPES = ["Prüfung", "Präsentation", ...]
EXAM_FORMATS = ["Multiple Choice", "Klausur", ...]
WEEKDAY_INDEX_TO_DE = {0: "Montag", 1: "Dienstag", ...}
DATE_FORMAT_SHORT = "%d.%m.%Y"
TIME_FORMAT = "%H:%M"

# config/settings.py (60 LOC)
DEFAULT_PLAN_START_TIME = "08:00"
DEFAULT_PLAN_END_TIME = "22:00"
DEFAULT_SESSION_MIN_DURATION = 60  # minutes
```

**Why Separate?**
- **Single Source of Truth**: Change once, update everywhere
- **Type Safety**: Enums prevent typos
- **Discoverability**: Developers know where to find constants

---

## 🔍 Service Layer Details

### 1. LLM Service (`llm_service.py`)

**Purpose**: Abstract away LLM provider differences

**Design Pattern**: Adapter Pattern

```python
class LLMProviderBase(ABC):
    @abstractmethod
    def generate_plan(self, prompt: str, **kwargs) -> str:
        pass

class OpenAIProvider(LLMProviderBase):
    def generate_plan(self, prompt: str, **kwargs) -> str:
        # OpenAI-specific implementation
        response = self.client.chat.completions.create(...)
        return response.choices[0].message.content

class GeminiProvider(LLMProviderBase):
    def generate_plan(self, prompt: str, **kwargs) -> str:
        # Gemini-specific implementation
        response = self.model.generate_content(...)
        return response.text
```

**Benefits**:
- ✅ Switch providers without changing UI code
- ✅ Easy to add new providers (Anthropic, Cohere, etc.)
- ✅ Testable with mock providers
- ✅ Retry logic centralized

**Key Methods**:
- `generate_plan()`: Main LLM call with retry logic
- `_create_openai_provider()`: Factory for OpenAI
- `_create_gemini_provider()`: Factory for Gemini

---

### 2. Planning Service (`planning_service.py`)

**Purpose**: Calculate available time slots for study sessions

**Core Algorithm**:
```python
def calculate_free_slots_from_session(
    plan_start_date: date,
    plan_end_date: date,
    start_time: time,
    end_time: time,
    busy_times: List[BusyTime],
    absences: List[Absence]
) -> List[FreeSlot]:
    """
    Algorithm:
    1. Generate all days in range
    2. Filter out absences
    3. For each day:
       - Start with [start_time, end_time] as free
       - Subtract all busy_times for that day
       - Split into remaining free slots
    4. Return list of FreeSlot objects
    """
```

**Key Functions**:
- `calculate_free_slots_from_session()`: Main calculation
- `_subtract_busy_time()`: Remove busy periods from free slots
- `_time_to_minutes()`: Helper for time arithmetic

**Performance**:
- Time Complexity: O(d × b) where d=days, b=busy_times
- Space Complexity: O(f) where f=free_slots

---

### 3. Session Manager (`session_manager.py`)

**Purpose**: Centralize Streamlit session state management

**Key Functions**:
```python
def init_session_state():
    """Initialize all session state variables with defaults"""
    
def validate_setup_complete() -> bool:
    """Check if user completed all setup steps"""
    
def get_setup_summary() -> dict:
    """Return summary of user's setup configuration"""
    
def reset_plan_data():
    """Clear generated plan data (keep setup)"""
    
def has_plan() -> bool:
    """Check if a plan exists in session"""
```

**State Structure**:
```python
st.session_state = {
    # Setup Data
    'leistungsnachweise': List[Leistungsnachweis],
    'busy_times': List[BusyTime],
    'absences': List[Absence],
    'preferences': UserPreferences,
    
    # Plan Data
    'study_sessions': List[StudySession],
    'llm_response_raw': str,
    
    # UI State
    'current_page': str,
    'setup_complete': bool
}
```

**Why Centralized?**
- ✅ Prevents state-related bugs
- ✅ Consistent initialization
- ✅ Easy to debug state issues
- ✅ Single source of truth

---

### 4. Export Service (`export_service.py`)

**Purpose**: Generate exports in multiple formats

**Supported Formats**:

#### 📄 PDF Export
```python
def create_pdf_export(
    study_sessions: List[StudySession],
    preferences: UserPreferences
) -> bytes:
    """
    Creates visual study plan with:
    - Header with logo & title
    - Summary statistics
    - Weekly calendar view
    - Session list with details
    """
```

#### 📅 iCalendar Export
```python
def create_ical_export(
    study_sessions: List[StudySession]
) -> str:
    """
    Creates .ics file for calendar import:
    - VEVENT for each study session
    - Reminders (30 min before)
    - Color coding by priority
    - Works with Google/Outlook/Apple Calendar
    """
```

#### 💾 JSON Export
```python
def create_json_export(
    study_sessions: List[StudySession],
    leistungsnachweise: List[Leistungsnachweis],
    preferences: UserPreferences
) -> str:
    """
    Complete backup export:
    - All input data
    - All generated sessions
    - Configuration
    - Re-importable
    """
```

**Statistics Function**:
```python
def get_plan_statistics(
    study_sessions: List[StudySession]
) -> dict:
    """
    Returns:
    - total_sessions: int
    - total_hours: float
    - avg_session_duration: float
    - sessions_per_ln: dict
    - priority_distribution: dict
    """
```

---

## 🔄 Data Flow

### Complete User Journey

```
┌─────────────────────────────────────────────────────────┐
│ 1. SETUP PHASE (setup_page.py)                         │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
    User Input → Pydantic Validation → Session State
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ 2. PLANNING PHASE (plan_page.py)                       │
└─────────────────────────────────────────────────────────┘
                         │
    ┌────────────────────┼────────────────────┐
    ▼                    ▼                    ▼
Planning Service  →  LLM Service  →  Session State
(Free Slots)         (AI Plan)        (Study Sessions)
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ 3. EXPORT PHASE (export_page.py)                       │
└─────────────────────────────────────────────────────────┘
                         │
    ┌────────────────────┼────────────────────┐
    ▼                    ▼                    ▼
PDF Export          iCal Export          JSON Export
```

### Example: Generating a Study Plan

**Step 1: User completes setup**
```python
# setup_page.py
ln = Leistungsnachweis(
    type="Prüfung",
    title="Marketing Klausur",
    date=date(2024, 2, 15),
    priority=8
)
st.session_state.leistungsnachweise.append(ln)
```

**Step 2: User clicks "Plan generieren"**
```python
# plan_page.py calls planning_service
free_slots = planning_service.calculate_free_slots_from_session(
    plan_start_date=st.session_state.preferences.plan_start_date,
    plan_end_date=st.session_state.preferences.plan_end_date,
    start_time=st.session_state.preferences.start_time,
    end_time=st.session_state.preferences.end_time,
    busy_times=st.session_state.busy_times,
    absences=st.session_state.absences
)
```

**Step 3: Build prompt and call LLM**
```python
# plan_page.py calls llm_service
llm_provider = llm_service.OpenAIProvider(api_key=...)
prompt = build_prompt(
    leistungsnachweise=st.session_state.leistungsnachweise,
    free_slots=free_slots,
    preferences=st.session_state.preferences
)
llm_response = llm_provider.generate_plan(prompt)
```

**Step 4: Parse and validate response**
```python
# plan_page.py validates with Pydantic
study_sessions = [
    StudySession(**session_data)
    for session_data in parsed_response
]
st.session_state.study_sessions = study_sessions
```

**Step 5: User exports plan**
```python
# export_page.py calls export_service
pdf_bytes = export_service.create_pdf_export(
    study_sessions=st.session_state.study_sessions,
    preferences=st.session_state.preferences
)
st.download_button("Download PDF", pdf_bytes, "studyplan.pdf")
```

---

## 🎨 Design Patterns

### 1. **Adapter Pattern** (LLM Service)
**Problem**: Multiple LLM providers with different APIs  
**Solution**: Unified interface via `LLMProviderBase`

```python
# Before (tightly coupled)
if provider == "openai":
    response = openai.ChatCompletion.create(...)
elif provider == "gemini":
    response = genai.GenerativeModel(...).generate_content(...)

# After (loosely coupled)
provider = get_llm_provider()  # Returns LLMProviderBase
response = provider.generate_plan(prompt)
```

### 2. **Factory Pattern** (LLM Provider Creation)
**Problem**: Complex provider initialization  
**Solution**: Factory methods hide complexity

```python
def _create_openai_provider(api_key: str, model: str):
    client = OpenAI(api_key=api_key)
    return OpenAIProvider(client, model)
```

### 3. **Repository Pattern** (Session Manager)
**Problem**: Direct access to session state scattered everywhere  
**Solution**: Centralized state access via manager

```python
# Before
if 'study_sessions' not in st.session_state:
    st.session_state.study_sessions = []

# After
session_manager.init_session_state()
```

### 4. **Strategy Pattern** (Export Formats)
**Problem**: Multiple export formats with different logic  
**Solution**: Separate functions for each strategy

```python
# Export service offers multiple strategies
export_service.create_pdf_export(...)
export_service.create_ical_export(...)
export_service.create_json_export(...)
```

### 5. **Dependency Injection** (Testing)
**Problem**: Hard to test code with hardcoded dependencies  
**Solution**: Inject dependencies as parameters

```python
# Testable design
def generate_plan(
    llm_provider: LLMProviderBase,  # Can inject mock
    planning_service: PlanningService  # Can inject mock
):
    ...
```

---

## 🧪 Testing Strategy

### Test Pyramid

```
        ┌──────────┐
        │    E2E   │  ← Future: Selenium/Playwright
        │  Tests   │
        └──────────┘
      ┌──────────────┐
      │ Integration  │  ← Future: API + DB Tests
      │    Tests     │
      └──────────────┘
    ┌──────────────────┐
    │   Unit Tests     │  ← Current Focus (118 tests)
    │  (pytest)        │
    └──────────────────┘
```

### Current Coverage

| Module | Tests | Coverage | Status |
|--------|-------|----------|--------|
| `export_service.py` | 32 | 91.59% | ✅ Excellent |
| `session_manager.py` | 15 | 85.96% | ✅ Good |
| `constants.py` | 19 | 100% | ✅ Perfect |
| `models/*` | 32 | ~60% | ⚠️ Needs work |
| `llm_service.py` | 10 | ~40% | ⚠️ Needs work |
| `planning_service.py` | 10 | ~45% | ⚠️ Needs work |

**Total**: 118 tests, 62 passing, 16.84% overall coverage

### Test Structure

```python
# tests/conftest.py - Shared fixtures
@pytest.fixture
def sample_leistungsnachweis():
    return Leistungsnachweis(
        type="Prüfung",
        title="Test Exam",
        date=date.today() + timedelta(days=30),
        priority=5
    )

# tests/test_export_service.py
def test_create_pdf_export(sample_study_sessions, sample_preferences):
    pdf_bytes = export_service.create_pdf_export(
        study_sessions=sample_study_sessions,
        preferences=sample_preferences
    )
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes[:4] == b'%PDF'  # PDF magic number
```

### Testing Best Practices

1. **Arrange-Act-Assert (AAA)** pattern in all tests
2. **Fixtures** for reusable test data (`conftest.py`)
3. **Mocking** external APIs (OpenAI, Gemini)
4. **Parametrize** for testing multiple scenarios
5. **Coverage goals**: 80%+ for services, 60%+ overall

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific module
pytest tests/test_export_service.py -v

# Watch mode (with pytest-watch)
ptw
```

---

## 🚀 Performance Considerations

### 1. **LLM API Calls**
- **Bottleneck**: External API latency (2-10s)
- **Optimization**: 
  - Retry logic with exponential backoff
  - Cache responses in session state
  - Use faster models for iterations (gpt-4o-mini vs gpt-4o)

### 2. **Free Slot Calculation**
- **Complexity**: O(days × busy_times)
- **Optimization**:
  - Pre-filter absences by date range
  - Sort busy times once
  - Early exit for blocked days

### 3. **PDF Generation**
- **Bottleneck**: fpdf2 rendering (0.5-2s for 50 sessions)
- **Optimization**:
  - Generate on-demand (not pre-cached)
  - Limit calendar view to 4 weeks
  - Compress images

### 4. **Session State**
- **Issue**: Large session state (100+ sessions) can slow reruns
- **Optimization**:
  - Use `@st.cache_data` for expensive computations
  - Clear unused keys with `reset_plan_data()`
  - Avoid storing raw LLM responses long-term

---

## 📈 Future Architecture Improvements

### Phase 11: Database Layer (Deferred)
- **Goal**: Persistent storage of plans
- **Stack**: SQLite + SQLAlchemy
- **Benefits**: Multi-user support, plan history

### Phase 12: API Layer
- **Goal**: RESTful API for headless usage
- **Stack**: FastAPI
- **Benefits**: Mobile app integration, automation

### Phase 13: Background Jobs
- **Goal**: Async plan generation
- **Stack**: Celery + Redis
- **Benefits**: Non-blocking UI, scheduled replanning

### Phase 14: Authentication
- **Goal**: User accounts & plan privacy
- **Stack**: Streamlit Auth + JWT
- **Benefits**: Multi-tenancy, personalization

---

## 🔧 Maintenance Guidelines

### Adding a New Service

1. Create file in `services/` with clear responsibility
2. Define public API (exported functions)
3. Write unit tests in `tests/test_<service>.py`
4. Import in `services/__init__.py`
5. Document in this file

### Adding a New Model

1. Create Pydantic model in `models/`
2. Add field validators for business rules
3. Write tests for validation logic
4. Use in services, not directly in UI
5. Export from `models/__init__.py`

### Modifying UI

1. **Never** add business logic to UI files
2. Extract logic to appropriate service
3. Use session manager for state access
4. Keep UI files < 500 LOC
5. Test manually with different inputs

### Debugging Checklist

- [ ] Check session state with `st.session_state`
- [ ] Verify Pydantic validation errors
- [ ] Check LLM response format
- [ ] Test with minimal data first
- [ ] Use `st.write()` for debugging
- [ ] Check browser console for JS errors

---

## 📚 References

- **Streamlit Docs**: https://docs.streamlit.io/
- **Pydantic Docs**: https://docs.pydantic.dev/
- **OpenAI API**: https://platform.openai.com/docs/
- **Google Gemini API**: https://ai.google.dev/docs
- **pytest Docs**: https://docs.pytest.org/

---

**Last Updated**: Phase 10 (Documentation & Cleanup)  
**Maintained By**: StudyPlanner Team  
**Architecture Version**: 2.0 (Post-Refactoring)
