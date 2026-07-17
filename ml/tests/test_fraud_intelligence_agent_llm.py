"""
Tests for the fraud intelligence agent — LLM integration.

This module mirrors ``test_investigation_agent_llm.py`` and tests the
fraud intelligence agent's LLM-backed and fallback code paths using
a ``MockProvider`` that returns a fixed ``FraudIntelligenceLLMResponse``.
"""

from __future__ import annotations

from typing import Any, Type
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import BaseModel

from ml.agents.fraud_intelligence_agent import (
    FraudIntelligenceAgent,
    FraudIntelligenceAgentError,
    _build_fallback_intelligence,
    _build_intelligence_prompt,
    _format_documents,
    _format_findings,
    _format_indicators,
    _format_prediction,
    _format_statistics,
    _map_intelligence_response_to_state,
    _load_prompt_template,
    run_fraud_intelligence_node,
)
from ml.agents.state import InvestigationState
from ml.llm.base import BaseLLMProvider
from ml.llm.exceptions import LLMProviderError
from ml.llm.schemas import (
    FraudIntelligenceCriticalFinding,
    FraudIntelligenceLLMResponse,
    FraudIntelligenceRecommendation,
    LLMConfig,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FIXED_RESPONSE = FraudIntelligenceLLMResponse(
    overall_assessment=(
        "Comprehensive fraud intelligence analysis for provider ACME-001. "
        "Multiple upcoding patterns detected with high confidence."
    ),
    confidence=0.87,
    investigation_priority="High",
    critical_findings=[
        FraudIntelligenceCriticalFinding(
            finding_type="upcoding",
            severity="High",
            description="Systematic upcoding of E&M services detected",
            evidence=["Claim codes exceed documentation", "Pattern across 15 claims"],
            confidence=0.85,
            estimated_impact=45000.0,
            regulatory_reference="CMS-1557",
        ),
        FraudIntelligenceCriticalFinding(
            finding_type="unbundling",
            severity="Medium",
            description="Possible unbundling of laboratory panels",
            evidence=["Separate billing of panel components"],
            confidence=0.72,
            estimated_impact=12000.0,
            regulatory_reference=None,
        ),
    ],
    supporting_evidence=[
        "Claim data shows consistent upcoding pattern",
        "Knowledge base confirms CMS guidelines",
    ],
    recommended_actions=[
        FraudIntelligenceRecommendation(
            category="audit",
            priority="High",
            description="Conduct full claims audit for ACME-001",
            rationale="Strong evidence of systematic upcoding",
            deadline_days=14,
        ),
        FraudIntelligenceRecommendation(
            category="referral",
            priority="Medium",
            description="Refer to OIG for further investigation",
            rationale="Pattern may indicate intentional fraud",
            deadline_days=30,
        ),
    ],
    risk_factors=[
        "Multiple claim codes exceed documentation",
        "Billing pattern deviates from peer norms",
    ],
    mitigating_factors=[
        "Some claims are within normal range",
    ],
)


def _make_state(**overrides: Any) -> InvestigationState:
    """Return a minimal InvestigationState with optional overrides."""
    base: InvestigationState = {
        "claim_id": "CLM-TEST-001",
        "provider_id": "ACME-001",
        "risk_level": "High",
        "fraud_score": 78,
        "status": "pending_investigation",
        "transaction_data": {},
        "indicators": [
            {"title": "High fraud score", "status": "flagged", "severity": "High",
             "description": "Fraud score exceeds threshold"},
            {"title": "Claim volume spike", "status": "normal", "severity": "Low",
             "description": "Normal monthly volume"},
        ],
        "predictions": [],
        "anomalies": [],
        "similar_cases": [],
        "recommendations": [],
        "documents": [],
        "risk_factors": [],
        "explanation": "",
        "executed_nodes": [],
        "execution_log": [],
        "metadata": {},
        "current_agent": "",
        "messages": [],
        "errors": [],
        "ai_findings": [
            {
                "finding_id": "INV-ACME-001-0001",
                "category": "coding_pattern",
                "severity": "High",
                "description": "Upcoding of E&M services",
                "evidence": ["Claim data analysis"],
                "confidence": 0.8,
                "estimated_impact": 30000.0,
            },
        ],
        "retrieved_documents": [
            {
                "doc_id": "DOC-001",
                "source": "CMS Guidelines 2024",
                "content": "E&M services must be documented appropriately",
                "relevance_score": 0.92,
            },
        ],
        "prediction": {
            "prediction": "fraud",
            "fraud_probability": 0.78,
            "confidence": 85.0,
            "provider_id": "ACME-001",
        },
        "provider_statistics": {
            "total_claims": 150,
            "total_payments": 500000,
            "avg_claim_amount": 3333,
            "unique_providers": 1,
        },
        "investigation_type": "routine",
        "llm_investigation_response": "",
        "intelligence_assessment": "",
        "knowledge_agent_response": "",
        "report": {},
        "pipeline_name": "test_pipeline",
        "request_id": "req-001",
        "error": None,
        "fraud_agent_response": "",
        "investigation_agent_response": "",
        "report_agent_response": "",
        "supervisor_agent_response": "",
    }
    base.update(overrides)
    return base


class MockProvider(BaseLLMProvider):
    """Mock LLM provider that returns a fixed FraudIntelligenceLLMResponse."""

    def __init__(
        self,
        response: FraudIntelligenceLLMResponse | None = None,
        should_fail: bool = False,
    ) -> None:
        config = LLMConfig(provider="mock", model="mock-v1")
        super().__init__(config)
        self._response = response or FIXED_RESPONSE
        self._should_fail = should_fail

    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        if self._should_fail:
            raise LLMProviderError("Mock failure", provider="mock")
        return "Mocked LLM response text"

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        *,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> Any:
        if self._should_fail:
            raise LLMProviderError("Mock failure", provider="mock")
        return self._response

    async def health_check(self) -> bool:
        return not self._should_fail


# ---------------------------------------------------------------------------
# Tests: Prompt loading
# ---------------------------------------------------------------------------


class TestPromptLoading:
    """Tests for the prompt template loading helper."""

    def test_load_prompt_template_returns_string(self) -> None:
        """_load_prompt_template() should return a non-empty string."""
        template = _load_prompt_template()
        assert isinstance(template, str)
        assert len(template) > 0

    def test_load_prompt_template_has_placeholders(self) -> None:
        """The template should contain expected placeholders."""
        template = _load_prompt_template()
        assert "{provider_id}" in template
        assert "{risk_level}" in template
        assert "{fraud_score}" in template
        assert "{prediction_text}" in template
        assert "{findings_text}" in template
        assert "{documents_text}" in template
        assert "{indicators_text}" in template
        assert "{statistics_text}" in template


# ---------------------------------------------------------------------------
# Tests: Formatting helpers
# ---------------------------------------------------------------------------


class TestFormatFindings:
    """Tests for the findings formatter."""

    def test_empty_findings(self) -> None:
        """Empty list should return a fallback message."""
        result = _format_findings([])
        assert "No investigation findings available" in result

    def test_single_finding(self) -> None:
        """A single finding should be formatted with all fields."""
        findings = [
            {
                "finding_id": "INV-001",
                "category": "upcoding",
                "severity": "High",
                "description": "Upcoded E&M services",
                "evidence": ["Claim data"],
                "confidence": 0.85,
                "estimated_impact": 25000.0,
            }
        ]
        result = _format_findings(findings)
        assert "INV-001" in result
        assert "upcoding" in result
        assert "High" in result
        assert "0.85" in result
        assert "$25,000.00" in result
        assert "Upcoded E&M services" in result
        assert "Claim data" in result

    def test_multiple_findings(self) -> None:
        """Multiple findings should be numbered sequentially."""
        findings = [
            {"finding_id": "F1", "category": "upcoding", "severity": "High",
             "description": "First", "evidence": [], "confidence": 0.9},
            {"finding_id": "F2", "category": "unbundling", "severity": "Medium",
             "description": "Second", "evidence": ["X"], "confidence": 0.7},
        ]
        result = _format_findings(findings)
        assert "1." in result
        assert "2." in result

    def test_finding_without_impact(self) -> None:
        """Findings without estimated_impact should omit the impact line."""
        findings = [
            {"finding_id": "F1", "category": "other", "severity": "Low",
             "description": "No impact", "evidence": [], "confidence": 0.3}
        ]
        result = _format_findings(findings)
        assert "Estimated impact" not in result


class TestFormatDocuments:
    """Tests for the document formatter."""

    def test_empty_documents(self) -> None:
        """Empty list should return a fallback message."""
        result = _format_documents([])
        assert "No knowledge base documents available" in result

    def test_single_document(self) -> None:
        """A single document should be formatted with source and score."""
        docs = [
            {
                "doc_id": "DOC-1",
                "source": "OIG Guidelines",
                "content": "Billing must follow guidelines",
                "relevance_score": 0.95,
            }
        ]
        result = _format_documents(docs)
        assert "OIG Guidelines" in result
        assert "0.95" in result
        assert "Billing must follow guidelines" in result

    def test_long_content_truncated(self) -> None:
        """Document content longer than 500 chars should be truncated."""
        long_content = "x" * 600
        docs = [{"source": "Test", "content": long_content, "relevance_score": 0.5}]
        result = _format_documents(docs)
        assert "..." in result


class TestFormatIndicators:
    """Tests for the indicator formatter."""

    def test_empty_indicators(self) -> None:
        """Empty list should return a fallback message."""
        result = _format_indicators([])
        assert "No indicators available" in result

    def test_single_indicator(self) -> None:
        """A single indicator should be formatted with title and status."""
        indicators = [
            {"title": "High fraud score", "status": "flagged",
             "severity": "High", "description": "Score above threshold"}
        ]
        result = _format_indicators(indicators)
        assert "High fraud score" in result
        assert "flagged" in result
        assert "High" in result
        assert "Score above threshold" in result


class TestFormatStatistics:
    """Tests for the statistics formatter."""

    def test_empty_statistics(self) -> None:
        """Empty dict should return a fallback message."""
        result = _format_statistics({})
        assert "No statistics available" in result

    def test_populated_statistics(self) -> None:
        """Populated dict should have key-value pairs."""
        stats = {"total_claims": 150, "total_payments": 500000}
        result = _format_statistics(stats)
        assert "total_claims" in result
        assert "150" in result
        assert "total_payments" in result
        assert "500000" in result


class TestFormatPrediction:
    """Tests for the prediction formatter."""

    def test_empty_prediction(self) -> None:
        """Empty dict should return a fallback message."""
        result = _format_prediction({})
        assert "No prediction available" in result

    def test_populated_prediction(self) -> None:
        """Populated dict should include prediction details."""
        pred = {"prediction": "fraud", "fraud_probability": 0.85, "confidence": 92.0}
        result = _format_prediction(pred)
        assert "fraud" in result
        assert "0.8500" in result
        assert "92.00" in result


# ---------------------------------------------------------------------------
# Tests: Prompt building
# ---------------------------------------------------------------------------


class TestBuildIntelligencePrompt:
    """Tests for the intelligence prompt builder."""

    def test_prompt_contains_provider_id(self) -> None:
        """The prompt should contain the provider ID."""
        state = _make_state()
        prompt = _build_intelligence_prompt(state)
        assert "ACME-001" in prompt

    def test_prompt_contains_risk_level(self) -> None:
        """The prompt should contain the risk level."""
        state = _make_state(risk_level="Critical")
        prompt = _build_intelligence_prompt(state)
        assert "Critical" in prompt

    def test_prompt_contains_findings_text(self) -> None:
        """The prompt should include formatted investigation findings."""
        state = _make_state()
        prompt = _build_intelligence_prompt(state)
        assert "Upcoding of E&M services" in prompt

    def test_prompt_contains_documents_text(self) -> None:
        """The prompt should include formatted knowledge base documents."""
        state = _make_state()
        prompt = _build_intelligence_prompt(state)
        assert "CMS Guidelines 2024" in prompt

    def test_prompt_contains_indicators_text(self) -> None:
        """The prompt should include formatted indicators."""
        state = _make_state()
        prompt = _build_intelligence_prompt(state)
        assert "High fraud score" in prompt

    def test_prompt_contains_statistics_text(self) -> None:
        """The prompt should include formatted provider statistics."""
        state = _make_state()
        prompt = _build_intelligence_prompt(state)
        assert "total_claims" in prompt

    def test_prompt_contains_prediction_text(self) -> None:
        """The prompt should include formatted prediction details."""
        state = _make_state()
        prompt = _build_intelligence_prompt(state)
        assert "fraud" in prompt

    def test_prompt_with_empty_state(self) -> None:
        """Prompt should handle empty findings and documents gracefully."""
        state = _make_state(
            ai_findings=[],
            retrieved_documents=[],
            indicators=[],
            provider_statistics={},
            prediction={},
        )
        prompt = _build_intelligence_prompt(state)
        assert "No investigation findings available" in prompt
        assert "No knowledge base documents available" in prompt


# ---------------------------------------------------------------------------
# Tests: Response mapping
# ---------------------------------------------------------------------------


class TestMapIntelligenceResponseToState:
    """Tests for mapping the LLM response into the state."""

    def test_mappings_finding_ids(self) -> None:
        """Findings should receive sequential INT- prefixed IDs."""
        state = _make_state(ai_findings=[])
        response = FIXED_RESPONSE
        _map_intelligence_response_to_state(response, "ACME-001", state)

        assert len(state["ai_findings"]) == 2
        assert state["ai_findings"][0]["finding_id"] == "INT-ACME-001-0001"
        assert state["ai_findings"][1]["finding_id"] == "INT-ACME-001-0002"

    def test_mappings_category(self) -> None:
        """Findings should carry the original finding_type."""
        state = _make_state(ai_findings=[])
        _map_intelligence_response_to_state(FIXED_RESPONSE, "ACME-001", state)

        assert state["ai_findings"][0]["category"] == "upcoding"
        assert state["ai_findings"][1]["category"] == "unbundling"

    def test_mappings_severity(self) -> None:
        """Findings should carry the original severity."""
        state = _make_state(ai_findings=[])
        _map_intelligence_response_to_state(FIXED_RESPONSE, "ACME-001", state)

        assert state["ai_findings"][0]["severity"] == "High"
        assert state["ai_findings"][1]["severity"] == "Medium"

    def test_mappings_estimated_impact(self) -> None:
        """Findings should carry the original estimated_impact."""
        state = _make_state(ai_findings=[])
        _map_intelligence_response_to_state(FIXED_RESPONSE, "ACME-001", state)

        assert state["ai_findings"][0]["estimated_impact"] == 45000.0
        assert state["ai_findings"][1]["estimated_impact"] == 12000.0

    def test_mappings_recommendation_ids(self) -> None:
        """Recommendations should receive sequential REC-INT- prefixed IDs."""
        state = _make_state(recommendations=[])
        _map_intelligence_response_to_state(FIXED_RESPONSE, "ACME-001", state)

        assert len(state["recommendations"]) == 2
        assert state["recommendations"][0]["recommendation_id"] == "REC-INT-ACME-001-0001"
        assert state["recommendations"][1]["recommendation_id"] == "REC-INT-ACME-001-0002"

    def test_mappings_recommendation_category(self) -> None:
        """Recommendations should carry the original category."""
        state = _make_state(recommendations=[])
        _map_intelligence_response_to_state(FIXED_RESPONSE, "ACME-001", state)

        assert state["recommendations"][0]["category"] == "audit"
        assert state["recommendations"][1]["category"] == "referral"

    def test_mappings_metadata_assessment(self) -> None:
        """The assessment should be stored in metadata."""
        state = _make_state()
        _map_intelligence_response_to_state(FIXED_RESPONSE, "ACME-001", state)

        assessment = state["metadata"]["fraud_intelligence_assessment"]
        assert assessment["overall_assessment"] == FIXED_RESPONSE.overall_assessment
        assert assessment["confidence"] == 0.87
        assert assessment["investigation_priority"] == "High"
        assert assessment["critical_findings_count"] == 2
        assert assessment["recommended_actions_count"] == 2

    def test_mappings_metadata_risk_mitigating_factors(self) -> None:
        """Risk and mitigating factors should be in the assessment."""
        state = _make_state()
        _map_intelligence_response_to_state(FIXED_RESPONSE, "ACME-001", state)

        assessment = state["metadata"]["fraud_intelligence_assessment"]
        assert len(assessment["risk_factors"]) == 2
        assert len(assessment["mitigating_factors"]) == 1

    def test_mappings_extends_existing_findings(self) -> None:
        """New findings should be appended to existing ones, not replace them."""
        existing = [{"finding_id": "INV-EXISTS-001", "category": "existing"}]
        state = _make_state(ai_findings=existing)
        _map_intelligence_response_to_state(FIXED_RESPONSE, "ACME-001", state)

        assert len(state["ai_findings"]) == 3
        assert state["ai_findings"][0]["finding_id"] == "INV-EXISTS-001"

    def test_mappings_extends_existing_recommendations(self) -> None:
        """New recommendations should be appended to existing ones."""
        existing = [{"recommendation_id": "REC-EXISTS-001", "category": "existing"}]
        state = _make_state(recommendations=existing)
        _map_intelligence_response_to_state(FIXED_RESPONSE, "ACME-001", state)

        assert len(state["recommendations"]) == 3
        assert state["recommendations"][0]["recommendation_id"] == "REC-EXISTS-001"


# ---------------------------------------------------------------------------
# Tests: run_fraud_intelligence_node — happy path (LLM)
# ---------------------------------------------------------------------------


class TestRunFraudIntelligenceNodeLLM:
    """Tests for the LangGraph node with a working LLM provider."""

    def test_status_sets_to_intelligence_complete(self) -> None:
        """Successful analysis should set status to intelligence_complete."""
        state = _make_state()
        provider = MockProvider()
        result = run_fraud_intelligence_node(state, provider=provider)
        assert result["status"] == "intelligence_complete"

    def test_execution_log_has_started_and_completed(self) -> None:
        """The execution_log should have started + completed entries."""
        state = _make_state()
        provider = MockProvider()
        result = run_fraud_intelligence_node(state, provider=provider)
        log = result["execution_log"]
        assert len(log) >= 2
        assert log[0]["status"] == "started"
        assert log[1]["status"] == "completed"

    def test_execution_log_completed_has_source_llm(self) -> None:
        """The completed log entry should include source=llm."""
        state = _make_state()
        provider = MockProvider()
        result = run_fraud_intelligence_node(state, provider=provider)
        log = result["execution_log"]
        completed_entry = log[-1]
        assert "source=llm" in completed_entry["message"]

    def test_findings_are_appended(self) -> None:
        """LLM findings should be appended to existing ai_findings."""
        state = _make_state()
        provider = MockProvider()
        result = run_fraud_intelligence_node(state, provider=provider)
        # 1 existing + 2 new from response
        assert len(result["ai_findings"]) == 3

    def test_recommendations_are_appended(self) -> None:
        """LLM recommendations should be appended to existing."""
        state = _make_state()
        provider = MockProvider()
        result = run_fraud_intelligence_node(state, provider=provider)
        # 0 existing + 2 new
        assert len(result["recommendations"]) == 2

    def test_metadata_assessment_stored(self) -> None:
        """The full assessment should be stored in metadata."""
        state = _make_state()
        provider = MockProvider()
        result = run_fraud_intelligence_node(state, provider=provider)
        assessment = result["metadata"]["fraud_intelligence_assessment"]
        assert assessment["overall_assessment"] == FIXED_RESPONSE.overall_assessment
        assert assessment["confidence"] == 0.87

    def test_llm_exception_triggers_fallback(self) -> None:
        """LLM exceptions should fall back to indicator-based analysis."""
        state = _make_state()
        provider = MockProvider(should_fail=True)
        result = run_fraud_intelligence_node(state, provider=provider)
        assert result["status"] == "intelligence_complete"
        assert len(result["ai_findings"]) >= 1

    def test_provider_id_preserved(self) -> None:
        """The provider_id should be preserved after analysis."""
        state = _make_state(provider_id="PROV-999")
        provider = MockProvider()
        result = run_fraud_intelligence_node(state, provider=provider)
        assert result["provider_id"] == "PROV-999"


# ---------------------------------------------------------------------------
# Tests: run_fraud_intelligence_node — fallback
# ---------------------------------------------------------------------------


class TestRunFraudIntelligenceNodeFallback:
    """Tests for the LangGraph node when the LLM is unavailable."""

    def test_fallback_status(self) -> None:
        """Fallback should still set status to intelligence_complete."""
        state = _make_state()
        provider = MockProvider(should_fail=True)
        result = run_fraud_intelligence_node(state, provider=provider)
        assert result["status"] == "intelligence_complete"

    def test_fallback_adds_finding(self) -> None:
        """Fallback should add an indicator-based finding."""
        state = _make_state(ai_findings=[])
        provider = MockProvider(should_fail=True)
        result = run_fraud_intelligence_node(state, provider=provider)
        assert len(result["ai_findings"]) == 1
        assert result["ai_findings"][0]["category"] == "pending_intelligence_analysis"

    def test_fallback_adds_recommendation(self) -> None:
        """Fallback should add an indicator-based recommendation."""
        state = _make_state(recommendations=[])
        provider = MockProvider(should_fail=True)
        result = run_fraud_intelligence_node(state, provider=provider)
        assert len(result["recommendations"]) == 1
        assert result["recommendations"][0]["category"] == "fraud_intelligence"

    def test_fallback_metadata(self) -> None:
        """Fallback should store an assessment in metadata."""
        state = _make_state()
        provider = MockProvider(should_fail=True)
        result = run_fraud_intelligence_node(state, provider=provider)
        assessment = result["metadata"]["fraud_intelligence_assessment"]
        assert "fallback" in assessment["overall_assessment"].lower()
        assert assessment["source"] == "fallback"
        assert assessment["confidence"] == 0.0

    def test_fallback_risk_factors_from_flagged_indicators(self) -> None:
        """Risk factors should be derived from flagged indicators."""
        state = _make_state(indicators=[
            {"title": "Upcoding", "status": "flagged", "severity": "High",
             "description": "Upcoding detected"},
            {"title": "Normal", "status": "normal", "severity": "Low",
             "description": "All good"},
        ])
        provider = MockProvider(should_fail=True)
        result = run_fraud_intelligence_node(state, provider=provider)
        assessment = result["metadata"]["fraud_intelligence_assessment"]
        assert len(assessment["risk_factors"]) == 1
        assert "Upcoding" in assessment["risk_factors"][0]

    def test_fallback_investigation_priority_from_risk_level(self) -> None:
        """Investigation priority should be derived from risk_level."""
        state = _make_state(risk_level="Critical")
        provider = MockProvider(should_fail=True)
        result = run_fraud_intelligence_node(state, provider=provider)
        assessment = result["metadata"]["fraud_intelligence_assessment"]
        assert assessment["investigation_priority"] == "Immediate"

    def test_fallback_execution_log(self) -> None:
        """The execution_log should have started + completed entries."""
        state = _make_state()
        provider = MockProvider(should_fail=True)
        result = run_fraud_intelligence_node(state, provider=provider)
        log = result["execution_log"]
        assert len(log) >= 2
        assert log[0]["status"] == "started"
        assert log[1]["status"] == "completed"


# ---------------------------------------------------------------------------
# Tests: build_fallback_intelligence helper
# ---------------------------------------------------------------------------


class TestBuildFallbackIntelligence:
    """Tests for the fallback intelligence builder."""

    def test_adds_fallback_finding(self) -> None:
        """Should add a pending_intelligence_analysis finding."""
        state = _make_state(ai_findings=[])
        _build_fallback_intelligence("PROV-001", "High", [], state)
        assert len(state["ai_findings"]) == 1
        assert state["ai_findings"][0]["category"] == "pending_intelligence_analysis"

    def test_adds_fallback_recommendation(self) -> None:
        """Should add a fraud_intelligence recommendation."""
        state = _make_state(recommendations=[])
        _build_fallback_intelligence("PROV-001", "High", [], state)
        assert len(state["recommendations"]) == 1
        assert state["recommendations"][0]["category"] == "fraud_intelligence"

    def test_stores_metadata(self) -> None:
        """Should store the fallback assessment in metadata."""
        state = _make_state()
        _build_fallback_intelligence("PROV-001", "High", [], state)
        assessment = state["metadata"]["fraud_intelligence_assessment"]
        assert assessment["source"] == "fallback"

    def test_risk_level_critical_sets_immediate_priority(self) -> None:
        """Critical risk level should map to Immediate priority."""
        state = _make_state()
        _build_fallback_intelligence("PROV-001", "Critical", [], state)
        assessment = state["metadata"]["fraud_intelligence_assessment"]
        assert assessment["investigation_priority"] == "Immediate"

    def test_unknown_risk_level_defaults_medium(self) -> None:
        """Unknown risk levels should default to Medium priority."""
        state = _make_state()
        _build_fallback_intelligence("PROV-001", "Unknown", [], state)
        assessment = state["metadata"]["fraud_intelligence_assessment"]
        assert assessment["investigation_priority"] == "Medium"


# ---------------------------------------------------------------------------
# Tests: Legacy FraudIntelligenceAgent class
# ---------------------------------------------------------------------------


class TestFraudIntelligenceAgentClass:
    """Tests for the legacy FraudIntelligenceAgent(BaseAgent) class."""

    def test_agent_name(self) -> None:
        """The agent name should be 'fraud_intelligence'."""
        agent = FraudIntelligenceAgent()
        assert agent.name == "fraud_intelligence"

    def test_agent_description(self) -> None:
        """The agent should have a non-empty description."""
        agent = FraudIntelligenceAgent()
        assert len(agent.description) > 0

    def test_agent_stores_provider(self) -> None:
        """The agent should store the provided provider."""
        provider = MockProvider()
        agent = FraudIntelligenceAgent(provider=provider)
        assert agent._provider is provider

    def test_agent_no_provider_initially(self) -> None:
        """The agent should have no provider when constructed without one."""
        agent = FraudIntelligenceAgent()
        assert agent._provider is None

    def test_agent_raises_on_llm_failure(self) -> None:
        """execute() should raise FraudIntelligenceAgentError on LLM failure."""
        agent = FraudIntelligenceAgent(provider=MockProvider(should_fail=True))
        state = {
            "status": "in_progress",
            "claim_id": "CLM-001",
            "error": None,
        }
        with pytest.raises(FraudIntelligenceAgentError, match="LLM call failed"):
            import asyncio
            asyncio.run(agent.execute(state))


# ---------------------------------------------------------------------------
# Tests: Full workflow integration
# ---------------------------------------------------------------------------


class TestWorkflowIntegration:
    """Integration-style tests for the full workflow pipeline."""

    def test_full_workflow_with_llm(self) -> None:
        """Complete workflow with LLM should produce valid output."""
        state = _make_state()
        provider = MockProvider()
        result = run_fraud_intelligence_node(state, provider=provider)

        # Verify final state
        assert result["status"] == "intelligence_complete"
        assert result["claim_id"] == "CLM-TEST-001"
        assert len(result["ai_findings"]) == 3  # 1 existing + 2 new
        assert len(result["recommendations"]) == 2

        # Verify the assessment is in metadata
        assessment = result["metadata"]["fraud_intelligence_assessment"]
        assert "overall_assessment" in assessment
        assert "confidence" in assessment
        assert "risk_factors" in assessment

    def test_full_workflow_fallback(self) -> None:
        """Complete workflow with LLM failure should produce valid output."""
        state = _make_state(ai_findings=[], recommendations=[])
        provider = MockProvider(should_fail=True)
        result = run_fraud_intelligence_node(state, provider=provider)

        assert result["status"] == "intelligence_complete"
        assert len(result["ai_findings"]) == 1
        assert len(result["recommendations"]) == 1
        assessment = result["metadata"]["fraud_intelligence_assessment"]
        assert assessment["source"] == "fallback"

    def test_workflow_preserves_existing_data(self) -> None:
        """Workflow should not overwrite existing state data."""
        state = _make_state(
            ai_findings=[
                {"finding_id": "INV-OLD-0001", "category": "old_finding"}
            ],
            recommendations=[
                {"recommendation_id": "REC-OLD-0001", "category": "old_rec"}
            ],
        )
        provider = MockProvider()
        result = run_fraud_intelligence_node(state, provider=provider)

        # Old data should still be there
        assert result["ai_findings"][0]["finding_id"] == "INV-OLD-0001"
        assert result["recommendations"][0]["recommendation_id"] == "REC-OLD-0001"
        # New data should be appended
        assert len(result["ai_findings"]) == 3
        assert len(result["recommendations"]) == 3

    def test_workflow_empty_state_with_llm(self) -> None:
        """Workflow with completely empty inputs should still succeed."""
        state = _make_state(
            ai_findings=[],
            retrieved_documents=[],
            indicators=[],
            provider_statistics={},
            prediction={},
        )
        provider = MockProvider()
        result = run_fraud_intelligence_node(state, provider=provider)

        assert result["status"] == "intelligence_complete"
        assert len(result["ai_findings"]) == 2
        assert len(result["recommendations"]) == 2
