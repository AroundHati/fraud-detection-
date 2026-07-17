"""
Utility helpers for the LangGraph investigation workflow.

Provides factory functions for initial state creation, log management,
validation routines, and common state transformations used by every
node in the workflow graph.

All functions in this module are **pure** — they do not perform I/O,
make network calls, or modify global state.  They operate exclusively
on ``InvestigationState`` dicts passed as arguments.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from ml.agents.state import InvestigationState

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# Status constants
# -----------------------------------------------------------------------

STATUS_INITIALIZED: str = "initialized"
"""Initial status when the state is first created."""

STATUS_PIPELINE_COMPLETE: str = "pipeline_complete"
"""Status after feature engineering and prediction are done."""

STATUS_INVESTIGATING: str = "investigating"
"""Status while the Investigation Agent is processing."""

STATUS_KNOWLEDGE_RETRIEVED: str = "knowledge_retrieved"
"""Status after the Knowledge Agent has retrieved documents."""

STATUS_INTELLIGENCE_COMPLETE: str = "intelligence_complete"
"""Status after the Fraud Intelligence Agent completes."""

STATUS_REPORTING: str = "reporting"
"""Status while the Report Agent is assembling the report."""

STATUS_COMPLETED: str = "completed"
"""Status when the entire workflow finishes successfully."""

STATUS_FAILED: str = "failed"
"""Status when the workflow terminates due to an error."""

# -----------------------------------------------------------------------
# Status vocabulary (for validation)
# -----------------------------------------------------------------------

VALID_STATUSES: frozenset[str] = frozenset({
    STATUS_INITIALIZED,
    STATUS_PIPELINE_COMPLETE,
    STATUS_INVESTIGATING,
    STATUS_KNOWLEDGE_RETRIEVED,
    STATUS_INTELLIGENCE_COMPLETE,
    STATUS_REPORTING,
    STATUS_COMPLETED,
    STATUS_FAILED,
})

# -----------------------------------------------------------------------
# State factory
# -----------------------------------------------------------------------


def create_initial_state(
    investigation_id: Optional[str] = None,
    provider_id: str = "",
    csv_data: Any = None,
) -> InvestigationState:
    """Create a fresh ``InvestigationState`` with all fields initialised.

    This is the canonical entry point for workflow initialisation.  It
    generates a unique investigation ID if none is provided, sets the
    initial status, and records a ``"workflow_started"`` timestamp.

    Parameters
    ----------
    investigation_id : str, optional
        Pre-assigned investigation identifier.  If ``None``, a new
        identifier is generated in the format ``INV-XXXXXXXX``.
    provider_id : str
        Identifier of the provider under investigation.
    csv_data : Any
        Raw claims data (typically a ``pandas.DataFrame``).

    Returns
    -------
    InvestigationState
        A fully initialised state dict ready for the workflow graph.

    Examples
    --------
    >>> state = create_initial_state(provider_id="PRV-001", csv_data=df)
    >>> state["status"]
    'initialized'
    >>> state["investigation_id"].startswith("INV-")
    True
    """
    if investigation_id is None:
        investigation_id = f"INV-{uuid4().hex[:8].upper()}"

    now_iso = datetime.now(timezone.utc).isoformat()

    state: InvestigationState = {
        "investigation_id": investigation_id,
        "provider_id": provider_id,
        "csv_data": csv_data,
        "status": STATUS_INITIALIZED,
        "execution_log": [
            _make_log_entry(
                agent_name="system",
                status="started",
                message=f"Workflow initialised for investigation {investigation_id}.",
            )
        ],
        "metadata": {},
        "indicators": [],
        "retrieved_documents": [],
        "ai_findings": [],
        "recommendations": [],
    }

    logger.info(
        "Initial state created — investigation_id=%s provider_id=%s",
        investigation_id,
        provider_id,
    )

    return state


# -----------------------------------------------------------------------
# Log management
# -----------------------------------------------------------------------


def _make_log_entry(
    agent_name: str,
    status: str,
    message: str = "",
    duration_seconds: Optional[float] = None,
    error: Optional[str] = None,
) -> dict[str, Any]:
    """Construct a single execution log entry dict.

    Parameters
    ----------
    agent_name : str
        Name of the agent/node producing this entry.
    status : str
        Event type — ``"started"``, ``"completed"``, ``"failed"``.
    message : str
        Human-readable detail about the event.
    duration_seconds : float, optional
        Wall-clock time for the operation.
    error : str, optional
        Error message if the event represents a failure.

    Returns
    -------
    dict[str, Any]
        A log entry conforming to the ``execution_log`` schema.
    """
    return {
        "agent_name": agent_name,
        "status": status,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": duration_seconds,
        "error": error,
    }


def append_log(
    state: InvestigationState,
    agent_name: str,
    status: str,
    message: str = "",
    duration_seconds: Optional[float] = None,
    error: Optional[str] = None,
) -> InvestigationState:
    """Append a log entry to the state's ``execution_log``.

    This is the primary logging interface for LangGraph nodes.  It
    creates a structured log entry and appends it to the state's
    ``execution_log`` list, ensuring a complete audit trail.

    Parameters
    ----------
    state : InvestigationState
        The current workflow state (mutated in-place and returned).
    agent_name : str
        Name of the agent/node producing this entry.
    status : str
        Event type (``"started"``, ``"completed"``, ``"failed"``).
    message : str
        Human-readable detail about the event.
    duration_seconds : float, optional
        Wall-clock time for the operation.
    error : str, optional
        Error message if the event represents a failure.

    Returns
    -------
    InvestigationState
        The same state dict with the new log entry appended.
    """
    entry = _make_log_entry(
        agent_name=agent_name,
        status=status,
        message=message,
        duration_seconds=duration_seconds,
        error=error,
    )

    log = state.get("execution_log", [])
    log.append(entry)
    state["execution_log"] = log

    logger.info("[%s] %s — %s", agent_name, status, message)
    return state


def update_status(state: InvestigationState, new_status: str) -> InvestigationState:
    """Update the ``status`` field of the workflow state.

    Parameters
    ----------
    state : InvestigationState
        The current workflow state (mutated in-place and returned).
    new_status : str
        The new status value.  Should be one of the ``STATUS_*``
        constants defined in this module.

    Returns
    -------
    InvestigationState
        The same state dict with the updated status.

    Raises
    ------
    ValueError
        If ``new_status`` is not in the valid status vocabulary.
    """
    if new_status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid status '{new_status}'. "
            f"Must be one of: {sorted(VALID_STATUSES)}"
        )

    old_status = state.get("status", "<unset>")
    state["status"] = new_status

    logger.info(
        "Status updated: %s → %s",
        old_status,
        new_status,
    )
    return state


# -----------------------------------------------------------------------
# Node lifecycle helpers
# -----------------------------------------------------------------------


def begin_node(
    state: InvestigationState,
    agent_name: str,
    target_status: str,
) -> float:
    """Standard node entry routine: update status and log ``"started"``.

    This function should be called at the top of every LangGraph node
    function.  It updates the workflow status and appends a start log
    entry, returning the start time for later duration calculation.

    Parameters
    ----------
    state : InvestigationState
        The current workflow state (mutated in-place and returned).
    agent_name : str
        Name of the node/agent being started.
    target_status : str
        The status to set when this node begins execution.

    Returns
    -------
    float
        Start time (from ``time.monotonic()``) for duration calculation.

    Examples
    --------
    >>> def my_node(state: InvestigationState) -> InvestigationState:
    ...     start = begin_node(state, "knowledge", STATUS_KNOWLEDGE_RETRIEVED)
    ...     # ... do work ...
    ...     return complete_node(state, "knowledge", start)
    """
    update_status(state, target_status)
    append_log(
        state,
        agent_name=agent_name,
        status="started",
        message=f"Running {agent_name}",
    )
    return time.monotonic()


def complete_node(
    state: InvestigationState,
    agent_name: str,
    start_time: float,
    extra_message: str = "",
) -> InvestigationState:
    """Standard node exit routine: log ``"completed"`` with duration.

    This function should be called at the end of every LangGraph node
    function (before the ``return``).  It appends a completion log entry
    with the wall-clock duration.

    Parameters
    ----------
    state : InvestigationState
        The current workflow state (mutated in-place and returned).
    agent_name : str
        Name of the node/agent that completed.
    start_time : float
        The start time returned by ``begin_node()``.
    extra_message : str
        Optional additional detail for the log entry.

    Returns
    -------
    InvestigationState
        The same state dict with the completion log entry appended.
    """
    duration = round(time.monotonic() - start_time, 3)
    message = f"{agent_name} completed"
    if extra_message:
        message = f"{message} — {extra_message}"

    append_log(
        state,
        agent_name=agent_name,
        status="completed",
        message=message,
        duration_seconds=duration,
    )
    return state


def fail_node(
    state: InvestigationState,
    agent_name: str,
    start_time: float,
    error: str,
) -> InvestigationState:
    """Standard node failure routine: log ``"failed"`` and update status.

    This function should be called in the ``except`` block of every
    LangGraph node function.  It appends a failure log entry, updates
    the workflow status to ``"failed"``.

    Parameters
    ----------
    state : InvestigationState
        The current workflow state (mutated in-place and returned).
    agent_name : str
        Name of the node/agent that failed.
    start_time : float
        The start time returned by ``begin_node()``.
    error : str
        Description of the error that occurred.

    Returns
    -------
    InvestigationState
        The same state dict with the failure log entry appended.
    """
    duration = round(time.monotonic() - start_time, 3)

    update_status(state, STATUS_FAILED)
    append_log(
        state,
        agent_name=agent_name,
        status="failed",
        message=f"{agent_name} failed",
        duration_seconds=duration,
        error=error,
    )

    return state


# -----------------------------------------------------------------------
# Validation
# -----------------------------------------------------------------------


def validate_state(
    state: InvestigationState,
    *,
    required_fields: Optional[list[str]] = None,
) -> None:
    """Validate that the state contains required fields with truthy values.

    Parameters
    ----------
    state : InvestigationState
        The workflow state to validate.
    required_fields : list[str], optional
        List of field names that must be present and truthy.
        Defaults to ``["investigation_id", "provider_id"]``.

    Raises
    ------
    ValueError
        If any required field is missing or falsy.
    """
    if required_fields is None:
        required_fields = ["investigation_id", "provider_id"]

    missing: list[str] = []
    for field in required_fields:
        value = state.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(field)

    if missing:
        raise ValueError(
            f"State validation failed — missing or empty fields: {missing}"
        )


def validate_pipeline_state(state: InvestigationState) -> None:
    """Validate that pipeline results are present in the state.

    Checks for the presence of ``features``, ``prediction``, ``fraud_score``,
    ``risk_level``, and ``indicators`` fields.

    Raises
    ------
    ValueError
        If any pipeline output field is missing.
    """
    validate_state(state)
    required = ["features", "prediction", "risk_level"]
    missing: list[str] = []
    for field in required:
        value = state.get(field)
        if value is None:
            missing.append(field)

    if missing:
        raise ValueError(
            f"Pipeline output missing — required fields: {missing}"
        )


# -----------------------------------------------------------------------
# Serialization helpers
# -----------------------------------------------------------------------


def state_summary(state: InvestigationState) -> dict[str, Any]:
    """Return a concise, JSON-safe summary of the workflow state.

    Useful for API responses, logging, and debugging.  Large fields
    (``csv_data``, ``features``) are represented by their type name
    and shape rather than full content.

    Parameters
    ----------
    state : InvestigationState
        The workflow state to summarise.

    Returns
    -------
    dict[str, Any]
        A flat dictionary with summary fields.
    """
    summary: dict[str, Any] = {
        "investigation_id": state.get("investigation_id", ""),
        "provider_id": state.get("provider_id", ""),
        "status": state.get("status", ""),
        "execution_log_count": len(state.get("execution_log", [])),
        "indicators_count": len(state.get("indicators", [])),
        "retrieved_documents_count": len(state.get("retrieved_documents", [])),
        "ai_findings_count": len(state.get("ai_findings", [])),
        "recommendations_count": len(state.get("recommendations", [])),
        "has_report": state.get("report") is not None,
    }

    csv_data = state.get("csv_data")
    if csv_data is not None:
        try:
            import pandas as pd

            if isinstance(csv_data, pd.DataFrame):
                summary["csv_data_shape"] = list(csv_data.shape)
            else:
                summary["csv_data_shape"] = "non-dataframe"
        except ImportError:
            summary["csv_data_shape"] = "unknown (pandas not available)"

    features = state.get("features")
    if features is not None:
        try:
            import pandas as pd

            if isinstance(features, pd.DataFrame):
                summary["features_shape"] = list(features.shape)
            else:
                summary["features_shape"] = "non-dataframe"
        except ImportError:
            summary["features_shape"] = "unknown"

    return summary
