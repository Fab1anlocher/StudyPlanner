"""
Konfiguration für Prompt-Versionen
Wähle hier die aktive Prompt-Version aus
"""

# ════════════════════════════════════════════════════════════════
# AKTIVE PROMPT-VERSION HIER ÄNDERN
# ════════════════════════════════════════════════════════════════
# Optionen: "v1_zero_shot", "v2_few_shot", "v3_chain_of_thought", "v4_few_shot_cot"

ACTIVE_PROMPT_VERSION = "v1_zero_shot"


# ════════════════════════════════════════════════════════════════
# VERFÜGBARE VERSIONEN (für UI-Auswahl)
# ════════════════════════════════════════════════════════════════

AVAILABLE_VERSIONS = {
    "v1_zero_shot": "V1: Zero-Shot (Baseline)",
    "v2_few_shot": "V2: Few-Shot (mit Beispielen)",
    "v3_chain_of_thought": "V3: Chain-of-Thought (Reasoning)",
    "v4_few_shot_cot": "V4: Few-Shot + CoT (Hybrid)"
}


def get_active_prompts():
    """
    Gibt die aktive Prompt-Version zurück.
    
    Returns:
        tuple: (get_system_prompt, build_user_prompt) Funktionen
    """
    if ACTIVE_PROMPT_VERSION == "v1_zero_shot":
        from prompts.v1_zero_shot import get_system_prompt, build_user_prompt
    elif ACTIVE_PROMPT_VERSION == "v2_few_shot":
        from prompts.v2_few_shot import get_system_prompt, build_user_prompt
    elif ACTIVE_PROMPT_VERSION == "v3_chain_of_thought":
        from prompts.v3_chain_of_thought import get_system_prompt, build_user_prompt
    elif ACTIVE_PROMPT_VERSION == "v4_few_shot_cot":
        from prompts.v4_few_shot_cot import get_system_prompt, build_user_prompt
    else:
        raise ValueError(f"Unknown prompt version: {ACTIVE_PROMPT_VERSION}")
    
    return get_system_prompt, build_user_prompt


def set_active_version(version: str):
    """
    Setzt die aktive Prompt-Version (für Session State).
    
    Args:
        version (str): Name der Version (z.B. "v2_few_shot")
    """
    global ACTIVE_PROMPT_VERSION
    if version in AVAILABLE_VERSIONS:
        ACTIVE_PROMPT_VERSION = version
    else:
        raise ValueError(f"Invalid version: {version}")
