"""
Shared agent state for the FraudShield multi-agent system.

``AgentState`` is the single mutable object passed between agents
during an orchestration run.  Every agent reads from and writes to
this state instead of passing ad-hoc dictionaries.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from ml.schemas.investigation import InvestigationSummary, ProviderFinding, Recommendation
from ml.schemas.report import ReportContent, ReportMetadata
from ml.schemas.risk import RiskAssessment

logger = logging.getLogger(__name__)


class ExecutionLogEntry(BaseModel):
    """A single entry in the agent execution log."""

    agent_name: str = Field(
        ...,
        description="Name of the agent that produced this entry.",
    )
    status: str = Field(
        ...,
        description="Execution status (started / completed / failed / retried).",
    )
    message: str = Field(
        default="",
        description="Human-readable status message.",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the entry was recorded.",
    )
    duration_seconds: Optional[float] = Field(
        default=None,
        description="Wall-clock time the agent spent executing.",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if the agent failed.",
    )


class AgentState(BaseModel):
    """Shared mutable state object for the multi-agent orchestration.

    Every agent receives, mutates, and returns an ``AgentState`` instance.
    The supervisor is responsible for initialising the state and passing
    it through the agent pipeline.

    Attributes:
        investigation_id: Unique identifier for the current investigation run.
        source_file: Path or name of the uploaded source data file.
        pipeline_result: Raw output from the ML pipeline (``PipelineResult`` dict).
        risk_assessment: Structured risk assessment produced by the Risk Agent.
        investigation_summary: Narrative produced by the Investigation Agent.
        provider_findings: Individual provider findings (denormalised for convenience).
        recommendations: Actionable recommendations derived from findings.
        report_metadata: Metadata for the final report.
        report: Fully assembled report content ready for PDF generation.
        execution_log: Ordered list of agent execution log entries.
        errors: Accumulated error messages from any agent.
        timestamps: Key timestamps (started, each agent start/end, finished).
        metadata: Arbitrary key-value metadata for extensibility.
    """

    # ------------------------------------------------------------------
    # Identifiers
    # ------------------------------------------------------------------

    investigation_id: str = Field(
        default="",
        description="Unique identifier for the current investigation run.",
    )
    source_file: str = Field(
        default="",
        description="Path or filename of the uploaded source data.",
    )

    # ------------------------------------------------------------------
    # Pipeline output
    # ------------------------------------------------------------------

    pipeline_result: Optional[dict[str, Any]] = Field(
        default=None,
        description="Serialised PipelineResult from the ML pipeline.",
    )

    # ------------------------------------------------------------------
    # Agent-produced data
    # ------------------------------------------------------------------

    risk_assessment: Optional[RiskAssessment] = Field(
        default=None,
        description="Structured risk assessment produced by the Risk Agent.",
    )
    investigation_summary: Optional[InvestigationSummary] = Field(
        default=None,
        description="Investigation narrative produced by the Investigation Agent.",
    )
    provider_findings: list[ProviderFinding] = Field(
        default_factory=list,
        description="Denormalised list of per-provider findings.",
    )
    recommendations: list[Recommendation] = Field(
        default_factory=list,
        description="Actionable recommendations from the Investigation Agent.",
    )

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------

    report_metadata: Optional[ReportMetadata] = Field(
        default=None,
        description="Metadata for the final report.",
    )
    report: Optional[ReportContent] = Field(
        default=None,
        description="Fully assembled report content.",
    )

    # ------------------------------------------------------------------
    # Observability
    # ------------------------------------------------------------------

    execution_log: list[ExecutionLogEntry] = Field(
        default_factory=list,
        description="Ordered log of agent execution events.",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Accumulated error messages from any agent.",
    )
    timestamps: dict[str, datetime] = Field(
        default_factory=dict,
        description="Key timestamps (e.g. 'started', 'risk_agent_completed').",
    )

    # ------------------------------------------------------------------
    # Extensibility
    # ------------------------------------------------------------------

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary key-value store for future extensions.",
    )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def log_entry(
        self,
        agent_name: str,
        status: str,
        message: str = "",
        duration_seconds: Optional[float] = None,
        error: Optional[str] = None,
    ) -> None:
        """Append an entry to the execution log.

        Args:
            agent_name: Name of the agent logging the entry.
            status: Execution status (started / completed / failed).
            message: Human-readable detail.
            duration_seconds: Optional wall-clock duration.
            error: Optional error message.
        """
        entry = ExecutionLogEntry(
            agent_name=agent_name,
            status=status,
            message=message,
            duration_seconds=duration_seconds,
            error=error,
        )
        self.execution_log.append(entry)
        logger.info("[%s] %s — %s", agent_name, status, message)

    def record_error(self, agent_name: str, error: str) -> None:
        """Append an error message and log it.

        Args:
            agent_name: Name of the agent that encountered the error.
            error: Description of the error.
        """
        self.errors.append(f"[{agent_name}] {error}")
        logger.error("[%s] ERROR — %s", agent_name, error)

    def set_timestamp(self, key: str) -> None:
        """Record a timestamp under the given key.

        Args:
            key: Descriptive key (e.g. ``"risk_agent_started"``).
        """
        self.timestamps[key] = datetime.utcnow()

    @property
    def has_errors(self) -> bool:
        """Return ``True`` if any errors have been recorded."""
        return len(self.errors) > 0
