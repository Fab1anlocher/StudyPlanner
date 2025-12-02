"""
Service Layer für Business Logic
Trennt API-Integration, Planning-Logic und Session-Management von UI
"""

from .llm_service import (
    LLMProviderBase,
    OpenAIProvider,
    GeminiProvider,
    get_llm_provider,
    LLMError,
    LLMRateLimitError,
    LLMResponseError,
)

from .planning_service import (
    calculate_free_slots_from_session,
    get_total_available_hours,
    get_available_days_count,
)

from .session_manager import (
    init_session_state,
    validate_setup_complete,
    get_setup_summary,
    get_active_learning_strategies,
    reset_plan_data,
    has_plan,
)

from .export_service import (
    create_pdf_export,
    create_excel_export,
    get_plan_statistics,
)

__all__ = [
    # LLM Service
    "LLMProviderBase",
    "OpenAIProvider",
    "GeminiProvider",
    "get_llm_provider",
    "LLMError",
    "LLMRateLimitError",
    "LLMResponseError",
    # Planning Service
    "calculate_free_slots_from_session",
    "get_total_available_hours",
    "get_available_days_count",
    # Session Manager
    "init_session_state",
    "validate_setup_complete",
    "get_setup_summary",
    "get_active_learning_strategies",
    "reset_plan_data",
    "has_plan",
    # Export Service
    "create_pdf_export",
    "create_ical_export",
    "create_json_export",
    "get_plan_statistics",
]
