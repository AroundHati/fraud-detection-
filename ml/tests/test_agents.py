"""
Tests for the LangGraph agent node functions.

Verifies that:
- Each node function accepts InvestigationState and returns InvestigationState.
- Each node appends entries to execution_log.
- Each node updates the status field.
- Nodes produce placeholder outputs in the correct schema.
- Nodes handle missing input data gracefully.
- Nodes produce deterministic outputs (no randomness).
"""

from __future__ import annotations

import pytest

from ml.agents.fraud_intelligence_agent import run_fraud_intelligence_node
from ml.agents.investigation_agent import run_investigation_node
from ml.agents.knowledge_agent import run_knowledge_node
from ml.agents.report_agent import run_report_node
from ml.agents.state import InvestigationState
from ml.agents.utils import (
    STATUS_COMPLETED,
    STATUS_INTELLIGENCE_COMPLETE,
    STATUS_INVESTIGATING,
    STATUS_KNOWLEDGE_RETRIEVED,
    STATUS_REPORTING,
    create_initial_state,
)


# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------


@pytest.fixture
def base_state() -> InvestigationState:
    """Create a base state with pipeline outputs for agent testing."""
    state = create_initial_state(
        investigation_id="INV-AGENT-TEST",
        provider_id="PRV-AGENT-TEST",
    )
    state["features"] = {"TotalClaims": 200}
    state["prediction"] = {
        "provider_id": "PRV-AGENT-TEST",
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


# -----------------------------------------------------------------------
# Investigation Agent Node Tests
# -----------------------------------------------------------------------


class TestInvestigationAgentNode:
    """Tests for run_investigation_node."""

    def test_returns_investigation_state(self, base_state):
        """The node should return an InvestigationState dict."""
        result = run_investigation_node(base_state)
        assert isinstance(result, dict)
        assert "investigation_id" in result

    def test_updates_status(self, base_state):
        """The node should update status to 'investigating' (then beyond)."""
        result = run_investigation_node(base_state)
        # After investigation completes, status should not be 'initialized'.
        assert result["status"] != "initialized"

    def test_appends_to_execution_log(self, base_state):
        """The node should append at least 2 entries to execution_log."""
        initial_count = len(base_state.get("execution_log", []))
        result = run_investigation_node(base_state)
        final_count = len(result.get("execution_log", []))
        assert final_count >= initial_count + 2

    def test_log_entries_have_correct_agent_name(self, base_state):
        """Log entries should reference 'investigation_agent'."""
        result = run_investigation_node(base_state)
        agent_entries = [
            e for e in result["execution_log"]
            if e.get("agent_name") == "investigation_agent"
        ]
        assert len(agent_entries) >= 2  # started + completed

    def test_populates_ai_findings(self, base_state):
        """The node should populate ai_findings with placeholder data."""
        result = run_investigation_node(base_state)
        assert len(result.get("ai_findings", [])) > 0
        finding = result["ai_findings"][0]
        assert "finding_id" in finding
        assert "category" in finding
        assert "severity" in finding
        assert "description" in finding

    def test_populates_recommendations(self, base_state):
        """The node should add recommendations for flagged indicators."""
        result = run_investigation_node(base_state)
        assert len(result.get("recommendations", [])) > 0

    def test_preserves_investigation_id(self, base_state):
        """The investigation ID should not change."""
        result = run_investigation_node(base_state)
        assert result["investigation_id"] == "INV-AGENT-TEST"

    def test_handles_missing_pipeline_data(self):
        """The node should handle missing pipeline outputs gracefully."""
        state = create_initial_state(provider_id="PRV-EMPTY")
        result = run_investigation_node(state)
        # Should fail but not crash — status should be 'failed'.
        assert result["status"] == "failed"
        # Error should be in execution log.
        error_entries = [
            e for e in result["execution_log"] if e.get("error")
        ]
        assert len(error_entries) > 0

    def test_deterministic_output(self, base_state):
        """Running the node twice with the same state should produce the same output."""
        import copy

        state1 = copy.deepcopy(base_state)
        state2 = copy.deepcopy(base_state)
        result1 = run_investigation_node(state1)
        result2 = run_investigation_node(state2)
        # Same findings count and categories.
        assert len(result1["ai_findings"]) == len(result2["ai_findings"])
        assert (
            result1["ai_findings"][0]["category"]
            == result2["ai_findings"][0]["category"]
        )


# -----------------------------------------------------------------------
# Knowledge Agent Node Tests
# -----------------------------------------------------------------------


class TestKnowledgeAgentNode:
    """Tests for run_knowledge_node."""

    def test_returns_investigation_state(self, base_state):
        """The node should return an InvestigationState dict."""
        # First run investigation to populate ai_findings.
        state = run_investigation_node(base_state)
        result = run_knowledge_node(state)
        assert isinstance(result, dict)

    def test_updates_status(self, base_state):
        """The node should update status to 'knowledge_retrieved'."""
        state = run_investigation_node(base_state)
        result = run_knowledge_node(state)
        assert result["status"] == STATUS_KNOWLEDGE_RETRIEVED

    def test_appends_to_execution_log(self, base_state):
        """The node should append entries to execution_log."""
        state = run_investigation_node(base_state)
        initial_count = len(state["execution_log"])
        result = run_knowledge_node(state)
        final_count = len(result["execution_log"])
        assert final_count >= initial_count + 2

    def test_populates_retrieved_documents(self, base_state):
        """The node should populate retrieved_documents."""
        state = run_investigation_node(base_state)
        result = run_knowledge_node(state)
        docs = result.get("retrieved_documents", [])
        assert len(docs) > 0
        for doc in docs:
            assert "source" in doc
            assert "content" in doc
            assert "relevance_score" in doc

    def test_adds_recommendations(self, base_state):
        """The node should add knowledge retrieval recommendations."""
        state = run_investigation_node(base_state)
        initial_rec_count = len(state.get("recommendations", []))
        result = run_knowledge_node(state)
        assert len(result["recommendations"]) >= initial_rec_count


# -----------------------------------------------------------------------
# Fraud Intelligence Agent Node Tests
# -----------------------------------------------------------------------


class TestFraudIntelligenceAgentNode:
    """Tests for run_fraud_intelligence_node."""

    def test_returns_investigation_state(self, base_state):
        """The node should return an InvestigationState dict."""
        state = run_investigation_node(base_state)
        state = run_knowledge_node(state)
        result = run_fraud_intelligence_node(state)
        assert isinstance(result, dict)

    def test_updates_status(self, base_state):
        """The node should update status to 'intelligence_complete'."""
        state = run_investigation_node(base_state)
        state = run_knowledge_node(state)
        result = run_fraud_intelligence_node(state)
        assert result["status"] == STATUS_INTELLIGENCE_COMPLETE

    def test_appends_to_execution_log(self, base_state):
        """The node should append entries to execution_log."""
        state = run_investigation_node(base_state)
        state = run_knowledge_node(state)
        initial_count = len(state["execution_log"])
        result = run_fraud_intelligence_node(state)
        final_count = len(result["execution_log"])
        assert final_count >= initial_count + 2

    def test_enriches_ai_findings(self, base_state):
        """The node should add an intelligence finding to ai_findings."""
        state = run_investigation_node(base_state)
        state = run_knowledge_node(state)
        initial_findings = len(state["ai_findings"])
        result = run_fraud_intelligence_node(state)
        assert len(result["ai_findings"]) >= initial_findings

    def test_consolidates_recommendations(self, base_state):
        """The node should add intelligence-level recommendations."""
        state = run_investigation_node(base_state)
        state = run_knowledge_node(state)
        initial_rec_count = len(state["recommendations"])
        result = run_fraud_intelligence_node(state)
        assert len(result["recommendations"]) >= initial_rec_count


# -----------------------------------------------------------------------
# Report Agent Node Tests
# -----------------------------------------------------------------------


class TestReportAgentNode:
    """Tests for run_report_node."""

    def test_returns_investigation_state(self, base_state):
        """The node should return an InvestigationState dict."""
        state = run_investigation_node(base_state)
        state = run_knowledge_node(state)
        state = run_fraud_intelligence_node(state)
        result = run_report_node(state)
        assert isinstance(result, dict)

    def test_updates_status_to_completed(self, base_state):
        """The node should update status to 'completed'."""
        state = run_investigation_node(base_state)
        state = run_knowledge_node(state)
        state = run_fraud_intelligence_node(state)
        result = run_report_node(state)
        assert result["status"] == STATUS_COMPLETED

    def test_populates_report(self, base_state):
        """The node should populate the report field."""
        state = run_investigation_node(base_state)
        state = run_knowledge_node(state)
        state = run_fraud_intelligence_node(state)
        result = run_report_node(state)
        report = result.get("report")
        assert report is not None
        assert "metadata" in report
        assert "sections" in report
        assert "executive_summary" in report

    def test_report_metadata_has_investigation_id(self, base_state):
        """The report metadata should reference the investigation ID."""
        state = run_investigation_node(base_state)
        state = run_knowledge_node(state)
        state = run_fraud_intelligence_node(state)
        result = run_report_node(state)
        meta = result["report"]["metadata"]
        assert meta["investigation_id"] == "INV-AGENT-TEST"

    def test_report_has_multiple_sections(self, base_state):
        """The report should contain multiple sections."""
        state = run_investigation_node(base_state)
        state = run_knowledge_node(state)
        state = run_fraud_intelligence_node(state)
        result = run_report_node(state)
        assert len(result["report"]["sections"]) >= 3

    def test_workflow_end_log_present(self, base_state):
        """The execution log should contain a 'workflow' completed entry."""
        state = run_investigation_node(base_state)
        state = run_knowledge_node(state)
        state = run_fraud_intelligence_node(state)
        result = run_report_node(state)
        workflow_entries = [
            e for e in result["execution_log"]
            if e.get("agent_name") == "workflow"
        ]
        assert len(workflow_entries) > 0


# -----------------------------------------------------------------------
# Full pipeline integration test
# -----------------------------------------------------------------------


class TestFullPipelineIntegration:
    """Integration test: run all four nodes in sequence."""

    def test_full_pipeline(self, base_state):
        """All four agents should execute in sequence and produce a complete result."""
        state = base_state

        # Step 1: Investigation Agent.
        state = run_investigation_node(state)
        assert state["status"] == STATUS_INVESTIGATING or len(state["ai_findings"]) > 0

        # Step 2: Knowledge Agent.
        state = run_knowledge_node(state)
        assert state["status"] == STATUS_KNOWLEDGE_RETRIEVED
        assert len(state["retrieved_documents"]) > 0

        # Step 3: Fraud Intelligence Agent.
        state = run_fraud_intelligence_node(state)
        assert state["status"] == STATUS_INTELLIGENCE_COMPLETE

        # Step 4: Report Agent.
        state = run_report_node(state)
        assert state["status"] == STATUS_COMPLETED
        assert state["report"] is not None

        # Verify execution log.
        assert len(state["execution_log"]) >= 8  # At least start+end for each node.

        # Verify no errors in log (happy path).
        errors = [e for e in state["execution_log"] if e.get("error")]
        assert len(errors) == 0
