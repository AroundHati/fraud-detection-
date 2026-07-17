"""
LangGraph workflow definition and execution for FraudShield.

This module provides the public API for creating and running the
multi-agent investigation workflow.  It wraps the LangGraph
``StateGraph`` construction, compilation, and execution into
two simple functions:

- ``create_workflow()`` — builds and compiles the graph (call once).
- ``run_workflow(state)`` — executes the compiled graph (call per investigation).

Architecture
------------
::

    START
      │
      ▼
  ┌─────────────────────┐
  │ Investigation Agent  │  ← Validates pipeline output, produces initial findings
  └──────────┬──────────┘
             │
             ▼
  ┌─────────────────────┐
  │   Knowledge Agent    │  ← Retrieves regulatory and case context
  └──────────┬──────────┘
             │
             ▼
  ┌──────────────────────────┐
  │ Fraud Intelligence Agent  │  ← Deep analysis, pattern matching, impact estimation
  └──────────┬───────────────┘
             │
             ▼
  ┌─────────────────────┐
  │    Report Agent      │  ← Assembles final report for PDF generation
  └──────────┬──────────┘
             │
             ▼
            END

The graph is compiled once and reused for every investigation run.
LangGraph handles state threading, checkpointing (if configured),
and error propagation between nodes.

Usage
-----
::

    from ml.agents.graph import create_workflow, run_workflow
    from ml.agents.utils import create_initial_state

    # Create and compile the workflow (once at startup).
    workflow = create_workflow()

    # Initialise state for a new investigation.
    state = create_initial_state(provider_id="PRV-001", csv_data=df)

    # Run the workflow.
    final_state = run_workflow(state, workflow=workflow)

    # Inspect results.
    print(final_state["report"])
    print(final_state["execution_log"])

Future Enhancements
-------------------
- Conditional routing based on risk level (Phase 4F).
- Parallel execution of independent nodes (e.g. Knowledge and Investigation).
- Checkpointing for long-running workflows.
- Human-in-the-loop interruption points.
- Streaming state updates for real-time UI feedback.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

from langgraph.graph import StateGraph

from ml.agents.state import InvestigationState
from ml.agents.supervisor import build_graph
from ml.agents.utils import (
    STATUS_FAILED,
    STATUS_INITIALIZED,
    append_log,
    create_initial_state,
    update_status,
)

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# Module-level compiled graph cache
# -----------------------------------------------------------------------

_compiled_graph: Any = None
"""Cached compiled graph instance.

Initialised lazily by ``create_workflow()`` and reused for all
subsequent ``run_workflow()`` calls.  Set to ``None`` to force
recompilation.
"""


# -----------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------


def create_workflow(
    *,
    force_recompile: bool = False,
) -> Any:
    """Build, compile, and cache the investigation workflow graph.

    This function constructs the LangGraph ``StateGraph``, registers
    all agent nodes, wires the sequential edges, and compiles the
    graph.  The compiled graph is cached at module level for reuse.

    Parameters
    ----------
    force_recompile : bool
        If ``True``, discards any cached compiled graph and rebuilds
        from scratch.  Defaults to ``False``.

    Returns
    -------
    CompiledGraph
        A compiled LangGraph graph ready for execution via ``invoke()``
        or ``ainvoke()``.

    Examples
    --------
    >>> workflow = create_workflow()
    >>> print(type(workflow))
    <class 'langgraph.graph.state.CompiledStateGraph'>
    """
    global _compiled_graph

    if _compiled_graph is not None and not force_recompile:
        logger.debug("Returning cached compiled workflow.")
        return _compiled_graph

    logger.info("Building and compiling investigation workflow graph.")

    graph: StateGraph = build_graph()
    _compiled_graph = graph.compile()

    logger.info("Workflow graph compiled successfully.")
    return _compiled_graph


def run_workflow(
    initial_state: InvestigationState,
    *,
    workflow: Optional[Any] = None,
) -> InvestigationState:
    """Execute the investigation workflow on the given initial state.

    This is the primary entry point for running an end-to-end
    investigation.  It compiles the workflow (if not already cached),
    invokes it with the provided state, and returns the final state.

    Parameters
    ----------
    initial_state : InvestigationState
        The initial workflow state.  Typically created via
        ``create_initial_state()`` with pipeline results already
        populated in the ``features``, ``prediction``, ``fraud_score``,
        ``risk_level``, and ``indicators`` fields.
    workflow : CompiledGraph, optional
        A pre-compiled LangGraph graph.  If ``None``, the cached
        or default workflow is used.

    Returns
    -------
    InvestigationState
        The final workflow state after all nodes have executed.
        Contains populated ``ai_findings``, ``retrieved_documents``,
        ``recommendations``, ``report``, and a complete
        ``execution_log``.

    Raises
    ------
    RuntimeError
        If the workflow execution fails catastrophically (e.g. a node
        raises an unhandled exception that is not caught by the node's
        own error handling).

    Examples
    --------
    >>> from ml.agents.utils import create_initial_state
    >>> state = create_initial_state(provider_id="PRV-001", csv_data=df)
    >>> state["risk_level"] = "High"
    >>> state["indicators"] = [{"title": "Test", "status": "flagged", ...}]
    >>> final = run_workflow(state)
    >>> print(final["status"])
    'completed'
    """
    start_time = time.monotonic()

    # Ensure we have a compiled workflow.
    if workflow is None:
        workflow = create_workflow()

    logger.info(
        "Running workflow — investigation_id=%s provider_id=%s",
        initial_state.get("investigation_id", "unknown"),
        initial_state.get("provider_id", "unknown"),
    )

    # Add workflow start log entry.
    append_log(
        initial_state,
        agent_name="workflow",
        status="started",
        message="LangGraph workflow execution starting.",
    )

    try:
        # Execute the graph synchronously via invoke().
        # LangGraph handles state threading internally.
        final_state_dict: dict[str, Any] = workflow.invoke(initial_state)

        # The result is a plain dict (LangGraph unwraps TypedDict).
        # Cast back to InvestigationState.
        final_state: InvestigationState = final_state_dict  # type: ignore[assignment]

        duration = round(time.monotonic() - start_time, 3)

        # If the report node didn't mark as completed (defensive), do it.
        if final_state.get("status") not in (STATUS_FAILED, "completed"):
            final_state["status"] = "completed"

        append_log(
            final_state,
            agent_name="workflow",
            status="completed",
            message=f"LangGraph workflow finished in {duration}s.",
            duration_seconds=duration,
        )

        logger.info(
            "Workflow completed — investigation_id=%s duration=%ss "
            "log_entries=%d",
            final_state.get("investigation_id", "unknown"),
            duration,
            len(final_state.get("execution_log", [])),
        )

        return final_state

    except Exception as exc:
        duration = round(time.monotonic() - start_time, 3)

        # Update the original state with failure information.
        # We can't rely on LangGraph's state after an unhandled error.
        update_status(initial_state, STATUS_FAILED)
        append_log(
            initial_state,
            agent_name="workflow",
            status="failed",
            message=f"Workflow failed: {exc}",
            duration_seconds=duration,
            error=str(exc),
        )

        logger.exception(
            "Workflow failed — investigation_id=%s duration=%ss error=%s",
            initial_state.get("investigation_id", "unknown"),
            duration,
            exc,
        )

        return initial_state


def reset_workflow_cache() -> None:
    """Discard the cached compiled workflow graph.

    Call this to force recompilation on the next ``create_workflow()``
    call.  Useful during development or when node functions are
    modified at runtime.
    """
    global _compiled_graph
    _compiled_graph = None
    logger.info("Workflow cache reset.")
