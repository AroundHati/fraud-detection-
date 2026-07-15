"""
Investigation schemas for the FraudShield agent framework.

Defines the data structures produced by the Investigation Agent and
consumed by the Report Agent.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class FindingSeverity(str, Enum):
    """Severity classification for an individual provider finding."""

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class FraudPattern(str, Enum):
    """Known fraud pattern categories."""

    UPCODING = "upcoding"
    UNBUNDLING = "unbundling"
    PHANTOM_BILLING = "phantom_billing"
    DOUBLE_BILLING = "double_billing"
    KICKBACK = "kickback"
    UNNECESSARY_SERVICES = "unnecessary_services"
    IDENTITY_MISUSE = "identity_misuse"
    OTHER = "other"


class ProviderFinding(BaseModel):
    """A single finding for one provider within an investigation."""

    provider_id: str = Field(
        ...,
        description="Unique identifier of the provider.",
    )
    severity: FindingSeverity = Field(
        ...,
        description="Severity of the finding.",
    )
    fraud_patterns: list[FraudPattern] = Field(
        default_factory=list,
        description="Detected fraud pattern categories.",
    )
    narrative: str = Field(
        default="",
        description="LLM-generated narrative describing the finding.",
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="List of evidence snippets (claim IDs, amounts, dates).",
    )
    estimated_financial_impact: Optional[float] = Field(
        default=None,
        description="Estimated dollar amount of potential fraud.",
    )
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Agent confidence in this finding (0–1).",
    )
    recommended_action: str = Field(
        default="",
        description="Suggested next step for this provider.",
    )


class Recommendation(BaseModel):
    """An actionable recommendation derived from the investigation."""

    recommendation_id: str = Field(
        ...,
        description="Unique identifier for this recommendation.",
    )
    provider_id: str = Field(
        ...,
        description="Provider this recommendation pertains to.",
    )
    priority: str = Field(
        ...,
        description="Priority label (Immediate / High / Medium / Low).",
    )
    category: str = Field(
        ...,
        description="Category of action (audit, referral, monitoring, etc.).",
    )
    description: str = Field(
        ...,
        description="Human-readable description of the recommended action.",
    )
    rationale: str = Field(
        default="",
        description="Explanation of why this recommendation is made.",
    )
    deadline_days: Optional[int] = Field(
        default=None,
        description="Suggested deadline in business days.",
    )


class InvestigationSummary(BaseModel):
    """Top-level summary produced by the Investigation Agent.

    Stored in ``AgentState.investigation_summary`` and consumed by
    the Report Agent.
    """

    investigation_id: str = Field(
        ...,
        description="Unique identifier for this investigation.",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the investigation was created.",
    )
    executive_summary: str = Field(
        default="",
        description="High-level summary of the entire investigation.",
    )
    provider_findings: list[ProviderFinding] = Field(
        default_factory=list,
        description="Per-provider findings.",
    )
    recommendations: list[Recommendation] = Field(
        default_factory=list,
        description="Actionable recommendations.",
    )
    total_providers_investigated: int = Field(
        default=0,
        description="Number of providers included in this investigation.",
    )
    total_providers_flagged: int = Field(
        default=0,
        description="Number of providers with at least one finding.",
    )
    total_estimated_impact: Optional[float] = Field(
        default=None,
        description="Aggregate estimated financial impact across all findings.",
    )
    investigation_status: str = Field(
        default="draft",
        description="Lifecycle status (draft / in_progress / completed).",
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Arbitrary metadata for extensibility.",
    )
