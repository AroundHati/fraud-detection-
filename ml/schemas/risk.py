"""
Risk assessment schemas for the FraudShield agent framework.

Defines the data structures produced by the Risk Agent and consumed
by downstream Investigation and Report agents.  All models are
pure data containers with no business logic.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Enumeration of possible risk classifications for a provider."""

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class InvestigationPriority(str, Enum):
    """Enumeration of investigation priority tiers."""

    CRITICAL = "Critical"
    URGENT = "Urgent"
    STANDARD = "Standard"
    ROUTINE = "Routine"


class FraudIndicator(BaseModel):
    """A single fraud indicator extracted from pipeline explainability output."""

    title: str = Field(
        ...,
        description="Human-readable name of the indicator.",
    )
    status: str = Field(
        ...,
        description="Indicator status (normal / warning / flagged).",
    )
    severity: str = Field(
        ...,
        description="Severity level (low / medium / high / critical).",
    )
    description: str = Field(
        default="",
        description="Explanation of the indicator reading.",
    )


class ProviderRisk(BaseModel):
    """Risk assessment for a single provider.

    Populated by the Risk Agent from per-provider pipeline output.
    """

    provider_id: str = Field(
        ...,
        description="Unique identifier of the healthcare provider.",
    )
    fraud_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model-predicted probability of fraud (0-1).",
    )
    predicted_label: str = Field(
        ...,
        description="Raw model prediction label (e.g. 'Yes' / 'No').",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Model confidence expressed as a percentage (0-100).",
    )
    risk_level: RiskLevel = Field(
        ...,
        description="Discrete risk classification.",
    )
    priority: InvestigationPriority = Field(
        ...,
        description="Investigation priority tier.",
    )
    requires_manual_review: bool = Field(
        default=False,
        description="Whether the provider must be reviewed by a human investigator.",
    )
    review_reason: Optional[str] = Field(
        default=None,
        description="Explanation for why manual review is required.",
    )
    fraud_indicators: list[FraudIndicator] = Field(
        default_factory=list,
        description="Fraud indicators from the explainability engine.",
    )
    investigation_score: float = Field(
        default=0.0,
        description="Investigation score (fraud_probability * 100).",
    )
    investigation_summary: Optional[dict] = Field(
        default=None,
        description="Aggregate claim statistics from explainability.",
    )
    recommendation: Optional[dict] = Field(
        default=None,
        description="Recommended action from explainability engine.",
    )


class RiskAssessment(BaseModel):
    """Top-level risk assessment produced by the Risk Agent.

    This model is stored in ``AgentState.risk_assessment`` and is
    consumed by the Investigation Agent and Report Agent.

    Contains both aggregate statistics across all providers and the
    per-provider risk breakdown in ``provider_risks``.
    """

    assessment_id: str = Field(
        ...,
        description="Unique identifier for this assessment run.",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the assessment was created.",
    )

    # --- Aggregate statistics ---

    total_providers: int = Field(
        default=0,
        description="Total number of providers assessed.",
    )
    overall_risk_level: RiskLevel = Field(
        default=RiskLevel.LOW,
        description="Overall risk level across the entire provider cohort.",
    )
    highest_risk_provider: Optional[str] = Field(
        default=None,
        description="Provider ID with the highest fraud probability.",
    )
    highest_probability: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Highest fraud probability observed across all providers.",
    )
    average_probability: float = (
        Field(
            default=0.0,
            ge=0.0,
            le=1.0,
            description="Mean fraud probability across all providers.",
        )
    )
    high_risk_count: int = (
        Field(
            default=0,
            description="Count of providers classified as High or Critical risk.",
        )
    )
    medium_risk_count: int = Field(
        default=0,
        description="Count of providers classified as Medium risk.",
    )
    low_risk_count: int = Field(
        default=0,
        description="Count of providers classified as Low risk.",
    )
    requires_manual_review_count: int = Field(
        default=0,
        description="Count of providers flagged for manual review.",
    )
    investigation_priority: InvestigationPriority = Field(
        default=InvestigationPriority.ROUTINE,
        description="Overall investigation priority for the cohort.",
    )
    requires_manual_review: bool = Field(
        default=False,
        description="Whether the cohort as a whole requires manual review.",
    )

    # --- Detailed data ---

    provider_risks: list[ProviderRisk] = Field(
        default_factory=list,
        description="Risk details for each provider analysed.",
    )
    summary: str = Field(
        default="",
        description="Deterministic executive summary of the risk landscape.",
    )
    processing_metadata: dict = Field(
        default_factory=dict,
        description="Arbitrary metadata (model version, timing, etc.).",
    )
