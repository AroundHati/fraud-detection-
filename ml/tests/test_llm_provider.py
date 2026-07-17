"""
Tests for the FraudShield LLM provider layer.

Covers:
- Exception hierarchy (exception types, attributes, repr).
- Schema validation (LLMConfig, InvestigationLLMResponse, etc.).
- ResponseParser (parse_json, validate_response, safe_parse).
- Factory (create_llm_provider, register_provider, list_providers).
- BaseLLMProvider interface contract.

All tests use mocked or in-memory logic — no live API calls.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Optional, Type
from unittest.mock import patch

import pytest
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
from ml.llm.factory import (
    _PROVIDER_REGISTRY,
    create_llm_provider,
    list_providers,
    register_provider,
)
from ml.llm.parser import ParseError, ResponseParser
from ml.llm.schemas import (
    InvestigationFinding,
    InvestigationLLMResponse,
    InvestigationRecommendation,
    LLMConfig,
)


# =====================================================================
# Exception hierarchy tests
# =====================================================================


class TestLLMProviderError:
    """Tests for the base LLMProviderError exception."""

    def test_is_exception_subclass(self):
        assert issubclass(LLMProviderError, Exception)

    def test_attributes(self):
        exc = LLMProviderError(
            "test error",
            provider="gemini",
            model="gemini-1.5-flash",
        )
        assert str(exc) == "test error"
        assert exc.provider == "gemini"
        assert exc.model == "gemini-1.5-flash"
        assert exc.cause is None

    def test_repr(self):
        exc = LLMProviderError("err", provider="openai", model="gpt-4o")
        assert "LLMProviderError" in repr(exc)
        assert "openai" in repr(exc)

    def test_cause_preserved(self):
        original = ValueError("original")
        exc = LLMProviderError("wrapped", cause=original)
        assert exc.cause is original


class TestLLMConnectionError:
    def test_hierarchy(self):
        assert issubclass(LLMConnectionError, LLMProviderError)

    def test_attributes(self):
        exc = LLMConnectionError("timeout", provider="gemini")
        assert exc.provider == "gemini"


class TestLLMRateLimitError:
    def test_hierarchy(self):
        assert issubclass(LLMRateLimitError, LLMProviderError)

    def test_retry_after(self):
        exc = LLMRateLimitError("rate limited", retry_after=30.0)
        assert exc.retry_after == 30.0

    def test_retry_after_none(self):
        exc = LLMRateLimitError("rate limited")
        assert exc.retry_after is None


class TestLLMResponseError:
    def test_hierarchy(self):
        assert issubclass(LLMResponseError, LLMProviderError)


class TestLLMConfigError:
    def test_hierarchy(self):
        assert issubclass(LLMConfigError, LLMProviderError)


class TestLLMResponseValidationError:
    def test_hierarchy(self):
        assert issubclass(LLMResponseValidationError, LLMProviderError)

    def test_extra_attributes(self):
        exc = LLMResponseValidationError(
            "validation failed",
            validation_errors={"field": "error"},
            raw_response='{"bad": "json"}',
        )
        assert exc.validation_errors == {"field": "error"}
        assert exc.raw_response == '{"bad": "json"}'


# =====================================================================
# Schema tests
# =====================================================================


class TestLLMConfig:
    """Tests for LLMConfig Pydantic model."""

    def test_defaults(self):
        config = LLMConfig()
        assert config.provider == "gemini"
        assert config.model == "gemini-1.5-flash"
        assert config.temperature == 0.3
        assert config.max_tokens == 4096
        assert config.timeout == 60
        assert config.max_retries == 3

    def test_custom_values(self):
        config = LLMConfig(
            provider="openai",
            model="gpt-4o",
            temperature=0.7,
            max_tokens=2048,
            timeout=30,
            max_retries=5,
        )
        assert config.provider == "openai"
        assert config.temperature == 0.7

    def test_temperature_bounds(self):
        with pytest.raises(ValidationError):
            LLMConfig(temperature=-0.1)
        with pytest.raises(ValidationError):
            LLMConfig(temperature=2.1)

    def test_max_tokens_positive(self):
        with pytest.raises(ValidationError):
            LLMConfig(max_tokens=0)

    def test_empty_provider_rejected(self):
        with pytest.raises(ValidationError):
            LLMConfig(provider="")

    def test_serialization(self):
        config = LLMConfig(provider="gemini", api_key="test-key-123")
        data = config.model_dump()
        assert data["provider"] == "gemini"
        assert data["api_key"] == "test-key-123"
        restored = LLMConfig(**data)
        assert restored == config


class TestInvestigationFinding:
    def test_valid_finding(self):
        finding = InvestigationFinding(
            category="upcoding",
            severity="High",
            description="Suspicious billing pattern detected",
            evidence=["CLM-001", "CLM-002"],
            confidence=0.85,
            estimated_impact=15000.0,
        )
        assert finding.category == "upcoding"
        assert finding.confidence == 0.85

    def test_minimal_finding(self):
        finding = InvestigationFinding(
            category="other",
            severity="Low",
            description="Minor anomaly",
        )
        assert finding.evidence == []
        assert finding.estimated_impact is None

    def test_empty_category_rejected(self):
        with pytest.raises(ValidationError):
            InvestigationFinding(
                category="",
                severity="Medium",
                description="test",
            )

    def test_confidence_bounds(self):
        with pytest.raises(ValidationError):
            InvestigationFinding(
                category="test",
                severity="Low",
                description="test",
                confidence=1.5,
            )


class TestInvestigationRecommendation:
    def test_valid_recommendation(self):
        rec = InvestigationRecommendation(
            category="audit",
            priority="Immediate",
            description="Conduct full audit of billing records",
            rationale="High fraud score detected",
        )
        assert rec.category == "audit"
        assert rec.priority == "Immediate"


class TestInvestigationLLMResponse:
    def test_full_response(self):
        response = InvestigationLLMResponse(
            executive_summary="Provider shows upcoding patterns.",
            findings=[
                InvestigationFinding(
                    category="upcoding",
                    severity="High",
                    description="Systematic upcoding detected",
                    confidence=0.9,
                )
            ],
            recommendations=[
                InvestigationRecommendation(
                    category="audit",
                    priority="High",
                    description="Conduct immediate audit",
                )
            ],
        )
        assert len(response.findings) == 1
        assert len(response.recommendations) == 1

    def test_empty_response(self):
        response = InvestigationLLMResponse(
            executive_summary="No issues found.",
        )
        assert response.findings == []
        assert response.recommendations == []

    def test_empty_summary_rejected(self):
        with pytest.raises(ValidationError):
            InvestigationLLMResponse(executive_summary="")


# =====================================================================
# Parser tests
# =====================================================================


class TestParseJson:
    """Tests for ResponseParser.parse_json()."""

    def test_valid_json(self):
        raw = '{"key": "value", "count": 42}'
        result = ResponseParser.parse_json(raw)
        assert result == {"key": "value", "count": 42}

    def test_json_with_markdown_fences(self):
        raw = '```json\n{"key": "value"}\n```'
        result = ResponseParser.parse_json(raw)
        assert result == {"key": "value"}

    def test_json_with_plain_fences(self):
        raw = '```\n{"key": "value"}\n```'
        result = ResponseParser.parse_json(raw)
        assert result == {"key": "value"}

    def test_json_embedded_in_text(self):
        raw = 'Here is the result: {"key": "value"} done.'
        result = ResponseParser.parse_json(raw)
        assert result == {"key": "value"}

    def test_json_with_trailing_commas(self):
        raw = '{"key": "value", "list": [1, 2, 3,],}'
        result = ResponseParser.parse_json(raw)
        assert result["key"] == "value"
        assert result["list"] == [1, 2, 3]

    def test_empty_string_raises(self):
        with pytest.raises(ParseError, match="empty"):
            ResponseParser.parse_json("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ParseError, match="empty"):
            ResponseParser.parse_json("   \n  ")

    def test_no_json_raises(self):
        with pytest.raises(ParseError):
            ResponseParser.parse_json("This is just plain text with no JSON.")

    def test_nested_json(self):
        raw = '{"outer": {"inner": [1, 2, 3]}}'
        result = ResponseParser.parse_json(raw)
        assert result["outer"]["inner"] == [1, 2, 3]


class TestValidateResponse:
    """Tests for ResponseParser.validate_response()."""

    def test_valid_data(self):
        data = {"executive_summary": "Test summary"}
        result = ResponseParser.validate_response(
            data, InvestigationLLMResponse
        )
        assert isinstance(result, InvestigationLLMResponse)
        assert result.executive_summary == "Test summary"

    def test_invalid_data_raises(self):
        data = {"executive_summary": ""}  # empty string violates min_length
        with pytest.raises(ParseError, match="Validation failed"):
            ResponseParser.validate_response(data, InvestigationLLMResponse)

    def test_missing_required_field(self):
        data = {}  # missing executive_summary
        with pytest.raises(ParseError, match="Validation failed"):
            ResponseParser.validate_response(data, InvestigationLLMResponse)


class TestSafeParse:
    """Tests for ResponseParser.safe_parse()."""

    def test_valid_json_no_model(self):
        raw = '{"key": "value"}'
        result = ResponseParser.safe_parse(raw)
        assert result == {"key": "value"}

    def test_valid_json_with_model(self):
        raw = '{"executive_summary": "All clear"}'
        result = ResponseParser.safe_parse(raw, InvestigationLLMResponse)
        assert isinstance(result, InvestigationLLMResponse)

    def test_invalid_json_returns_empty_dict(self):
        result = ResponseParser.safe_parse("not json at all")
        assert result == {}

    def test_invalid_validation_returns_raw_dict(self):
        raw = '{"executive_summary": ""}'  # invalid (empty)
        result = ResponseParser.safe_parse(raw, InvestigationLLMResponse)
        # Should return the raw dict, not the model
        assert isinstance(result, dict)
        assert "executive_summary" in result

    def test_none_model_returns_dict(self):
        raw = '{"a": 1}'
        result = ResponseParser.safe_parse(raw, model=None)
        assert result == {"a": 1}


# =====================================================================
# Factory tests
# =====================================================================


class TestFactory:
    """Tests for the provider factory."""

    def test_list_providers(self):
        providers = list_providers()
        assert "gemini" in providers

    def test_register_provider(self):
        register_provider("test_provider", "ml.llm.base.BaseLLMProvider")
        assert "test_provider" in list_providers()
        # Clean up
        del _PROVIDER_REGISTRY["test_provider"]

    def test_register_empty_name_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            register_provider("", "ml.llm.base.BaseLLMProvider")

    def test_register_empty_path_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            register_provider("test", "")

    def test_unknown_provider_raises(self):
        with pytest.raises(LLMConfigError, match="Unknown LLM provider"):
            create_llm_provider("nonexistent_provider")

    def test_default_provider_is_gemini(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            provider = create_llm_provider()
            assert provider.provider_name == "gemini"

    def test_explicit_provider(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            provider = create_llm_provider("gemini")
            assert provider.provider_name == "gemini"


# =====================================================================
# BaseLLMProvider tests (via concrete mock)
# =====================================================================


class MockProvider(BaseLLMProvider):
    """Minimal concrete provider for testing the ABC contract."""

    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        return f"Mock response to: {prompt[:50]}"

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        *,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> BaseModel:
        return response_model(
            executive_summary="Mock structured response",
            findings=[],
            recommendations=[],
        )

    async def health_check(self) -> bool:
        return True


class TestBaseLLMProvider:
    """Tests for BaseLLMProvider abstract interface."""

    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            BaseLLMProvider(LLMConfig())

    def test_concrete_provider_properties(self):
        config = LLMConfig(provider="mock", model="mock-v1")
        provider = MockProvider(config)
        assert provider.provider_name == "mock"
        assert provider.model == "mock-v1"
        assert provider.config == config

    def test_repr(self):
        config = LLMConfig(provider="mock", model="mock-v1")
        provider = MockProvider(config)
        r = repr(provider)
        assert "MockProvider" in r
        assert "mock" in r

    def test_generate(self):
        config = LLMConfig()
        provider = MockProvider(config)
        result = asyncio.get_event_loop().run_until_complete(
            provider.generate("Hello")
        )
        assert "Mock response" in result

    def test_generate_structured(self):
        config = LLMConfig()
        provider = MockProvider(config)
        result = asyncio.get_event_loop().run_until_complete(
            provider.generate_structured("Investigate", InvestigationLLMResponse)
        )
        assert isinstance(result, InvestigationLLMResponse)

    def test_health_check(self):
        config = LLMConfig()
        provider = MockProvider(config)
        result = asyncio.get_event_loop().run_until_complete(
            provider.health_check()
        )
        assert result is True
