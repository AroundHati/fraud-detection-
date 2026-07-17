"""
Agent framework package for the FraudShield multi-agent system.

This package provides two orchestration interfaces:

**Legacy interface (BaseAgent + SupervisorAgent):**
    Uses ``BaseAgent`` subclasses orchestrated by ``SupervisorAgent``.
    Agents are ``async`` classes with lifecycle hooks, retries, and
    error handling.

    - ``BaseAgent`` — Abstract base class for all agents.
    - ``SupervisorAgent`` — Sequential orchestrator with retries.
    - ``RiskAgent`` — Deterministic risk assessment (fully implemented).
    - ``InvestigationAgent`` — Investigation narratives (skeleton).
    - ``ReportAgent`` — Report assembly (skeleton).

**LangGraph interface (StateGraph + node functions):**
    Uses ``StateGraph`` from LangGraph with standalone node functions
    that operate on ``InvestigationState`` (``TypedDict``).

    - ``InvestigationState`` — TypedDict state schema for the graph.
    - ``run_investigation_node`` — Investigation agent node.
    - ``run_knowledge_node`` — Knowledge retrieval node.
    - ``run_fraud_intelligence_node`` — Fraud intelligence node.
    - ``run_report_node`` — Report assembly node.
    - ``create_workflow`` — Build and compile the LangGraph graph.
    - ``run_workflow`` — Execute the workflow end-to-end.

Both interfaces coexist during the migration period.  The LangGraph
interface is the primary development target for Phase 4 and beyond.
"""

from __future__ import annotations

# -----------------------------------------------------------------------
# Legacy agent framework
# -----------------------------------------------------------------------

from ml.agents.base_agent import BaseAgent, AgentExecutionError
from ml.agents.supervisor_agent import SupervisorAgent, SupervisorError
from ml.agents.risk_agent import RiskAgent, RiskAgentError
from ml.agents.investigation_agent import (
    InvestigationAgent,
    InvestigationAgentError,
)
from ml.agents.report_agent import ReportAgent, ReportAgentError

# -----------------------------------------------------------------------
# LangGraph workflow interface
# -----------------------------------------------------------------------

from ml.agents.state import InvestigationState
from ml.agents.utils import (
    create_initial_state,
    append_log,
    update_status,
    validate_state,
    state_summary,
)
from ml.agents.supervisor import build_graph, DEFAULT_NODE_ORDER
from ml.agents.graph import create_workflow, run_workflow, reset_workflow_cache

# -----------------------------------------------------------------------
# New agent nodes
# -----------------------------------------------------------------------

from ml.agents.knowledge_agent import run_knowledge_node
from ml.agents.fraud_intelligence_agent import run_fraud_intelligence_node

__all__ = [
    # Legacy framework
    "BaseAgent",
    "AgentExecutionError",
    "SupervisorAgent",
    "SupervisorError",
    "RiskAgent",
    "RiskAgentError",
    "InvestigationAgent",
    "InvestigationAgentError",
    "ReportAgent",
    "ReportAgentError",
    # LangGraph state
    "InvestigationState",
    # Utilities
    "create_initial_state",
    "append_log",
    "update_status",
    "validate_state",
    "state_summary",
    # Graph construction
    "build_graph",
    "DEFAULT_NODE_ORDER",
    # Workflow execution
    "create_workflow",
    "run_workflow",
    "reset_workflow_cache",
    # New agent nodes
    "run_knowledge_node",
    "run_fraud_intelligence_node",
]
