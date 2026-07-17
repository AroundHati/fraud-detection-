"""
Abstract base class for LLM provider backends.

Defines the provider contract that all concrete implementations
(Gemini, OpenAI, Anthropic, etc.) must satisfy.  The investigation
agent and any future LLM-consuming code should depend only on
``BaseLLMProvider`` — never on a concrete SDK class.

Design
------
- ``generate()`` returns raw text — callers handle parsing.
- ``generate_structured()`` returns a validated Pydantic model
  instance — callers get typed data directly.
- ``health_check()`` allows pre-flight connectivity verification.
- All methods are ``async`` so that provider implementations can
  perform non-blocking I/O.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional, Type, TypeVar

from pydantic import BaseModel

from ml.llm.schemas import LLMConfig

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Abstract interface for an LLM provider backend.

    Subclasses must implement ``generate``, ``generate_structured``,
    and ``health_check``.  All other methods have sensible defaults.

    Parameters
    ----------
    config : LLMConfig
        Validated configuration for this provider instance.

    Examples
    --------
    >>> provider = GeminiProvider(LLMConfig(model="gemini-1.5-flash"))
    >>> text = await provider.generate("What is 2+2?")
    >>> print(text)
    '4'
    """

    def __init__(self, config: LLMConfig) -> None:
        self._config = config
        logger.info(
            "%s initialised — model=%s temperature=%.2f max_tokens=%d",
            self.__class__.__name__,
            config.model,
            config.temperature,
            config.max_tokens,
        )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def provider_name(self) -> str:
        """Return the provider identifier string."""
        return self._config.provider

    @property
    def model(self) -> str:
        """Return the model identifier."""
        return self._config.model

    @property
    def config(self) -> LLMConfig:
        """Return the full configuration object."""
        return self._config

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
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
            System-level instruction prefix prepended to the prompt.
        temperature : float, optional
            Override the default sampling temperature for this call.
        max_tokens : int, optional
            Override the default maximum token count for this call.

        Returns
        -------
        str
            The LLM response as plain text.

        Raises
        ------
        LLMConnectionError
            If the provider cannot be reached.
        LLMRateLimitError
            If the provider returns a 429 response.
        LLMResponseError
            If the response is empty or otherwise unusable.
        """
        ...

    @abstractmethod
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

        The provider requests JSON output (where supported), and the
        response is parsed and validated before being returned.

        Parameters
        ----------
        prompt : str
            User-facing prompt string.
        response_model : Type[T]
            The Pydantic model class to validate the response against.
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
            If the LLM response cannot be validated against the model.
        LLMResponseError
            If the raw response is empty or unusable.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Verify that the provider is reachable and configured correctly.

        Returns
        -------
        bool
            ``True`` if the provider responds successfully, ``False``
            otherwise.  Implementations should log the reason for
            failure but never raise an exception.
        """
        ...

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}("
            f"provider={self.provider_name!r}, model={self.model!r})>"
        )
