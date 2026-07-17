"""
Structured data schemas for LLM configuration and responses.

Defines Pydantic models that:

1. **Validate provider configuration** — ``LLMConfig`` ensures that
   all required settings are present and within supported ranges
   before any API call is made.

2. **Validate LLM outputs** — ``InvestigationLLMResponse`` and its
   nested models define the exact JSON schema that the Investigation
   Agent expects from the LLM.  Every response is validated against
   these models before being consumed by downstream agents.

Design Principles
-----------------
- All models use ``pydantic.BaseModel`` for validation and
  serialisation.
- Field constraints (``ge``, ``le``, ``min_length``) enforce
  business invariants at the schema level.
- Default values are chosen to be safe in production — no implicit
  ``None`` where a concrete value is required.
- Models are deliberately independent of any LLM SDK; they define
  the *data contract*, not the transport.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# =====================================================================
# Provider configuration
# =====================================================================


class LLMConfig(BaseModel):
    """Configuration for an LLM provider instance.

    This model is the single source of truth for all provider settings.
    It is typically populated from environment variables via the factory
    and validated once at application startup.

    Attributes:
        provider: Backend identifier (e.g. ``"gemini"``, ``"openai"``).
        model: Model identifier (e.g. ``"gemini-1.5-flash"``).
        api_key: API authentication key.  Loaded from environment
            variables by the factory; never hardcoded.
        temperature: Sampling temperature (0.0 = deterministic,
            1.0 = maximum creativity).  Lower values are preferred
            for fraud investigation tasks.
        max_tokens: Maximum number of tokens in a single completion.
        timeout: Per-request timeout in seconds.
        max_retries: Number of automatic retry attempts on transient
            failures (rate limits, connection errors).
        retry_base_delay: Base delay in seconds for exponential
            backoff between retries.
    """

    provider: str = Field(
        default="gemini",
        min_length=1,
        description="Backend identifier.",
    )
    model: str = Field(
        default="gemini-1.5-flash",
        min_length=1,
        description="Model identifier used for completions.",
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key.  Loaded from environment by the factory.",
    )
    temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="Sampling temperature.",
    )
    max_tokens: int = Field(
        default=4096,
        ge=1,
        le=1_048_576,
        description="Maximum tokens per completion.",
    )
    timeout: int = Field(
        default=60,
        ge=1,
        le=600,
        description="Per-request timeout in seconds.",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Number of automatic retry attempts.",
    )
    retry_base_delay: float = Field(
        default=1.0,
        ge=0.0,
        le=30.0,
        description="Base delay in seconds for exponential backoff.",
    )


# =====================================================================
# Investigation Agent structured output schemas
# =====================================================================


class InvestigationFindingCategory(str, Enum):
    """Recognised fraud pattern categories for investigation findings."""

    UPCODING = "upcoding"
    UNBUNDLING = "unbundling"
    PHANTOM_BILLING = "phantom_billing"
    DOUBLE_BILLING = "double_billing"
    KICKBACK = "kickback"
    UNNECESSARY_SERVICES = "unnecessary_services"
    IDENTITY_MISUSE = "identity_misuse"
    EXCESSIVE_SERVICES = "excessive_services"
    OTHER = "other"


class FindingSeverity(str, Enum):
    """Severity classification for an individual finding."""

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class RecommendationPriority(str, Enum):
    """Priority classification for investigation recommendations."""

    IMMEDIATE = "Immediate"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class RecommendationCategory(str, Enum):
    """Category classification for investigation recommendations."""

    AUDIT = "audit"
    REFERRAL = "referral"
    MONITORING = "monitoring"
    EDUCATION = "education"
    COMPLIANCE = "compliance"


class InvestigationFinding(BaseModel):
    """A single structured finding produced by the LLM.

    Each finding represents a suspected fraud pattern or anomaly
    identified during the investigation of a healthcare provider.
    """

    category: str = Field(
        ...,
        min_length=1,
        description=(
            "Fraud pattern category "
            "(e.g. upcoding, unbundling, phantom_billing)."
        ),
    )
    severity: str = Field(
        ...,
        description="Severity classification: Critical, High, Medium, or Low.",
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Detailed narrative description of the finding.",
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="List of supporting evidence items (claim IDs, amounts, dates).",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence level in this finding (0.0–1.0).",
    )
    estimated_impact: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Estimated financial impact in USD, if determinable.",
    )


class InvestigationRecommendation(BaseModel):
    """A single actionable recommendation produced by the LLM."""

    category: str = Field(
        ...,
        min_length=1,
        description=(
            "Action category "
            "(e.g. audit, referral, monitoring, education)."
        ),
    )
    priority: str = Field(
        ...,
        description="Priority level: Immediate, High, Medium, or Low.",
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Human-readable description of the recommended action.",
    )
    rationale: str = Field(
        default="",
        description="Justification for why this recommendation is made.",
    )


class InvestigationLLMResponse(BaseModel):
    """Top-level validated response from the Investigation Agent LLM.

    This model defines the exact JSON contract that the LLM must
    produce.  Every field is validated before the response is
    consumed by downstream agents.

    Attributes:
        executive_summary: High-level overview of all findings.
        findings: List of structured investigation findings.
        recommendations: List of actionable recommendations.
    """

    executive_summary: str = Field(
        ...,
        min_length=1,
        description="Brief overview of the investigation findings.",
    )
    findings: list[InvestigationFinding] = Field(
        default_factory=list,
        description="Structured findings from the investigation.",
    )
    recommendations: list[InvestigationRecommendation] = Field(
        default_factory=list,
        description="Actionable recommendations.",
    )


# =====================================================================
# Fraud Intelligence Agent structured output schemas
# =====================================================================


class FraudIntelligenceCriticalFinding(BaseModel):
    """A critical finding identified by the Fraud Intelligence Agent."""

    finding_type: str = Field(
        ...,
        min_length=1,
        description="Classification of the fraud pattern (e.g. upcoding, kickback).",
    )
    severity: str = Field(
        ...,
        description="Severity level: Critical, High, Medium, or Low.",
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Detailed description of the critical finding.",
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="Supporting evidence items (claim IDs, amounts, dates).",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence level in this finding (0.0–1.0).",
    )
    estimated_impact: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Estimated financial impact in USD, if determinable.",
    )
    regulatory_reference: Optional[str] = Field(
        default=None,
        description="Relevant CMS, OIG, or statute reference, if applicable.",
    )


class FraudIntelligenceRecommendation(BaseModel):
    """An actionable recommendation from the Fraud Intelligence Agent."""

    category: str = Field(
        ...,
        min_length=1,
        description="Action category (e.g. audit, referral, monitoring, education).",
    )
    priority: str = Field(
        ...,
        description="Priority level: Immediate, High, Medium, or Low.",
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Human-readable description of the recommended action.",
    )
    rationale: str = Field(
        default="",
        description="Justification for why this recommendation is made.",
    )
    deadline_days: Optional[int] = Field(
        default=None,
        ge=0,
        description="Suggested deadline in business days.",
    )


class FraudIntelligenceLLMResponse(BaseModel):
    """Top-level validated response from the Fraud Intelligence Agent LLM.

    This model defines the exact JSON contract that the LLM must
    produce.  Every field is validated before the response is
    consumed by the Report Agent.

    Attributes:
        overall_assessment: Comprehensive summary of the intelligence
            analysis including fraud likelihood and key findings.
        confidence: Agent confidence in the overall assessment (0.0–1.0).
        investigation_priority: Recommended investigation priority tier.
        critical_findings: List of critical fraud patterns identified.
        supporting_evidence: Consolidated evidence supporting the assessment.
        recommended_actions: Prioritised list of recommended next steps.
        risk_factors: Factors that increase fraud risk for this provider.
        mitigating_factors: Factors that decrease fraud risk or provide
            context (e.g. high-volume specialty, seasonal patterns).
    """

    overall_assessment: str = Field(
        ...,
        min_length=1,
        description=(
            "Comprehensive summary of the fraud intelligence analysis."
        ),
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Agent confidence in the overall assessment (0.0–1.0).",
    )
    investigation_priority: str = Field(
        default="Medium",
        description=(
            "Recommended investigation priority: "
            "Immediate, High, Medium, or Low."
        ),
    )
    critical_findings: list[FraudIntelligenceCriticalFinding] = Field(
        default_factory=list,
        description="Critical fraud patterns identified.",
    )
    supporting_evidence: list[str] = Field(
        default_factory=list,
        description="Consolidated evidence supporting the assessment.",
    )
    recommended_actions: list[FraudIntelligenceRecommendation] = Field(
        default_factory=list,
        description="Prioritised list of recommended next steps.",
    )
    risk_factors: list[str] = Field(
        default_factory=list,
        description="Factors that increase fraud risk for this provider.",
    )
    mitigating_factors: list[str] = Field(
        default_factory=list,
        description=(
            "Factors that decrease fraud risk or provide context."
        ),
    )
