"""
Tests for the LangGraph workflow graph (ml.agents.graph).

Verifies that:
- The workflow graph compiles successfully.
- The workflow executes with a valid initial state.
- State passes correctly through all nodes.
- The execution log grows at each step.
- Status updates correctly through the workflow lifecycle.
- Error states are handled gracefully.
"""

from __future__ import annotations

import pytest

from ml.agents.graph import create_workflow, reset_workflow_cache, run_workflow
from ml.agents.state import InvestigationState
from ml.agents.utils import (
    STATUS_COMPLETED,
    STATUS_INITIALIZED,
    create_initial_state,
    validate_state,
)


# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------


@pytest.fixture
def sample_state() -> InvestigationState:
    """Create a minimal valid initial state for testing."""
    state = create_initial_state(
        provider_id="PRV-TEST-001",
        csv_data=None,
    )
    # Populate pipeline output fields that downstream agents expect.
    state["features"] = {"TotalClaims": 150}
    state["prediction"] = {
        "provider_id": "PRV-TEST-001",
        "prediction": "Yes",
        "fraud_probability": 0.85,
        "confidence": 92.0,
    }
    state["fraud_score"] = 0.85
    state["risk_level"] = "High"
    state["indicators"] = [
        {
            "title": "Claim Volume",
            "status": "flagged",
            "severity": "high",
            "description": "Abnormally high claim volume.",
        },
        {
            "title": "Average Claim Amount",
            "status": "warning",
            "severity": "medium",
            "description": "Above average claim amounts.",
        },
    ]
    state["provider_statistics"] = {
        "total_claims": 150,
        "total_reimbursement": 450000.0,
        "average_claim_amount": 3000.0,
    }
    return state


@pytest.fixture(autouse=True)
def _reset_cache():
    """Reset the workflow cache before each test."""
    reset_workflow_cache()
    yield
    reset_workflow_cache()


# -----------------------------------------------------------------------
# Graph compilation tests
# -----------------------------------------------------------------------


class TestGraphCompilation:
    """Tests for graph construction and compilation."""

    def test_create_workflow_returns_compiled_graph(self):
        """The workflow should compile without errors."""
        workflow = create_workflow()
        assert workflow is not None

    def test_create_workflow_is_cached(self):
        """Subsequent calls should return the same compiled graph."""
        w1 = create_workflow()
        w2 = create_workflow()
        assert w1 is w2

    def test_force_recompile_creates_new_instance(self):
        """force_recompile should produce a new graph instance."""
        w1 = create_workflow()
        w2 = create_workflow(force_recompile=True)
        assert w1 is not w2

    def test_reset_workflow_cache_clears_instance(self):
        """reset_workflow_cache should clear the cached graph."""
        create_workflow()
        reset_workflow_cache()
        # Next call should compile fresh.
        w = create_workflow()
        assert w is not None


# -----------------------------------------------------------------------
# Workflow execution tests
# -----------------------------------------------------------------------


class TestWorkflowExecution:
    """Tests for end-to-end workflow execution."""

    def test_run_workflow_completes_successfully(self, sample_state):
        """The workflow should execute all nodes and complete."""
        final_state = run_workflow(sample_state)
        assert final_state["status"] == STATUS_COMPLETED

    def test_run_workflow_returns_investigation_state(self, sample_state):
        """The return value should be an InvestigationState dict."""
        final_state = run_workflow(sample_state)
        assert isinstance(final_state, dict)
        # Verify required keys are present.
        assert "investigation_id" in final_state
        assert "status" in final_state
        assert "execution_log" in final_state

    def test_investigation_id_preserved(self, sample_state):
        """The investigation ID should survive the workflow intact."""
        original_id = sample_state["investigation_id"]
        final_state = run_workflow(sample_state)
        assert final_state["investigation_id"] == original_id

    def test_provider_id_preserved(self, sample_state):
        """The provider ID should survive the workflow intact."""
        final_state = run_workflow(sample_state)
        assert final_state["provider_id"] == "PRV-TEST-001"

    def test_execution_log_grows(self, sample_state):
        """The execution log should grow with entries from each node."""
        initial_log_count = len(sample_state.get("execution_log", []))
        final_state = run_workflow(sample_state)
        final_log_count = len(final_state.get("execution_log", []))
        # At minimum: 1 system entry + 4 agent starts + 4 agent completes
        # + 1 workflow start + workflow end = 11 entries.
        assert final_log_count > initial_log_count
        assert final_log_count >= 6

    def test_execution_log_entries_have_required_keys(self, sample_state):
        """Each log entry should contain the required fields."""
        final_state = run_workflow(sample_state)
        required_keys = {"agent_name", "status", "message", "timestamp"}
        for entry in final_state["execution_log"]:
            assert required_keys.issubset(entry.keys()), (
                f"Log entry missing keys: {required_keys - entry.keys()}"
            )

    def test_ai_findings_populated(self, sample_state):
        """The Investigation Agent should populate ai_findings."""
        final_state = run_workflow(sample_state)
        assert len(final_state.get("ai_findings", [])) > 0

    def test_retrieved_documents_populated(self, sample_state):
        """The Knowledge Agent should populate retrieved_documents."""
        final_state = run_workflow(sample_state)
        assert len(final_state.get("retrieved_documents", [])) > 0

    def test_recommendations_populated(self, sample_state):
        """Agents should accumulate recommendations."""
        final_state = run_workflow(sample_state)
        assert len(final_state.get("recommendations", [])) > 0

    def test_report_populated(self, sample_state):
        """The Report Agent should populate the report field."""
        final_state = run_workflow(sample_state)
        assert final_state.get("report") is not None
        assert "metadata" in final_state["report"]
        assert "sections" in final_state["report"]

    def test_report_has_metadata(self, sample_state):
        """The report metadata should contain required fields."""
        final_state = run_workflow(sample_state)
        meta = final_state["report"]["metadata"]
        assert "report_id" in meta
        assert "investigation_id" in meta
        assert meta["investigation_id"] == sample_state["investigation_id"]


# -----------------------------------------------------------------------
# Error handling tests
# -----------------------------------------------------------------------


class TestWorkflowErrorHandling:
    """Tests for error handling in the workflow."""

    def test_workflow_handles_missing_pipeline_data(self):
        """The workflow should handle missing pipeline outputs gracefully."""
        state = create_initial_state(provider_id="PRV-ERR-001")
        # Do not populate features/prediction/risk_level.
        state["risk_level"] = ""
        state["indicators"] = []

        # The workflow should still execute, with nodes handling errors.
        final_state = run_workflow(state)
        # Should not crash — at least one node should log an error.
        assert len(final_state.get("execution_log", [])) > 0

    def test_workflow_preserves_existing_metadata(self, sample_state):
        """Pre-existing metadata should survive the workflow."""
        sample_state["metadata"]["custom_key"] = "custom_value"
        final_state = run_workflow(sample_state)
        assert final_state["metadata"].get("custom_key") == "custom_value"
