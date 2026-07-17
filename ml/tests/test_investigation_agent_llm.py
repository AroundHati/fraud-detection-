"""
Tests for the refactored Investigation Agent with mocked LLM provider.

Verifies that:
- The investigation node calls the LLM provider correctly.
- LLM findings are mapped to state in the expected format.
- Fallback logic works when the LLM is unavailable.
- The prompt is built correctly from state data.
- Existing test contracts (finding_id, category, severity, etc.) are preserved.
- Backward compatibility with the legacy InvestigationAgent class.

All tests use a mock provider — no live API calls are made.
"""

from __future__ import annotations

import asyncio
import copy
from typing import Any, Optional, Type
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

from ml.agents.investigation_agent import (
    InvestigationAgent,
    InvestigationAgentError,
    _build_investigation_prompt,
    _format_indicators,
    _format_statistics,
    _map_llm_findings_to_state,
    _load_prompt_template,
    run_investigation_node,
)
from ml.agents.state import InvestigationState
from ml.agents.utils import (
    STATUS_INVESTIGATING,
    create_initial_state,
)
from ml.llm.base import BaseLLMProvider
from ml.llm.exceptions import LLMProviderError
from ml.llm.schemas import (
    InvestigationFinding,
    InvestigationLLMResponse,
    InvestigationRecommendation,
    LLMConfig,
)


# =====================================================================
# Mock LLM provider
# =====================================================================


class MockInvestigationProvider(BaseLLMProvider):
    """Mock provider that returns a fixed InvestigationLLMResponse."""

    def __init__(
        self,
        response: Optional[InvestigationLLMResponse] = None,
        should_fail: bool = False,
    ) -> None:
        config = LLMConfig(provider="mock", model="mock-v1")
        super().__init__(config)
        self._response = response or InvestigationLLMResponse(
            executive_summary="Provider shows upcoding patterns in claims data.",
            findings=[
                InvestigationFinding(
                    category="upcoding",
                    severity="High",
                    description=(
                        "Systematic upcoding of E&M codes detected across "
                        "15 claims with abnormally high reimbursement amounts."
                    ),
                    evidence=["CLM-001 ($5,200)", "CLM-002 ($4,800)"],
                    confidence=0.87,
                    estimated_impact=25000.0,
                ),
                InvestigationFinding(
                    category="unbundling",
                    severity="Medium",
                    description=(
                        "Lab panels billed as separate components instead of "
                        "bundled panel pricing."
                    ),
                    evidence=["CLM-003", "CLM-004"],
                    confidence=0.72,
                    estimated_impact=8500.0,
                ),
            ],
            recommendations=[
                InvestigationRecommendation(
                    category="audit",
                    priority="Immediate",
                    description="Conduct full E&M code audit for past 12 months",
                    rationale="High confidence upcoding detected",
                ),
                InvestigationRecommendation(
                    category="monitoring",
                    priority="Medium",
                    description="Place provider on enhanced claims monitoring",
                    rationale="Multiple fraud patterns identified",
                ),
            ],
        )
        self._should_fail = should_fail
        self.generate_calls: list[str] = []

    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        self.generate_calls.append(prompt)
        if self._should_fail:
            raise LLMProviderError("Mock failure", provider="mock")
        return "Mock response"

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        *,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> BaseModel:
        self.generate_calls.append(prompt)
        if self._should_fail:
            raise LLMProviderError("Mock failure", provider="mock")
        return self._response

    async def health_check(self) -> bool:
        return not self._should_fail


# =====================================================================
# Fixtures
# =====================================================================


@pytest.fixture
def base_state() -> InvestigationState:
    """Create a base state with pipeline outputs for agent testing."""
    state = create_initial_state(
        investigation_id="INV-LLM-TEST",
        provider_id="PRV-LLM-TEST",
    )
    state["features"] = {"TotalClaims": 200}
    state["prediction"] = {
        "provider_id": "PRV-LLM-TEST",
        "prediction": "Yes",
        "fraud_probability": 0.75,
        "confidence": 88.0,
    }
    state["fraud_score"] = 0.75
    state["risk_level"] = "High"
    state["indicators"] = [
        {
            "title": "Claim Volume",
            "status": "flagged",
            "severity": "high",
            "description": "Abnormally high claim volume.",
        },
    ]
    state["provider_statistics"] = {
        "total_claims": 200,
        "total_reimbursement": 600000.0,
    }
    return state


@pytest.fixture
def mock_provider() -> MockInvestigationProvider:
    """Create a mock LLM provider with default successful response."""
    return MockInvestigationProvider()


@pytest.fixture
def failing_provider() -> MockInvestigationProvider:
    """Create a mock LLM provider that always fails."""
    return MockInvestigationProvider(should_fail=True)


# =====================================================================
# Helper function tests
# =====================================================================


class TestFormatIndicators:
    def test_empty_indicators(self):
        result = _format_indicators([])
        assert "No indicators" in result

    def test_single_indicator(self):
        indicators = [
            {"title": "Volume", "status": "flagged", "severity": "high",
             "description": "High volume."}
        ]
        result = _format_indicators(indicators)
        assert "Volume" in result
        assert "flagged" in result
        assert "high volume" in result.lower()

    def test_multiple_indicators(self):
        indicators = [
            {"title": "A", "status": "ok", "severity": "low", "description": "A desc"},
            {"title": "B", "status": "flagged", "severity": "high", "description": "B desc"},
        ]
        result = _format_indicators(indicators)
        assert "1." in result
        assert "2." in result


class TestFormatStatistics:
    def test_empty_statistics(self):
        result = _format_statistics({})
        assert "No statistics" in result

    def test_with_data(self):
        stats = {"total_claims": 100, "total_reimbursement": 50000.0}
        result = _format_statistics(stats)
        assert "100" in result
        assert "50000" in result


class TestLoadPromptTemplate:
    def test_loads_successfully(self):
        template = _load_prompt_template()
        assert isinstance(template, str)
        assert "{provider_id}" in template
        assert "{risk_level}" in template
        assert "{fraud_score}" in template


class TestBuildInvestigationPrompt:
    def test_prompt_contains_state_data(self, base_state):
        prompt = _build_investigation_prompt(base_state)
        assert "PRV-LLM-TEST" in prompt
        assert "High" in prompt
        assert "0.75" in prompt
        assert "Claim Volume" in prompt

    def test_prompt_with_missing_data(self):
        state = create_initial_state(provider_id="PRV-NO-DATA")
        state["risk_level"] = "unknown"
        state["fraud_score"] = "N/A"
        prompt = _build_investigation_prompt(state)
        assert "PRV-NO-DATA" in prompt


class TestMapLlmFindings:
    def test_maps_findings_and_recommendations(self):
        response = InvestigationLLMResponse(
            executive_summary="Summary",
            findings=[
                InvestigationFinding(
                    category="upcoding",
                    severity="High",
                    description="Test finding",
                    confidence=0.9,
                )
            ],
            recommendations=[
                InvestigationRecommendation(
                    category="audit",
                    priority="High",
                    description="Audit recommendation",
                )
            ],
        )
        findings, recs = _map_llm_findings_to_state(response, "PRV-001")
        assert len(findings) == 1
        assert findings[0]["finding_id"] == "FI-PRV-001-0001"
        assert findings[0]["category"] == "upcoding"
        assert findings[0]["severity"] == "High"
        assert findings[0]["confidence"] == 0.9
        assert len(recs) == 1
        assert recs[0]["recommendation_id"] == "REC-PRV-001-0001"

    def test_empty_response(self):
        response = InvestigationLLMResponse(executive_summary="Nothing found")
        findings, recs = _map_llm_findings_to_state(response, "PRV-002")
        assert findings == []
        assert recs == []


# =====================================================================
# Investigation node tests (LLM-backed)
# =====================================================================


class TestInvestigationNodeLLM:
    """Tests for run_investigation_node with mocked LLM provider."""

    def test_returns_investigation_state(self, base_state, mock_provider):
        result = run_investigation_node(base_state, provider=mock_provider)
        assert isinstance(result, dict)
        assert "investigation_id" in result

    def test_updates_status(self, base_state, mock_provider):
        result = run_investigation_node(base_state, provider=mock_provider)
        assert result["status"] != "initialized"

    def test_appends_to_execution_log(self, base_state, mock_provider):
        initial_count = len(base_state.get("execution_log", []))
        result = run_investigation_node(base_state, provider=mock_provider)
        final_count = len(result.get("execution_log", []))
        assert final_count >= initial_count + 2

    def test_log_entries_have_correct_agent_name(self, base_state, mock_provider):
        result = run_investigation_node(base_state, provider=mock_provider)
        agent_entries = [
            e for e in result["execution_log"]
            if e.get("agent_name") == "investigation_agent"
        ]
        assert len(agent_entries) >= 2

    def test_populates_ai_findings_from_llm(self, base_state, mock_provider):
        result = run_investigation_node(base_state, provider=mock_provider)
        findings = result.get("ai_findings", [])
        assert len(findings) == 2
        # Verify finding schema
        for finding in findings:
            assert "finding_id" in finding
            assert "category" in finding
            assert "severity" in finding
            assert "description" in finding
            assert "evidence" in finding
            assert "confidence" in finding

    def test_findings_have_correct_ids(self, base_state, mock_provider):
        result = run_investigation_node(base_state, provider=mock_provider)
        findings = result["ai_findings"]
        assert findings[0]["finding_id"] == "FI-PRV-LLM-TEST-0001"
        assert findings[1]["finding_id"] == "FI-PRV-LLM-TEST-0002"

    def test_populates_recommendations_from_llm(self, base_state, mock_provider):
        result = run_investigation_node(base_state, provider=mock_provider)
        recs = result.get("recommendations", [])
        assert len(recs) >= 2
        assert any(r["category"] == "audit" for r in recs)

    def test_preserves_investigation_id(self, base_state, mock_provider):
        result = run_investigation_node(base_state, provider=mock_provider)
        assert result["investigation_id"] == "INV-LLM-TEST"

    def test_llm_provider_called(self, base_state, mock_provider):
        run_investigation_node(base_state, provider=mock_provider)
        assert len(mock_provider.generate_calls) == 1
        assert "PRV-LLM-TEST" in mock_provider.generate_calls[0]

    def test_source_tagged_as_llm(self, base_state, mock_provider):
        result = run_investigation_node(base_state, provider=mock_provider)
        completed_entries = [
            e for e in result["execution_log"]
            if e.get("status") == "completed" and e.get("agent_name") == "investigation_agent"
        ]
        assert any("source=llm" in e.get("message", "") for e in completed_entries)


# =====================================================================
# Fallback tests (LLM failure)
# =====================================================================


class TestInvestigationNodeFallback:
    """Tests for fallback behaviour when the LLM is unavailable."""

    def test_handles_missing_pipeline_data(self):
        state = create_initial_state(provider_id="PRV-EMPTY")
        result = run_investigation_node(state)
        assert result["status"] == "failed"
        error_entries = [e for e in result["execution_log"] if e.get("error")]
        assert len(error_entries) > 0

    def test_fallback_on_llm_failure(self, base_state, failing_provider):
        result = run_investigation_node(base_state, provider=failing_provider)
        findings = result.get("ai_findings", [])
        assert len(findings) == 1
        assert findings[0]["category"] == "pending_analysis"
        assert findings[0]["severity"] == "Medium"

    def test_fallback_adds_indicator_recommendations(self, base_state, failing_provider):
        result = run_investigation_node(base_state, provider=failing_provider)
        recs = result.get("recommendations", [])
        assert len(recs) >= 1
        assert any("Claim Volume" in r.get("description", "") for r in recs)

    def test_source_tagged_as_fallback(self, base_state, failing_provider):
        result = run_investigation_node(base_state, provider=failing_provider)
        completed_entries = [
            e for e in result["execution_log"]
            if e.get("status") == "completed" and e.get("agent_name") == "investigation_agent"
        ]
        assert any("source=fallback" in e.get("message", "") for e in completed_entries)

    def test_deterministic_with_same_provider(self, base_state):
        provider = MockInvestigationProvider()
        state1 = copy.deepcopy(base_state)
        state2 = copy.deepcopy(base_state)
        result1 = run_investigation_node(state1, provider=provider)
        result2 = run_investigation_node(state2, provider=provider)
        assert len(result1["ai_findings"]) == len(result2["ai_findings"])
        assert result1["ai_findings"][0]["category"] == result2["ai_findings"][0]["category"]


# =====================================================================
# InvestigationAgent class tests (legacy interface)
# =====================================================================


class TestInvestigationAgentClass:
    """Tests for the InvestigationAgent BaseAgent subclass."""

    def test_execute_raises_without_risk_assessment(self):
        provider = MockInvestigationProvider()
        agent = InvestigationAgent(provider=provider)
        from ml.schemas.agent_state import AgentState
        state = AgentState(provider_id="PRV-001")
        with pytest.raises(InvestigationAgentError, match="risk_assessment is None"):
            asyncio.run(agent.execute(state))

    def test_execute_calls_llm(self):
        provider = MockInvestigationProvider()
        agent = InvestigationAgent(provider=provider)
        from ml.schemas.agent_state import AgentState
        from ml.schemas.risk import RiskAssessment
        risk = RiskAssessment(
            assessment_id="RA-001",
            total_providers=1,
            overall_risk_level="High",
        )
        state = AgentState(
            provider_id="PRV-001",
            risk_assessment=risk,
        )
        asyncio.run(agent.execute(state))
        assert len(provider.generate_calls) == 1

    def test_agent_name(self):
        agent = InvestigationAgent()
        assert agent.name == "investigation"

    def test_agent_description(self):
        agent = InvestigationAgent()
        assert "investigation" in agent.description.lower()
