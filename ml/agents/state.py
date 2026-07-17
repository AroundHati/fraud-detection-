"""
Shared investigation state for the LangGraph multi-agent workflow.

This module defines ``InvestigationState``, a ``TypedDict`` that serves
as the single source of truth for all data flowing through the LangGraph
workflow graph.  Every node (agent) reads from and writes to this state,
ensuring a clean, auditable data lineage from raw CSV ingestion through
to the final report.

Design Principles
-----------------
1. **TypedDict, not Pydantic.**  LangGraph's ``StateGraph`` expects
   ``TypedDict`` (or a ``pydantic.BaseModel`` that inherits from
   ``TypedDict``).  We use ``TypedDict`` directly to keep the state
   schema lightweight, serialisable, and free of validation overhead
   during graph execution.

2. **Progressive population.**  Fields are added to the state
   incrementally as each agent completes its work.  The initial state
   contains only identifiers and raw input data; pipeline outputs,
   agent findings, and report content are populated sequentially.

3. **Backward-compatible with Pydantic schemas.**  Although the LangGraph
   state is a ``TypedDict``, the *values* stored in shared fields
   (``risk_assessment``, ``investigation_summary``, ``report``) are the
   same Pydantic models used by the existing ``BaseAgent`` pipeline.
   This enables seamless integration between the legacy agent framework
   and the new LangGraph workflow.

4. **Observability by default.**  The ``execution_log`` and ``status``
   fields ensure that every graph execution is fully traceable without
   requiring external monitoring infrastructure.

Relationship to Existing Code
-----------------------------
The existing ``AgentState`` (``ml.schemas.agent_state``) is a Pydantic
``BaseModel`` used by ``BaseAgent`` subclasses and ``SupervisorAgent``.
``InvestigationState`` is a parallel construct designed specifically for
LangGraph.  During integration, a bridge function will convert between
the two representations.  For now, they coexist independently.

Field Conventions
-----------------
- Fields suffixed with ``_id`` are unique string identifiers.
- ``execution_log`` entries are plain dicts with keys:
  ``agent_name``, ``status``, ``message``, ``timestamp``, ``duration_seconds``.
- ``metadata`` is an open-ended dict for extensibility.
- ``status`` uses a fixed vocabulary: ``"initialized"``,
  ``"pipeline_complete"``, ``"investigating"``, ``"knowledge_retrieved"``,
  ``"intelligence_complete"``, ``"reporting"``, ``"completed"``, ``"failed"``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, TypedDict


class InvestigationState(TypedDict, total=False):
    """LangGraph-compatible state object for the fraud investigation workflow.

    This ``TypedDict`` is the contract between all nodes in the LangGraph
    ``StateGraph``.  Every node function accepts an ``InvestigationState``
    dict and returns a (possibly partial) dict of updates.

    The ``total=False`` modifier makes every field optional, which is
    essential because the state is populated *progressively* — fields
    are absent until the responsible agent populates them.

    Attributes
    ----------
    investigation_id : str
        Globally unique identifier for this investigation run.
        Generated once at workflow start and propagated through every
        downstream system (database, report, PDF).

    provider_id : str
        Identifier of the healthcare provider under investigation.
        Set during initialisation and used as the primary key for
        per-provider analysis.

    csv_data : Any
        Raw claims data, typically a ``pandas.DataFrame`` or its
        serialised representation.  This is the original input from
        the user upload and is never modified by downstream agents.

    features : Any
        Engineered feature matrix produced by ``FeatureBuilder``.
        Typically a ``pandas.DataFrame`` with exactly 12 aggregate
        features per provider (see ``feature_columns.json``).

    prediction : dict[str, Any]
        Single-provider prediction dict from ``Predictor``.  Keys
        include ``provider_id``, ``prediction``, ``fraud_probability``,
        and ``confidence``.

    fraud_score : float
        Normalised fraud probability score (0.0 – 1.0) extracted from
        the prediction.  Used as the primary numerical signal by
        downstream agents.

    risk_level : str
        Discrete risk classification string (``"Critical"``, ``"High"``,
        ``"Medium"``, ``"Low"``).  Derived from ``RiskScorer`` output.

    indicators : list[dict[str, Any]]
        Fraud indicators produced by ``ExplainabilityEngine``.  Each
        entry is a dict with keys: ``title``, ``status``, ``severity``,
        ``description``.  These provide human-readable signals that
        agents consume for investigation narrative generation.

    provider_statistics : dict[str, Any]
        Aggregate provider-level statistics from the pipeline.  Includes
        fields like ``total_claims``, ``total_reimbursement``,
        ``average_claim_amount``, ``unique_beneficiaries``, etc.

    retrieved_documents : list[dict[str, Any]]
        Knowledge base documents retrieved by the Knowledge Agent.
        Each entry is a dict with ``source``, ``content``, and
        ``relevance_score``.  Populated during the knowledge retrieval
        phase and consumed by downstream agents.

    ai_findings : list[dict[str, Any]]
        AI-generated findings from the Fraud Intelligence Agent.
        Each entry represents an identified fraud pattern or anomaly
        with supporting evidence.

    recommendations : list[dict[str, Any]]
        Actionable recommendations produced by investigation and
        intelligence agents.  Each entry is a dict with ``category``,
        ``priority``, ``description``, and ``rationale``.

    report : dict[str, Any]
        Fully assembled report content ready for PDF generation.
        Contains structured sections, executive summary, provider
        tables, and recommendation summaries.

    metadata : dict[str, Any]
        Arbitrary key-value store for extensibility.  Agents may store
        intermediate results, timing information, or any other data
        that does not fit neatly into a dedicated field.

    status : str
        Current workflow status.  Must be one of the predefined status
        vocabulary values (see module docstring).  Updated by every
        node as it begins and completes execution.

    execution_log : list[dict[str, Any]]
        Ordered, append-only log of every event during workflow
        execution.  Each entry is a dict with keys:
        ``agent_name`` (str), ``status`` (str), ``message`` (str),
        ``timestamp`` (str, ISO-8601), ``duration_seconds`` (float | None),
        ``error`` (str | None).  This log provides a complete audit
        trail for debugging and compliance.
    """

    # ------------------------------------------------------------------
    # Identifiers
    # ------------------------------------------------------------------

    investigation_id: str
    """Globally unique identifier for this investigation run.

    Format: ``INV-XXXXXXXX`` where ``XXXXXXXX`` is a random hex string.
    Generated once at workflow initialisation and never modified.
    """

    provider_id: str
    """Identifier of the healthcare provider under investigation.

    Extracted from the uploaded CSV data and used as the grouping key
    for feature engineering, prediction, and all downstream analysis.
    """

    # ------------------------------------------------------------------
    # Input data (immutable after initialisation)
    # ------------------------------------------------------------------

    csv_data: Any
    """Raw claims data (typically ``pandas.DataFrame``).

    This is the original user-uploaded data.  It is passed through the
    workflow unchanged so that agents can reference raw claim records
    when constructing investigation narratives or evidence lists.

    .. note::

       In LangGraph, state must be JSON-serialisable for checkpointing.
       If checkpointing is enabled, this field should contain a
       serialised representation (e.g. CSV string or dict of records).
    """

    # ------------------------------------------------------------------
    # Pipeline outputs (populated by FeatureBuilder → Predictor)
    # ------------------------------------------------------------------

    features: Any
    """Engineered feature matrix from ``FeatureBuilder``.

    A ``pandas.DataFrame`` with exactly 12 columns matching the
    model's expected feature schema.  One row per provider.
    """

    prediction: dict[str, Any]
    """Single-provider prediction result from ``Predictor``.

    Expected keys: ``provider_id``, ``prediction``, ``fraud_probability``,
    ``confidence``.  This is the raw model output before risk scoring.
    """

    fraud_score: float
    """Normalised fraud probability (0.0 – 1.0).

    Extracted from ``prediction["fraud_probability"]`` for convenient
    access by downstream agents without dict traversal.
    """

    risk_level: str
    """Discrete risk classification.

    One of: ``"Critical"``, ``"High"``, ``"Medium"``, ``"Low"``.
    Produced by ``RiskScorer`` based on configurable thresholds.
    """

    indicators: list[dict[str, Any]]
    """Fraud indicators from ``ExplainabilityEngine``.

    Each indicator dict contains:
      - ``title`` (str): Human-readable indicator name.
      - ``status`` (str): ``"normal"``, ``"warning"``, or ``"flagged"``.
      - ``severity`` (str): ``"low"``, ``"medium"``, ``"high"``, ``"critical"``.
      - ``description`` (str): Explanation of the indicator reading.
    """

    provider_statistics: dict[str, Any]
    """Aggregate provider-level statistics.

    Includes raw feature values and any supplementary statistics
    computed by the pipeline (e.g. claim volume, reimbursement totals,
    beneficiary counts, physician concentration).
    """

    # ------------------------------------------------------------------
    # Agent outputs (populated sequentially by LangGraph nodes)
    # ------------------------------------------------------------------

    retrieved_documents: list[dict[str, Any]]
    """Knowledge base documents retrieved by the Knowledge Agent.

    Each document dict contains:
      - ``source`` (str): Document origin identifier.
      - ``content`` (str): Document text content.
      - ``relevance_score`` (float): Semantic similarity score (0–1).
      - ``metadata`` (dict): Additional document metadata.

    This field is empty until the Knowledge Agent populates it.
    """

    ai_findings: list[dict[str, Any]]
    """AI-generated investigation findings from the Fraud Intelligence Agent.

    Each finding dict contains:
      - ``finding_id`` (str): Unique identifier.
      - ``category`` (str): Fraud pattern category.
      - ``severity`` (str): ``"Critical"`` / ``"High"`` / ``"Medium"`` / ``"Low"``.
      - ``description`` (str): Narrative description of the finding.
      - ``evidence`` (list[str]): Supporting evidence snippets.
      - ``confidence`` (float): Agent confidence (0–1).
      - ``estimated_impact`` (float | None): Dollar estimate.

    This field is empty until the Fraud Intelligence Agent populates it.
    """

    recommendations: list[dict[str, Any]]
    """Actionable recommendations produced by investigation agents.

    Each recommendation dict contains:
      - ``recommendation_id`` (str): Unique identifier.
      - ``category`` (str): Action category (audit, referral, monitoring).
      - ``priority`` (str): ``"Immediate"`` / ``"High"`` / ``"Medium"`` / ``"Low"``.
      - ``description`` (str): Human-readable action description.
      - ``rationale`` (str): Justification for the recommendation.
      - ``deadline_days`` (int | None): Suggested deadline in business days.

    Accumulated across multiple agents; the Report Agent consolidates
    these into the final report.
    """

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------

    report: dict[str, Any]
    """Fully assembled report content for PDF generation.

    Contains structured sections, executive summary, provider summary
    tables, and consolidated recommendations.  Produced by the Report
    Agent and consumed by the PDF generation service.
    """

    # ------------------------------------------------------------------
    # Metadata and observability
    # ------------------------------------------------------------------

    metadata: dict[str, Any]
    """Open-ended metadata store for extensibility.

    Agents may store:
      - ``"pipeline_duration_seconds"``: Time taken by the ML pipeline.
      - ``"model_version"``: Version of the XGBoost model used.
      - ``"config_snapshot"``: Frozen copy of workflow configuration.
      - Any other data that does not fit a dedicated field.

    This field is initialised as an empty dict and grows as agents
    add entries.
    """

    status: str
    """Current workflow execution status.

    Valid values (in execution order):
      1. ``"initialized"`` — State created, workflow not yet started.
      2. ``"pipeline_complete"`` — Feature engineering and prediction done.
      3. ``"investigating"`` — Investigation Agent is processing.
      4. ``"knowledge_retrieved"`` — Knowledge Agent has retrieved documents.
      5. ``"intelligence_complete"`` — Fraud Intelligence Agent is done.
      6. ``"reporting"`` — Report Agent is assembling the report.
      7. ``"completed"`` — Workflow finished successfully.
      8. ``"failed"`` — Workflow terminated due to an error.

    Every node updates this field as it begins and completes execution.
    """

    execution_log: list[dict[str, Any]]
    """Append-only execution audit log.

    Each entry is a dict with the following keys:

    - ``agent_name`` (str): Name of the node/agent that produced this entry.
    - ``status`` (str): Event type — ``"started"``, ``"completed"``, ``"failed"``.
    - ``message`` (str): Human-readable detail about the event.
    - ``timestamp`` (str): ISO-8601 timestamp of when the event occurred.
    - ``duration_seconds`` (float | None): Wall-clock time for the operation.
    - ``error`` (str | None): Error message if the event represents a failure.

    This log is consumed by:
      - The ``/investigate`` API endpoint for real-time progress tracking.
      - The Report Agent for the "Processing Notes" section.
      - Debugging tools for post-mortem analysis.
    """
