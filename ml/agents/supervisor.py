"""
Workflow supervisor for the LangGraph investigation graph.

The supervisor defines the deterministic routing logic that controls
the order in which agent nodes execute.  In this phase (4B), routing
is strictly sequential:

    Investigation Agent → Knowledge Agent → Fraud Intelligence Agent → Report Agent

In future phases, the supervisor will support conditional routing
based on state conditions (e.g. skipping the Knowledge Agent if no
documents are relevant, or branching to different analysis paths
based on risk level).

Design Notes
------------
This module is intentionally separate from ``supervisor_agent.py``
(the legacy ``BaseAgent``-based orchestrator).  The LangGraph
supervisor defines *graph topology* (which nodes connect to which),
while the legacy supervisor defines *execution semantics* (retries,
error handling, lifecycle hooks).  They serve different purposes and
will coexist until the legacy pipeline is fully migrated to LangGraph.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional, Sequence

from langgraph.graph import END, StateGraph

from ml.agents.state import InvestigationState
from ml.agents.utils import STATUS_FAILED

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# Default workflow node order
# -----------------------------------------------------------------------

DEFAULT_NODE_ORDER: list[str] = [
    "investigation_agent",
    "knowledge_agent",
    "fraud_intelligence_agent",
    "report_agent",
]
"""Default sequential execution order for the investigation workflow.

This list defines the deterministic routing path.  Each entry
corresponds to a registered LangGraph node.  The ``build_graph``
function wires these nodes in order with linear edges.
"""


# -----------------------------------------------------------------------
# Graph builder
# -----------------------------------------------------------------------


def build_graph(
    node_functions: Optional[dict[str, Callable[..., InvestigationState]]] = None,
    *,
    node_order: Optional[Sequence[str]] = None,
) -> StateGraph:
    """Build the LangGraph ``StateGraph`` with deterministic sequential routing.

    Constructs a linear graph where each node feeds into the next,
    terminated by LangGraph's ``END`` node.  No conditional edges
    are added in this phase.

    Parameters
    ----------
    node_functions : dict[str, Callable], optional
        Mapping of node names to their callable functions.  If ``None``,
        the default node functions are imported and used.
    node_order : Sequence[str], optional
        Ordered sequence of node names.  Defaults to
        ``DEFAULT_NODE_ORDER``.

    Returns
    -------
    StateGraph
        An uncompiled LangGraph ``StateGraph`` ready for compilation.

    Raises
    ------
    ValueError
        If ``node_functions`` is provided but is missing a node name
        listed in ``node_order``.

    Examples
    --------
    >>> from ml.agents.supervisor import build_graph
    >>> graph = build_graph()
    >>> compiled = graph.compile()
    """
    if node_order is None:
        node_order = DEFAULT_NODE_ORDER

    if node_functions is None:
        node_functions = _import_default_nodes()

    # Validate that all required nodes are present.
    missing = [n for n in node_order if n not in node_functions]
    if missing:
        raise ValueError(
            f"Missing node functions for: {missing}. "
            f"Available: {list(node_functions.keys())}"
        )

    # Build the graph.
    graph = StateGraph(InvestigationState)

    for node_name in node_order:
        graph.add_node(node_name, node_functions[node_name])
        logger.debug("Graph node added: %s", node_name)

    # Wire linear edges: START → node_0 → node_1 → ... → END.
    # LangGraph's StateGraph starts with an implicit START node.
    graph.set_entry_point(node_order[0])

    for i in range(len(node_order) - 1):
        graph.add_edge(node_order[i], node_order[i + 1])
        logger.debug("Graph edge: %s → %s", node_order[i], node_order[i + 1])

    # Terminal edge.
    graph.add_edge(node_order[-1], END)

    logger.info(
        "Graph built — nodes=%s edges=%d",
        node_order,
        len(node_order),
    )

    return graph


# -----------------------------------------------------------------------
# Default node import
# -----------------------------------------------------------------------


def _import_default_nodes() -> dict[str, Callable[..., InvestigationState]]:
    """Import the default LangGraph node functions.

    Returns
    -------
    dict[str, Callable]
        Mapping of node names to their callable functions.

    Raises
    ------
    ImportError
        If any node module cannot be imported.
    """
    from ml.agents.fraud_intelligence_agent import run_fraud_intelligence_node
    from ml.agents.investigation_agent import run_investigation_node
    from ml.agents.knowledge_agent import run_knowledge_node
    from ml.agents.report_agent import run_report_node

    nodes: dict[str, Callable[..., InvestigationState]] = {
        "investigation_agent": run_investigation_node,
        "knowledge_agent": run_knowledge_node,
        "fraud_intelligence_agent": run_fraud_intelligence_node,
        "report_agent": run_report_node,
    }

    logger.debug("Default node functions imported — %d nodes.", len(nodes))
    return nodes


# -----------------------------------------------------------------------
# Routing helpers (for future conditional routing)
# -----------------------------------------------------------------------


def should_skip_knowledge_retrieval(state: InvestigationState) -> str:
    """Determine whether the Knowledge Agent should be skipped.

    This is a **placeholder** routing function for future conditional
    routing.  In the current sequential workflow, this function is
    not used — all nodes always execute.

    Parameters
    ----------
    state : InvestigationState
        The current workflow state.

    Returns
    -------
    str
        ``"knowledge_agent"`` to proceed, or ``"fraud_intelligence_agent"``
        to skip directly to the Intelligence Agent.
    """
    # TODO: Phase 4F — Implement conditional routing.
    # Skip knowledge retrieval if risk level is Low and no indicators
    # are flagged.
    risk_level = state.get("risk_level", "unknown")
    indicators = state.get("indicators", [])

    if risk_level == "Low" and not any(
        isinstance(i, dict) and i.get("status") == "flagged"
        for i in indicators
    ):
        logger.info(
            "Routing: skipping knowledge_agent (risk=Low, no flagged indicators)"
        )
        return "fraud_intelligence_agent"

    return "knowledge_agent"


def determine_investigation_depth(state: InvestigationState) -> str:
    """Determine the investigation depth based on risk level.

    This is a **placeholder** routing function for future conditional
    routing.  In the current sequential workflow, this function is
    not used.

    Parameters
    ----------
    state : InvestigationState
        The current workflow state.

    Returns
    -------
    str
        Investigation depth level (``"shallow"``, ``"standard"``,
        ``"deep"``).
    """
    # TODO: Phase 4F — Implement depth-based routing.
    risk_level = state.get("risk_level", "unknown")

    depth_map: dict[str, str] = {
        "Critical": "deep",
        "High": "deep",
        "Medium": "standard",
        "Low": "shallow",
    }

    depth = depth_map.get(risk_level, "standard")
    logger.info("Determined investigation depth: %s (risk=%s)", depth, risk_level)
    return depth


# -----------------------------------------------------------------------
# Error-aware edge function (for future use)
# -----------------------------------------------------------------------


def check_for_errors(state: InvestigationState) -> str:
    """Route to END if a critical error is detected.

    This is a **placeholder** routing function for future conditional
    routing.  In the current sequential workflow, all nodes run
    regardless of errors (errors are logged and execution continues).

    Parameters
    ----------
    state : InvestigationState
        The current workflow state.

    Returns
    -------
    str
        ``"continue"`` or ``"abort"``.
    """
    # TODO: Phase 4F — Implement error-aware routing.
    if state.get("status") == STATUS_FAILED:
        logger.warning("Error routing: workflow status is 'failed'")
        return "abort"
    return "continue"
