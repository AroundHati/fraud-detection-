"""
Reusable LLM client for the FraudShield agent framework.

Encapsulates all communication with language-model backends so that
individual agents never import an SDK directly.  Supports synchronous
generation, JSON-mode generation, and streaming.
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator, Optional

logger = logging.getLogger(__name__)


class LLMClientError(Exception):
    """Raised when an LLM API call fails after exhausting retries."""


class LLMClient:
    """Stateless client that wraps an LLM provider SDK.

    Attributes:
        provider: Backend identifier (e.g. ``"openai"``).
        model: Model identifier used for every request.
        temperature: Sampling temperature.
        max_tokens: Maximum completion length.
        timeout: Per-request timeout in seconds.
        max_retries: Number of automatic retries on transient failures.
    """

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        timeout: int = 60,
        max_retries: int = 3,
        api_key: Optional[str] = None,
    ) -> None:
        """Initialise the LLM client.

        Args:
            provider: Backend identifier.
            model: Model to use for completions.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens per response.
            timeout: Timeout per request in seconds.
            max_retries: Retry count for transient failures.
            api_key: Optional API key override.  When *None* the provider
                SDK falls back to its default credential chain.
        """
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        self._api_key = api_key
        self._client: Any = None  # Lazily initialised SDK client.

        logger.info(
            "LLMClient initialised — provider=%s model=%s",
            self.provider,
            self.model,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_client(self) -> None:
        """Lazily instantiate the underlying provider SDK client.

        Raises:
            LLMClientError: If the SDK is not installed or the client
                cannot be created.
        """
        # TODO: Implement provider-specific client initialisation
        #       (OpenAI, Anthropic, Ollama, etc.)
        raise LLMClientError(
            f"SDK client for provider '{self.provider}' is not yet initialised."
        )

    # ------------------------------------------------------------------
    # Public API
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

        Args:
            prompt: User-facing prompt string.
            system_prompt: Optional system-level instruction prefix.
            temperature: Override the default sampling temperature.
            max_tokens: Override the default maximum token count.

        Returns:
            The LLM response as a plain string.

        Raises:
            LLMClientError: On any communication or response error.
        """
        logger.debug("generate() called — model=%s", self.model)

        # TODO: Implement async generation via provider SDK.
        #       1. Build the messages list from prompt + system_prompt.
        #       2. Call the provider's chat completions endpoint.
        #       3. Extract and return the assistant message content.
        #       4. Wrap provider-specific exceptions in LLMClientError.
        raise LLMClientError("generate() is not yet implemented.")

    async def generate_json(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Send a prompt and return a parsed JSON object.

        The method requests JSON-mode output from the LLM (where
        supported) and validates the response before returning.

        Args:
            prompt: User-facing prompt string.
            system_prompt: Optional system-level instruction prefix.
            temperature: Override the default sampling temperature.
            max_tokens: Override the default maximum token count.
            response_format: Optional dict requesting a specific schema
                (e.g. ``{"type": "json_object"}``).

        Returns:
            A dictionary parsed from the LLM's JSON response.

        Raises:
            LLMClientError: If the response is not valid JSON or the
                request fails.
        """
        logger.debug("generate_json() called — model=%s", self.model)

        # TODO: Implement JSON-mode generation.
        #       1. Set response_format={"type": "json_object"} if supported.
        #       2. Call generate() with the appropriate prompts.
        #       3. Parse the response via ResponseParser.parse_json().
        #       4. Return the validated dict.
        raise LLMClientError("generate_json() is not yet implemented.")

    async def stream(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Yield response tokens as they arrive from the LLM.

        Args:
            prompt: User-facing prompt string.
            system_prompt: Optional system-level instruction prefix.
            temperature: Override the default sampling temperature.
            max_tokens: Override the default maximum token count.

        Yields:
            Chunks of the LLM response text.

        Raises:
            LLMClientError: On any communication error during streaming.
        """
        logger.debug("stream() called — model=%s", self.model)

        # TODO: Implement streaming via provider SDK.
        #       1. Create a streaming chat completion request.
        #       2. Yield each delta.content chunk as a string.
        #       3. Close the stream on completion or error.
        raise LLMClientError("stream() is not yet implemented.")
