"""
LLM Service Layer mit Adapter Pattern
Abstrahiert OpenAI, Gemini und zukünftige LLM-Provider
"""

from abc import ABC, abstractmethod
from typing import Optional, Any
import json
import time

from openai import OpenAI, RateLimitError as OpenAIRateLimitError
import google.generativeai as genai

from config import settings
from constants import MAX_RETRY_DELAY_SECONDS


# ════════════════════════════════════════════════════════════════
# CUSTOM EXCEPTIONS
# ════════════════════════════════════════════════════════════════


class LLMError(Exception):
    """Base exception für LLM-Fehler"""

    pass


class LLMRateLimitError(LLMError):
    """Rate Limit erreicht"""

    pass


class LLMResponseError(LLMError):
    """Fehler beim Parsen der LLM-Response"""

    pass


# ════════════════════════════════════════════════════════════════
# ABSTRACT BASE CLASS
# ════════════════════════════════════════════════════════════════


class LLMProviderBase(ABC):
    """
    Abstract Base Class für LLM-Provider
    Implementiert gemeinsame Funktionalität und definiert Interface
    """

    def __init__(self, api_key: str, model: str):
        """
        Args:
            api_key: API-Schlüssel für den Provider
            model: Model-Name (z.B. "gpt-4o-mini", "gemini-1.5-flash")
        """
        self.api_key = api_key
        self.model = model

    @abstractmethod
    def _generate_raw(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """
        Interne Methode für rohe API-Calls
        Muss von Subklassen implementiert werden

        Args:
            system_prompt: System-Prompt (Rolle & Regeln)
            user_prompt: User-Prompt (Aufgabe & Daten)
            **kwargs: Provider-spezifische Parameter

        Returns:
            Raw response text
        """
        pass

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        retry_attempts: int = 3,
        retry_delay: float = 1.0,
    ) -> str:
        """
        Generiert Response mit automatischem Retry bei Rate Limits

        Args:
            system_prompt: System-Prompt
            user_prompt: User-Prompt
            temperature: Temperature (0.0-1.0), default aus settings
            max_tokens: Max tokens, default aus settings
            retry_attempts: Anzahl Retry-Versuche bei Rate Limit
            retry_delay: Delay zwischen Retries (exponential backoff)

        Returns:
            Response-Text

        Raises:
            LLMRateLimitError: Wenn Rate Limit nach allen Retries noch aktiv
            LLMError: Bei anderen Fehlern
        """
        temperature = temperature or settings.LLM_TEMPERATURE
        max_tokens = max_tokens or settings.LLM_MAX_TOKENS

        for attempt in range(retry_attempts):
            try:
                return self._generate_raw(
                    system_prompt,
                    user_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except LLMRateLimitError as e:
                if attempt < retry_attempts - 1:
                    # DEFENSIVE GUARD: Exponential backoff with max cap to prevent excessive waits
                    delay = retry_delay * (2**attempt)
                    delay = min(delay, MAX_RETRY_DELAY_SECONDS)
                    time.sleep(delay)
                    continue
                else:
                    raise  # Re-raise nach letztem Versuch
            except Exception as e:
                # Andere Fehler sofort werfen
                raise LLMError(f"LLM API Error: {repr(e)}") from e

        raise LLMError("Unerwarteter Fehler in generate()")

    def generate_json(self, system_prompt: str, user_prompt: str, **kwargs) -> Any:
        """
        Generiert Response und parsed als JSON
        Extrahiert automatisch JSON aus Markdown-Codeblocks
        
        FALLBACK STRATEGY: Try multiple parsing approaches
        1. Direct JSON parsing
        2. Extract from ```json``` blocks
        3. Extract from generic ``` blocks

        Args:
            system_prompt: System-Prompt
            user_prompt: User-Prompt
            **kwargs: Parameter für generate()

        Returns:
            Parsed JSON (dict oder list)

        Raises:
            LLMResponseError: Wenn Response kein valides JSON ist
        """
        response_text = self.generate(system_prompt, user_prompt, **kwargs)

        # Versuche direktes Parsing
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # FALLBACK: Versuche JSON aus Markdown-Codeblock zu extrahieren
        if "```json" in response_text:
            start_idx = response_text.find("```json") + 7
            end_idx = response_text.find("```", start_idx)
            if end_idx > start_idx:
                json_content = response_text[start_idx:end_idx].strip()
                try:
                    return json.loads(json_content)
                except json.JSONDecodeError:
                    pass

        # FALLBACK: Versuche allgemeinen Codeblock
        if "```" in response_text:
            start_idx = response_text.find("```") + 3
            end_idx = response_text.find("```", start_idx)
            if end_idx > start_idx:
                json_content = response_text[start_idx:end_idx].strip()
                try:
                    return json.loads(json_content)
                except json.JSONDecodeError:
                    pass

        # Kein valides JSON gefunden
        raise LLMResponseError(
            f"Response ist kein valides JSON. Erste 200 Zeichen: {response_text[:200]}"
        )


# ════════════════════════════════════════════════════════════════
# OPENAI PROVIDER
# ════════════════════════════════════════════════════════════════


class OpenAIProvider(LLMProviderBase):
    """OpenAI API Provider (GPT-4, GPT-3.5, etc.)"""

    def __init__(self, api_key: str, model: str):
        super().__init__(api_key, model)
        self.client = OpenAI(api_key=api_key)

    def _generate_raw(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """
        OpenAI Chat Completion API Call

        Raises:
            LLMRateLimitError: Bei Rate Limit
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=kwargs.get("temperature", settings.LLM_TEMPERATURE),
                max_tokens=kwargs.get("max_tokens", settings.LLM_MAX_TOKENS),
            )

            return response.choices[0].message.content.strip()

        except OpenAIRateLimitError as e:
            raise LLMRateLimitError(f"OpenAI Rate Limit: {repr(e)}") from e
        except Exception as e:
            raise LLMError(f"OpenAI API Error: {repr(e)}") from e


# ════════════════════════════════════════════════════════════════
# GEMINI PROVIDER
# ════════════════════════════════════════════════════════════════


class GeminiProvider(LLMProviderBase):
    """Google Gemini API Provider"""

    def __init__(self, api_key: str, model: str):
        super().__init__(api_key, model)
        genai.configure(api_key=api_key)
        self.model_instance = genai.GenerativeModel(model)

    def _generate_raw(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """
        Gemini Generate Content API Call

        Note: Gemini hat kein separates system_prompt Konzept,
        daher kombinieren wir beide Prompts
        """
        try:
            # Kombiniere system und user prompt
            combined_prompt = f"{system_prompt}\n\n{user_prompt}"

            response = self.model_instance.generate_content(
                combined_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=kwargs.get("temperature", settings.LLM_TEMPERATURE),
                    max_output_tokens=kwargs.get("max_tokens", settings.LLM_MAX_TOKENS),
                ),
            )

            return response.text.strip()

        except Exception as e:
            error_msg = str(e).lower()

            # Check für Rate Limit (Gemini wirft generische Exceptions)
            if "quota" in error_msg or "rate" in error_msg or "limit" in error_msg:
                raise LLMRateLimitError(f"Gemini Rate Limit: {repr(e)}") from e

            raise LLMError(f"Gemini API Error: {repr(e)}") from e


# ════════════════════════════════════════════════════════════════
# FACTORY FUNCTION
# ════════════════════════════════════════════════════════════════


def get_llm_provider(provider: str, api_key: str, model: str) -> LLMProviderBase:
    """
    Factory Function für LLM-Provider

    Args:
        provider: Provider-Name ("OpenAI" oder "Google Gemini")
        api_key: API-Schlüssel
        model: Model-Name

    Returns:
        LLMProviderBase instance

    Raises:
        ValueError: Bei unbekanntem Provider

    Example:
        >>> llm = get_llm_provider("OpenAI", "sk-...", "gpt-4o-mini")
        >>> response = llm.generate("You are...", "Generate...")
    """
    provider_lower = provider.lower()

    if "openai" in provider_lower:
        return OpenAIProvider(api_key, model)
    elif "gemini" in provider_lower or "google" in provider_lower:
        return GeminiProvider(api_key, model)
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider}. "
            f"Supported: 'OpenAI', 'Google Gemini'"
        )
