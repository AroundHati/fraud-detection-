"""
LLM integration layer for the FraudShield multi-agent system.

Provides a unified interface for prompt rendering, LLM communication,
and response parsing across all agents.
"""

from ml.llm.client import LLMClient
from ml.llm.parser import ResponseParser
from ml.llm.prompts import PromptTemplates

__all__ = [
    "LLMClient",
    "PromptTemplates",
    "ResponseParser",
]
