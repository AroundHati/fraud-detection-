"""
Exception hierarchy for the FraudShield LLM provider layer.

Defines a clean exception tree so that callers can catch broad
``LLMProviderError`` for any LLM failure, or narrow exceptions
for specific failure modes (connection, rate-limit, validation).

Design
------
- ``LLMProviderError`` is the base class for all LLM errors.
- Each subclass maps to a distinct, recoverable failure mode.
- Exceptions carry structured context (provider name, model, status
  code) so that logging and retry logic can make informed decisions.
- No SDK-specific exception types leak beyond the provider layer —
  every SDK error is wrapped in one of these classes.
"""

from __future__ import annotations

from typing import Any, Optional


class LLMProviderError(Exception):
    """Base exception for all errors originating from LLM providers.

    Attributes:
        provider: Identifier of the provider that raised the error
            (e.g. ``"gemini"``).
        model: Model identifier that was in use when the error occurred.
        message: Human-readable error description.
        cause: Original exception if this error wraps an SDK error.
    """

    def __init__(
        self,
        message: str,
        *,
        provider: str = "unknown",
        model: str = "unknown",
        cause: Optional[Exception] = None,
    ) -> None:
        self.provider = provider
        self.model = model
        self.cause = cause
        super().__init__(message)

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}("
            f"provider={self.provider!r}, model={self.model!r})>"
        )


class LLMConnectionError(LLMProviderError):
    """Raised when the provider cannot be reached.

    This covers network timeouts, DNS failures, TLS errors, and any
    other transport-level problem that prevents the request from
    completing.
    """


class LLMRateLimitError(LLMProviderError):
    """Raised when the provider returns a rate-limit (429) response.

    Attributes:
        retry_after: Optional number of seconds the provider recommends
            waiting before retrying.  ``None`` if not provided by the
            provider.
    """

    def __init__(
        self,
        message: str,
        *,
        provider: str = "unknown",
        model: str = "unknown",
        retry_after: Optional[float] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(
            message,
            provider=provider,
            model=model,
            cause=cause,
        )


class LLMResponseError(LLMProviderError):
    """Raised when the provider returns an unusable response.

    This covers empty completions, content-filter blocks, malformed
    output, and any other case where the response cannot be processed
    as valid text.
    """


class LLMConfigError(LLMProviderError):
    """Raised when provider configuration is missing or invalid.

    Typical causes:
        - Missing API key environment variable.
        - Invalid model identifier.
        - Configuration values outside the provider's supported range.
    """


class LLMResponseValidationError(LLMProviderError):
    """Raised when a structured LLM response fails Pydantic validation.

    Attributes:
        validation_errors: Raw Pydantic validation error details.
        raw_response: The original unparsed LLM response text.
    """

    def __init__(
        self,
        message: str,
        *,
        provider: str = "unknown",
        model: str = "unknown",
        validation_errors: Optional[Any] = None,
        raw_response: str = "",
        cause: Optional[Exception] = None,
    ) -> None:
        self.validation_errors = validation_errors
        self.raw_response = raw_response
        super().__init__(
            message,
            provider=provider,
            model=model,
            cause=cause,
        )
