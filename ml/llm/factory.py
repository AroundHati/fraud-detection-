"""
Provider factory for the FraudShield LLM layer.

Creates configured ``BaseLLMProvider`` instances from a provider
identifier string and optional configuration.  Supports a registry
pattern so that new providers can be registered without modifying
the factory's core logic.

Design
------
- The factory is the **only** place that maps provider name strings
  to concrete classes.  Agent code depends on ``BaseLLMProvider``.
- Providers are registered lazily — the concrete class is only
  imported when first requested — so missing optional dependencies
  (e.g. ``google-generativeai``) do not break unrelated imports.
- Configuration can be supplied explicitly or loaded from environment
  variables by the concrete provider.
"""

from __future__ import annotations

import logging
from typing import Optional, Type

from ml.llm.base import BaseLLMProvider
from ml.llm.exceptions import LLMConfigError
from ml.llm.schemas import LLMConfig

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# Provider registry
# -----------------------------------------------------------------------

_PROVIDER_REGISTRY: dict[str, str] = {
    "gemini": "ml.llm.gemini_provider.GeminiProvider",
    "openai": "ml.llm.openai_provider.OpenAIProvider",
}
"""Maps lowercase provider name to the fully-qualified class path.

Entries point to importable module paths rather than class objects
to support lazy loading.  The ``openai`` entry is a placeholder for
a future implementation.
"""


def register_provider(name: str, class_path: str) -> None:
    """Register a new LLM provider in the factory.

    Parameters
    ----------
    name : str
        Provider name (lowercase, e.g. ``"anthropic"``).
    class_path : str
        Fully-qualified class path (e.g.
        ``"ml.llm.anthropic_provider.AnthropicProvider"``).

    Raises
    ------
    ValueError
        If *name* or *class_path* is empty.
    """
    if not name or not name.strip():
        raise ValueError("Provider name must be a non-empty string")
    if not class_path or not class_path.strip():
        raise ValueError("Class path must be a non-empty string")

    _PROVIDER_REGISTRY[name.lower().strip()] = class_path
    logger.info("Provider registered — name=%s class=%s", name, class_path)


def list_providers() -> list[str]:
    """Return the names of all registered providers."""
    return sorted(_PROVIDER_REGISTRY.keys())


def _import_provider_class(class_path: str) -> Type[BaseLLMProvider]:
    """Dynamically import a provider class from its dotted path.

    Parameters
    ----------
    class_path : str
        Fully-qualified class path (e.g.
        ``"ml.llm.gemini_provider.GeminiProvider"``).

    Returns
    -------
    Type[BaseLLMProvider]
        The imported class.

    Raises
    ------
    LLMConfigError
        If the import fails.
    """
    module_path, class_name = class_path.rsplit(".", 1)

    try:
        import importlib

        module = importlib.import_module(module_path)
    except ImportError as exc:
        raise LLMConfigError(
            f"Cannot import provider module '{module_path}'. "
            f"Ensure the required SDK is installed.",
            provider=class_name,
            cause=exc,
        ) from exc

    try:
        cls = getattr(module, class_name)
    except AttributeError as exc:
        raise LLMConfigError(
            f"Module '{module_path}' has no attribute '{class_name}'",
            provider=class_name,
            cause=exc,
        ) from exc

    if not (isinstance(cls, type) and issubclass(cls, BaseLLMProvider)):
        raise LLMConfigError(
            f"'{class_path}' is not a BaseLLMProvider subclass",
            provider=class_name,
        )

    return cls


# -----------------------------------------------------------------------
# Factory function
# -----------------------------------------------------------------------


def create_llm_provider(
    provider: Optional[str] = None,
    config: Optional[LLMConfig] = None,
) -> BaseLLMProvider:
    """Create a configured LLM provider instance.

    This is the canonical entry point for obtaining a provider.  It
    resolves the provider name, imports the concrete class, and
    instantiates it with the supplied or default configuration.

    Parameters
    ----------
    provider : str, optional
        Provider name (e.g. ``"gemini"``).  If ``None``, defaults
        to ``"gemini"``.
    config : LLMConfig, optional
        Explicit configuration.  If ``None``, the concrete provider
        is expected to load its own config from environment variables.

    Returns
    -------
    BaseLLMProvider
        A fully initialised provider instance.

    Raises
    ------
    LLMConfigError
        If the provider name is unknown, the class cannot be imported,
        or the configuration is invalid.

    Examples
    --------
    >>> provider = create_llm_provider("gemini")
    >>> provider = create_llm_provider("gemini", config=LLMConfig(api_key="..."))
    >>> provider = create_llm_provider()  # defaults to gemini
    """
    provider_name = (provider or "gemini").lower().strip()

    if provider_name not in _PROVIDER_REGISTRY:
        available = list_providers()
        raise LLMConfigError(
            f"Unknown LLM provider '{provider_name}'. "
            f"Available providers: {available}",
            provider=provider_name,
        )

    class_path = _PROVIDER_REGISTRY[provider_name]
    cls = _import_provider_class(class_path)

    logger.info(
        "Creating LLM provider — name=%s class=%s",
        provider_name,
        class_path,
    )

    if config is not None:
        return cls(config)

    return cls()
