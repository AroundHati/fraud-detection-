"""
Google Gemini provider for the FraudShield LLM layer.

Wraps the ``google-generativeai`` SDK behind the ``BaseLLMProvider``
interface.  Configuration is loaded entirely from environment variables
— no credentials are ever hardcoded.

Environment Variables
---------------------
``GEMINI_API_KEY``
    Google AI Studio API key.  Required.
``GEMINI_MODEL``
    Model identifier (default ``"gemini-1.5-flash"``).
``GEMINI_TEMPERATURE``
    Sampling temperature override (default ``0.3``).
``GEMINI_MAX_TOKENS``
    Maximum tokens per completion (default ``4096``).

Design
------
- The ``google-generativeai`` import is lazy — this module is safe to
  import even when the SDK is not installed; the error surfaces only
  when ``GeminiProvider`` is instantiated.
- Exponential back-off with jitter is applied on transient failures
  (rate limits, connection errors).
- Structured JSON output is requested via Gemini's native JSON mode
  where the SDK supports it.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import time
from typing import Any, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

from ml.llm.base import BaseLLMProvider
from ml.llm.exceptions import (
    LLMConfigError,
    LLMConnectionError,
    LLMProviderError,
    LLMRateLimitError,
    LLMResponseError,
    LLMResponseValidationError,
)
from ml.llm.parser import ResponseParser
from ml.llm.schemas import LLMConfig

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


def _load_config_from_env() -> LLMConfig:
    """Build an ``LLMConfig`` from environment variables.

    Returns
    -------
    LLMConfig
        Configuration populated from ``GEMINI_*`` env vars with
        safe defaults.

    Raises
    ------
    LLMConfigError
        If ``GEMINI_API_KEY`` is not set.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise LLMConfigError(
            "GEMINI_API_KEY environment variable is not set. "
            "Set it to your Google AI Studio API key.",
            provider="gemini",
        )

    return LLMConfig(
        provider="gemini",
        model=os.environ.get("GEMINI_MODEL", "gemini-1.5-flash"),
        api_key=api_key,
        temperature=float(os.environ.get("GEMINI_TEMPERATURE", "0.3")),
        max_tokens=int(os.environ.get("GEMINI_MAX_TOKENS", "4096")),
        timeout=int(os.environ.get("GEMINI_TIMEOUT", "60")),
        max_retries=int(os.environ.get("GEMINI_MAX_RETRIES", "3")),
    )


class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider implementation.

    Uses the ``google-generativeai`` SDK for text generation with
    automatic retry, exponential back-off, and structured JSON output.

    Parameters
    ----------
    config : LLMConfig, optional
        Provider configuration.  If ``None``, configuration is loaded
        from environment variables via ``_load_config_from_env()``.

    Examples
    --------
    >>> provider = GeminiProvider()  # from env vars
    >>> response = await provider.generate("Analyse this claim data...")
    >>> structured = await provider.generate_structured(
    ...     "Investigate provider PRV-001",
    ...     InvestigationLLMResponse,
    ... )
    """

    def __init__(self, config: Optional[LLMConfig] = None) -> None:
        if config is None:
            config = _load_config_from_env()
        super().__init__(config)
        self._genai: Any = None
        self._model: Any = None

    # ------------------------------------------------------------------
    # Lazy SDK initialisation
    # ------------------------------------------------------------------

    def _ensure_sdk(self) -> None:
        """Lazily import and configure the ``google-generativeai`` SDK.

        Raises
        ------
        LLMConfigError
            If the SDK is not installed.
        """
        if self._model is not None:
            return

        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise LLMConfigError(
                "google-generativeai package is not installed. "
                "Install it with: pip install google-generativeai",
                provider="gemini",
                model=self.model,
                cause=exc,
            ) from exc

        self._genai = genai
        genai.configure(api_key=self._config.api_key)
        self._model = genai.GenerativeModel(self._config.model)
        logger.info(
            "Gemini SDK initialised — model=%s",
            self._config.model,
        )

    # ------------------------------------------------------------------
    # Retry helpers
    # ------------------------------------------------------------------

    async def _retry_with_backoff(
        self,
        coro_factory,
        *,
        max_retries: Optional[int] = None,
    ) -> Any:
        """Execute an async callable with exponential back-off.

        Parameters
        ----------
        coro_factory : callable
            A zero-argument callable that returns a new coroutine each
            time it is called (e.g. a lambda wrapping an await).
        max_retries : int, optional
            Maximum retry count.  Defaults to ``config.max_retries``.

        Returns
        -------
        Any
            The result of the coroutine on success.

        Raises
        ------
        LLMRateLimitError
            If all retries are exhausted on a rate-limit error.
        LLMConnectionError
            If all retries are exhausted on a connection error.
        LLMProviderError
            If all retries are exhausted on any other provider error.
        """
        retries = max_retries if max_retries is not None else self._config.max_retries
        last_exc: Optional[Exception] = None

        for attempt in range(retries + 1):
            try:
                return await coro_factory()
            except Exception as exc:
                last_exc = exc
                exc_str = str(exc).lower()

                if attempt == retries:
                    break

                is_rate_limit = (
                    "429" in exc_str
                    or "rate" in exc_str
                    or "quota" in exc_str
                    or "RESOURCE_EXHAUSTED" in str(exc)
                )
                is_connection = (
                    "timeout" in exc_str
                    or "connect" in exc_str
                    or "network" in exc_str
                    or "unreachable" in exc_str
                )

                if not (is_rate_limit or is_connection):
                    break

                delay = self._config.retry_base_delay * (2 ** attempt)
                jitter = random.uniform(0, delay * 0.5)
                sleep_time = delay + jitter

                logger.warning(
                    "Attempt %d/%d failed (%s) — retrying in %.1fs: %s",
                    attempt + 1,
                    retries + 1,
                    "rate_limit" if is_rate_limit else "connection",
                    sleep_time,
                    exc,
                )
                await asyncio.sleep(sleep_time)

        if last_exc is not None:
            exc_str = str(last_exc).lower()
            is_rate_limit = (
                "429" in exc_str
                or "rate" in exc_str
                or "quota" in exc_str
                or "RESOURCE_EXHAUSTED" in str(last_exc)
            )
            if is_rate_limit:
                raise LLMRateLimitError(
                    f"Gemini rate limit exceeded after {retries + 1} attempts: {last_exc}",
                    provider="gemini",
                    model=self.model,
                    cause=last_exc,
                ) from last_exc
            is_connection = (
                "timeout" in exc_str
                or "connect" in exc_str
                or "network" in exc_str
                or "unreachable" in exc_str
            )
            if is_connection:
                raise LLMConnectionError(
                    f"Gemini connection failed after {retries + 1} attempts: {last_exc}",
                    provider="gemini",
                    model=self.model,
                    cause=last_exc,
                ) from last_exc
            raise LLMProviderError(
                f"Gemini request failed after {retries + 1} attempts: {last_exc}",
                provider="gemini",
                model=self.model,
                cause=last_exc,
            ) from last_exc

        raise LLMProviderError(
            "Unexpected retry loop exit",
            provider="gemini",
            model=self.model,
        )

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Send a prompt and return the raw text completion.

        Parameters
        ----------
        prompt : str
            User-facing prompt string.
        system_prompt : str, optional
            System-level instruction prefix.
        temperature : float, optional
            Override the default sampling temperature.
        max_tokens : int, optional
            Override the default maximum token count.

        Returns
        -------
        str
            The LLM response as plain text.

        Raises
        ------
        LLMResponseError
            If the response is empty.
        """
        self._ensure_sdk()

        effective_temp = temperature if temperature is not None else self._config.temperature
        effective_max = max_tokens if max_tokens is not None else self._config.max_tokens

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        generation_config = self._genai.types.GenerationConfig(
            temperature=effective_temp,
            max_output_tokens=effective_max,
        )

        logger.debug(
            "Gemini generate() — model=%s temp=%.2f max_tokens=%d prompt_len=%d",
            self.model,
            effective_temp,
            effective_max,
            len(full_prompt),
        )

        async def _do_call():
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: self._model.generate_content(
                    full_prompt,
                    generation_config=generation_config,
                ),
            )

        response = await self._retry_with_backoff(_do_call)

        try:
            text = response.text
        except (AttributeError, ValueError) as exc:
            raise LLMResponseError(
                f"Gemini returned an empty or unusable response: {exc}",
                provider="gemini",
                model=self.model,
                cause=exc,
            ) from exc

        if not text or not text.strip():
            raise LLMResponseError(
                "Gemini returned an empty response",
                provider="gemini",
                model=self.model,
            )

        logger.debug(
            "Gemini generate() — response_len=%d",
            len(text),
        )
        return text.strip()

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        *,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> T:
        """Generate a response and validate it against a Pydantic model.

        Requests JSON output from Gemini, parses the response, and
        validates it against the provided Pydantic model class.

        Parameters
        ----------
        prompt : str
            User-facing prompt string.
        response_model : Type[T]
            Pydantic model class to validate the response against.
        system_prompt : str, optional
            System-level instruction prefix.
        temperature : float, optional
            Override the default sampling temperature.
        max_tokens : int, optional
            Override the default maximum token count.

        Returns
        -------
        T
            A validated instance of *response_model*.

        Raises
        ------
        LLMResponseValidationError
            If the response fails Pydantic validation.
        LLMResponseError
            If the raw response cannot be parsed.
        """
        json_instruction = (
            "\n\nIMPORTANT: Respond ONLY with valid JSON. "
            "Do not include any markdown, code fences, or text outside the JSON object."
        )

        full_prompt = prompt + json_instruction

        raw_response = await self.generate(
            full_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        try:
            parsed = ResponseParser.parse_json(raw_response)
        except Exception as exc:
            raise LLMResponseError(
                f"Failed to parse Gemini JSON response: {exc}",
                provider="gemini",
                model=self.model,
                cause=exc,
            ) from exc

        try:
            validated = response_model(**parsed)
        except ValidationError as exc:
            raise LLMResponseValidationError(
                f"Response validation failed for {response_model.__name__}: {exc}",
                provider="gemini",
                model=self.model,
                validation_errors=exc.errors(),
                raw_response=raw_response,
                cause=exc,
            ) from exc

        logger.debug(
            "Gemini generate_structured() — model=%s validated successfully",
            response_model.__name__,
        )
        return validated

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        """Verify that Gemini is reachable and configured correctly.

        Sends a minimal prompt and checks for a valid response.

        Returns
        -------
        bool
            ``True`` if Gemini responds successfully, ``False`` otherwise.
        """
        try:
            self._ensure_sdk()
            result = await self.generate(
                "Respond with exactly: OK",
                temperature=0.0,
                max_tokens=10,
            )
            ok = bool(result and "OK" in result.upper())
            if ok:
                logger.info("Gemini health check passed")
            else:
                logger.warning(
                    "Gemini health check — unexpected response: %s",
                    result[:100],
                )
            return ok
        except Exception as exc:
            logger.warning("Gemini health check failed — %s", exc)
            return False
