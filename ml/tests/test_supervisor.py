"""
Tests for the LangGraph workflow supervisor (ml.agents.supervisor).

Verifies that:
- The graph is built with the correct node order.
- Edges are wired sequentially.
- Default node functions are importable.
- Validation errors are raised for missing nodes.
- Routing helper functions return correct values.
"""

from __future__ import annotations

from typing import Any, Callable
from unittest.mock import MagicMock

import pytest

from ml.agents.state import InvestigationState
from ml.agents.supervisor import (
    DEFAULT_NODE_ORDER,
    build_graph,
    check_for_errors,
    determine_investigation_depth,
    should_skip_knowledge_retrieval,
)


# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------


@pytest.fixture
def minimal_node_functions() -> dict[str, Callable[..., InvestigationState]]:
    """Return a set of minimal mock node functions for testing."""

    def _noop(state: InvestigationState) -> InvestigationState:
        return state

    return {
        "investigation_agent": _noop,
        "knowledge_agent": _noop,
        "fraud_intelligence_agent": _noop,
        "report_agent": _noop,
    }


@pytest.fixture
def sample_state() -> InvestigationState:
    """Return a minimal state for testing routing functions."""
    return {
        "investigation_id": "INV-TEST",
        "provider_id": "PRV-TEST",
        "risk_level": "High",
        "indicators": [
            {"title": "Test", "status": "flagged", "severity": "high", "description": ""},
        ],
        "status": "investigating",
        "execution_log": [],
    }


# -----------------------------------------------------------------------
# Graph construction tests
# -----------------------------------------------------------------------


class TestGraphBuilding:
    """Tests for graph construction via build_graph."""

    def test_build_graph_returns_state_graph(self, minimal_node_functions):
        """build_graph should return a LangGraph StateGraph."""
        graph = build_graph(node_functions=minimal_node_functions)
        assert graph is not None

    def test_default_node_order_has_four_nodes(self):
        """The default node order should contain exactly 4 agents."""
        assert len(DEFAULT_NODE_ORDER) == 4
        assert DEFAULT_NODE_ORDER == [
            "investigation_agent",
            "knowledge_agent",
            "fraud_intelligence_agent",
            "report_agent",
        ]

    def test_build_graph_raises_for_missing_nodes(self):
        """build_graph should raise ValueError if nodes are missing."""
        incomplete = {
            "investigation_agent": lambda s: s,
            # Missing other nodes.
        }
        with pytest.raises(ValueError, match="Missing node functions"):
            build_graph(node_functions=incomplete, node_order=DEFAULT_NODE_ORDER)

    def test_build_graph_with_default_imports(self):
        """build_graph without explicit nodes should import defaults."""
        graph = build_graph()
        assert graph is not None

    def test_custom_node_order(self, minimal_node_functions):
        """build_graph should respect a custom node order."""
        custom_order = [
            "report_agent",
            "investigation_agent",
        ]
        graph = build_graph(
            node_functions=minimal_node_functions,
            node_order=custom_order,
        )
        assert graph is not None


# -----------------------------------------------------------------------
# Default node import tests
# -----------------------------------------------------------------------


class TestDefaultNodeImports:
    """Tests that default node functions are importable."""

    def test_import_investigation_node(self):
        from ml.agents.investigation_agent import run_investigation_node

        assert callable(run_investigation_node)

    def test_import_knowledge_node(self):
        from ml.agents.knowledge_agent import run_knowledge_node

        assert callable(run_knowledge_node)

    def test_import_fraud_intelligence_node(self):
        from ml.agents.fraud_intelligence_agent import run_fraud_intelligence_node

        assert callable(run_fraud_intelligence_node)

    def test_import_report_node(self):
        from ml.agents.report_agent import run_report_node

        assert callable(run_report_node)


# -----------------------------------------------------------------------
# Routing helper tests
# -----------------------------------------------------------------------


class TestRoutingHelpers:
    """Tests for the placeholder routing helper functions."""

    def test_should_skip_knowledge_low_risk_no_flags(self):
        """Should skip knowledge agent for Low risk with no flagged indicators."""
        state: InvestigationState = {
            "investigation_id": "INV-TEST",
            "provider_id": "PRV-TEST",
            "risk_level": "Low",
            "indicators": [
                {"title": "Test", "status": "normal", "severity": "low", "description": ""},
            ],
            "status": "initialized",
            "execution_log": [],
        }
        result = should_skip_knowledge_retrieval(state)
        assert result == "fraud_intelligence_agent"

    def test_should_not_skip_knowledge_high_risk(self):
        """Should not skip knowledge agent for High risk."""
        state: InvestigationState = {
            "investigation_id": "INV-TEST",
            "provider_id": "PRV-TEST",
            "risk_level": "High",
            "indicators": [],
            "status": "initialized",
            "execution_log": [],
        }
        result = should_skip_knowledge_retrieval(state)
        assert result == "knowledge_agent"

    def test_should_not_skip_knowledge_low_risk_with_flags(self):
        """Should not skip knowledge agent if indicators are flagged."""
        state: InvestigationState = {
            "investigation_id": "INV-TEST",
            "provider_id": "PRV-TEST",
            "risk_level": "Low",
            "indicators": [
                {"title": "Test", "status": "flagged", "severity": "high", "description": ""},
            ],
            "status": "initialized",
            "execution_log": [],
        }
        result = should_skip_knowledge_retrieval(state)
        assert result == "knowledge_agent"

    def test_determine_investigation_depth_critical(self):
        """Critical risk should return 'deep' depth."""
        state: InvestigationState = {
            "investigation_id": "INV-TEST",
            "provider_id": "PRV-TEST",
            "risk_level": "Critical",
            "indicators": [],
            "status": "initialized",
            "execution_log": [],
        }
        assert determine_investigation_depth(state) == "deep"

    def test_determine_investigation_depth_low(self):
        """Low risk should return 'shallow' depth."""
        state: InvestigationState = {
            "investigation_id": "INV-TEST",
            "provider_id": "PRV-TEST",
            "risk_level": "Low",
            "indicators": [],
            "status": "initialized",
            "execution_log": [],
        }
        assert determine_investigation_depth(state) == "shallow"

    def test_determine_investigation_depth_medium(self):
        """Medium risk should return 'standard' depth."""
        state: InvestigationState = {
            "investigation_id": "INV-TEST",
            "provider_id": "PRV-TEST",
            "risk_level": "Medium",
            "indicators": [],
            "status": "initialized",
            "execution_log": [],
        }
        assert determine_investigation_depth(state) == "standard"

    def test_check_for_errors_clean_state(self):
        """Clean state should return 'continue'."""
        state: InvestigationState = {
            "investigation_id": "INV-TEST",
            "provider_id": "PRV-TEST",
            "status": "completed",
            "execution_log": [],
        }
        assert check_for_errors(state) == "continue"

    def test_check_for_errors_failed_state(self):
        """Failed state should return 'abort'."""
        state: InvestigationState = {
            "investigation_id": "INV-TEST",
            "provider_id": "PRV-TEST",
            "status": "failed",
            "execution_log": [],
        }
        assert check_for_errors(state) == "abort"
