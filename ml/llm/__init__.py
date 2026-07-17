"""
LLM integration layer for the FraudShield multi-agent system.

Provides a unified interface for prompt rendering, LLM communication,
and response parsing across all agents.

Submodules
----------
- ``base`` — Abstract ``BaseLLMProvider`` interface.
- ``gemini_provider`` — Google Gemini implementation.
- ``factory`` — Provider factory with registry.
- ``schemas`` — Pydantic models for configuration and structured output.
- ``exceptions`` — LLM-specific exception hierarchy.
- ``parser`` — Response parsing and validation utilities.
- ``client`` — Legacy ``LLMClient`` (preserved for backward compatibility).
- ``prompts`` — Prompt template collection.
"""

from ml.llm.base import BaseLLMProvider
from ml.llm.client import LLMClient
from ml.llm.exceptions import (
    LLMConfigError,
    LLMConnectionError,
    LLMProviderError,
    LLMRateLimitError,
    LLMResponseError,
    LLMResponseValidationError,
)
from ml.llm.factory import create_llm_provider, list_providers, register_provider
from ml.llm.parser import ResponseParser
from ml.llm.prompts import PromptTemplates
from ml.llm.schemas import (
    FraudIntelligenceCriticalFinding,
    FraudIntelligenceLLMResponse,
    FraudIntelligenceRecommendation,
    InvestigationFinding,
    InvestigationLLMResponse,
    InvestigationRecommendation,
    LLMConfig,
)

__all__ = [
    # Base
    "BaseLLMProvider",
    # Factory
    "create_llm_provider",
    "list_providers",
    "register_provider",
    # Schemas
    "LLMConfig",
    "InvestigationLLMResponse",
    "InvestigationFinding",
    "InvestigationRecommendation",
    "FraudIntelligenceLLMResponse",
    "FraudIntelligenceCriticalFinding",
    "FraudIntelligenceRecommendation",
    # Exceptions
    "LLMProviderError",
    "LLMConnectionError",
    "LLMRateLimitError",
    "LLMResponseError",
    "LLMConfigError",
    "LLMResponseValidationError",
    # Utilities
    "ResponseParser",
    # Legacy (preserved for backward compatibility)
    "LLMClient",
    "PromptTemplates",
]
