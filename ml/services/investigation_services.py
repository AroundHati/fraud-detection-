"""
Investigation Agent — answers investigator questions about a provider using
ONLY the structured investigation data produced by the pipeline.

This service consumes:

- Provider prediction (risk score, fraud probability, prediction label)
- Investigation summary (claim counts, reimbursement, averages)
- Fraud indicators (severity, status, description)
- Recommendation (level, description)

and produces evidence-based answers without modifying or re-running the ML model.

The agent is initially implemented as deterministic (template-based).  The
architecture separates the ``ResponseGenerator`` protocol from the agent
itself so that a future LLM-based generator can be swapped in without
changing the API surface.
"""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Sequence

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Request / Response shapes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class InvestigateRequest:
    """Incoming request to the investigation agent."""

    provider: Dict[str, Any]
    question: str


@dataclass
class InvestigateResponse:
    """Outgoing response from the investigation agent."""

    answer: str
    sources: List[str]


# ---------------------------------------------------------------------------
# Response Generator (pluggable)
# ---------------------------------------------------------------------------

class ResponseGenerator(ABC):
    """Protocol for generating answers from investigation context.

    Implementations must never invent data — they should only reference
    values present in the provider context dict.
    """

    @abstractmethod
    def generate(
        self,
        provider: Dict[str, Any],
        question: str,
    ) -> InvestigateResponse:
        ...


# ---------------------------------------------------------------------------
# Template Response Generator (deterministic)
# ---------------------------------------------------------------------------

class TemplateResponseGenerator(ResponseGenerator):
    """Deterministic, template-based response generator.

    Matches the investigator's question against a set of known patterns
    and returns a structured answer built entirely from the provider data.
    """

    def generate(
        self,
        provider: Dict[str, Any],
        question: str,
    ) -> InvestigateResponse:
        q = question.lower().strip()

        # Try each handler in priority order
        for handler in [
            self._handle_flagged,
            self._handle_indicators,
            self._handle_review,
            self._handle_abuse_type,
            self._handle_summary,
            self._handle_prediction,
            self._handle_risk_score,
            self._handle_recommendation,
            self._handle_claims,
            self._handle_reimbursement,
            self._handle_indicators_detail,
            self._handle_fallback,
        ]:
            result = handler(provider, q)
            if result is not None:
                return result

        # Should never reach here, but safety net
        return InvestigateResponse(
            answer=(
                "I can answer questions about this provider's investigation results. "
                "Try asking about fraud indicators, risk level, recommendations, "
                "or claim statistics."
            ),
            sources=[],
        )

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _handle_flagged(
        self, provider: Dict[str, Any], q: str
    ) -> Optional[InvestigateResponse]:
        patterns = [
            r"why.*flagged",
            r"why.*(?:classified|rated|scored)",
            r"what.*risk",
            r"explain.*risk",
            r"reason.*(?:flag|risk|high)",
        ]
        if not any(re.search(p, q) for p in patterns):
            return None

        sources: List[str] = ["RiskScore", "FraudIndicators"]

        provider_name = provider.get("provider_name", "this provider")
        risk_score = provider.get("risk_score", provider.get("risk_level", "N/A"))
        prediction = provider.get("prediction", "N/A")
        confidence = provider.get("confidence", 0)
        confidence_pct = f"{confidence * 100:.0f}%" if isinstance(confidence, (int, float)) and confidence <= 1 else str(confidence)

        lines = [
            f"{provider_name} was classified as **{prediction}** with a risk score of **{risk_score}** "
            f"(confidence: {confidence_pct}).",
            "",
            "The classification was based on the following key factors:",
        ]

        indicators = provider.get("fraud_indicators", [])
        flagged = [i for i in indicators if i.get("status") == "flagged"]
        warnings = [i for i in indicators if i.get("status") == "warning"]

        if flagged:
            lines.append("")
            lines.append("**Flagged indicators:**")
            for ind in flagged:
                label = ind.get("label") or ind.get("title", "Unknown")
                severity = ind.get("severity", "")
                desc = ind.get("description", "")
                lines.append(f"- **{label}** ({severity}): {desc}")
                sources.append(label.replace(" ", ""))

        if warnings:
            lines.append("")
            lines.append("**Warning indicators:**")
            for ind in warnings:
                label = ind.get("label") or ind.get("title", "Unknown")
                severity = ind.get("severity", "")
                desc = ind.get("description", "")
                lines.append(f"- **{label}** ({severity}): {desc}")
                sources.append(label.replace(" ", ""))

        if not flagged and not warnings:
            lines.append("No flagged or warning indicators were found.")
            lines.append(
                "The risk classification may be based on the overall claim "
                "volume, reimbursement patterns, or other statistical signals."
            )

        return InvestigateResponse(answer="\n".join(lines), sources=sources)

    def _handle_indicators(
        self, provider: Dict[str, Any], q: str
    ) -> Optional[InvestigateResponse]:
        patterns = [
            r"which.*indicator",
            r"indicator.*contribut",
            r"fraud.*indicator",
            r"top.*indicator",
            r"most.*(?:important|significant|critical)",
            r"what.*indicator",
        ]
        if not any(re.search(p, q) for p in patterns):
            return None

        indicators = provider.get("fraud_indicators", [])
        if not indicators:
            return InvestigateResponse(
                answer="No fraud indicators were identified for this provider.",
                sources=[],
            )

        # Sort by severity priority: critical > high > medium > low
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_indicators = sorted(
            indicators,
            key=lambda x: severity_order.get(x.get("severity", "low"), 4),
        )

        sources = ["FraudIndicators"]
        lines = [
            f"There are **{len(indicators)} fraud indicators** for this provider, "
            "ranked by severity:",
            "",
        ]

        for i, ind in enumerate(sorted_indicators, 1):
            label = ind.get("label") or ind.get("title", "Unknown")
            severity = ind.get("severity", "unknown")
            status = ind.get("status", "unknown")
            desc = ind.get("description", "")
            lines.append(f"{i}. **{label}** — {severity} severity ({status})")
            if desc:
                lines.append(f"   {desc}")
            lines.append("")
            sources.append(label.replace(" ", ""))

        # Highlight the most critical
        critical = [i for i in sorted_indicators if i.get("severity") == "critical"]
        if critical:
            top = critical[0]
            top_label = top.get("label") or top.get("title", "Unknown")
            lines.append(
                f"The most critical indicator is **{top_label}**. "
                "This should be the primary focus of any investigation."
            )

        return InvestigateResponse(answer="\n".join(lines), sources=sources)

    def _handle_review(
        self, provider: Dict[str, Any], q: str
    ) -> Optional[InvestigateResponse]:
        patterns = [
            r"what.*(?:should|to).*review",
            r"where.*start",
            r"first.*step",
            r"investigator.*(?:do|check|look)",
            r"what.*(?:examine|check|audit)",
            r"priority.*action",
        ]
        if not any(re.search(p, q) for p in patterns):
            return None

        sources: List[str] = ["FraudIndicators", "Recommendation"]
        provider_name = provider.get("provider_name", "this provider")
        recommendation = provider.get("recommendation", {})
        rec_level = recommendation.get("level", "N/A")
        rec_desc = recommendation.get("description", "")

        lines = [
            f"For {provider_name}, recommended investigation priorities:",
            "",
        ]

        indicators = provider.get("fraud_indicators", [])
        flagged = [i for i in indicators if i.get("status") == "flagged"]
        warnings = [i for i in indicators if i.get("status") == "warning"]

        if flagged:
            lines.append("**Step 1 — Review flagged indicators:**")
            for ind in flagged:
                label = ind.get("label") or ind.get("title", "Unknown")
                desc = ind.get("description", "")
                lines.append(f"- {label}: {desc}")
                sources.append(label.replace(" ", ""))
            lines.append("")

        if warnings:
            lines.append("**Step 2 — Investigate warning indicators:**")
            for ind in warnings:
                label = ind.get("label") or ind.get("title", "Unknown")
                desc = ind.get("description", "")
                lines.append(f"- {label}: {desc}")
                sources.append(label.replace(" ", ""))
            lines.append("")

        if rec_desc:
            lines.append(f"**Overall recommendation ({rec_level}):**")
            lines.append(rec_desc)

        return InvestigateResponse(answer="\n".join(lines), sources=sources)

    def _handle_abuse_type(
        self, provider: Dict[str, Any], q: str
    ) -> Optional[InvestigateResponse]:
        patterns = [
            r"(?:billing|provider).*abuse",
            r"abuse.*type",
            r"upcod",
            r"unbundl",
            r"overbilling",
            r"what.*type.*fraud",
        ]
        if not any(re.search(p, q) for p in patterns):
            return None

        sources: List[str] = ["FraudIndicators", "InvestigationSummary"]
        indicators = provider.get("fraud_indicators", [])
        provider_name = provider.get("provider_name", "This provider")
        avg_claim = provider.get("average_claim_amount", 0)
        inpatient = provider.get("inpatient_claims", 0)
        outpatient = provider.get("outpatient_claims", 0)
        total_claims = provider.get("total_claims", 0)

        lines = [
            f"Based on the investigation data for **{provider_name}**:",
            "",
        ]

        # Check for billing abuse signals
        billing_signals = []
        provider_signals = []

        for ind in indicators:
            label = (ind.get("label") or ind.get("title", "")).lower()
            desc = ind.get("description", "").lower()
            combined = f"{label} {desc}"

            if any(kw in combined for kw in [
                "upcod", "unbundl", "overbiling", "claim amount",
                "billing", "reimbursement", "diagnosis diversity",
            ]):
                billing_signals.append(ind)
            if any(kw in combined for kw in [
                "inpatient ratio", "physician concentration",
                "beneficiary concentration", "chronic condition",
                "claim volume", "concentrated billing",
            ]):
                provider_signals.append(ind)

        if billing_signals:
            lines.append("**Potential billing abuse signals:**")
            for ind in billing_signals:
                label = ind.get("label") or ind.get("title", "Unknown")
                desc = ind.get("description", "")
                lines.append(f"- {label}: {desc}")
                sources.append(label.replace(" ", ""))
            lines.append("")

        if provider_signals:
            lines.append("**Potential provider abuse signals:**")
            for ind in provider_signals:
                label = ind.get("label") or ind.get("title", "Unknown")
                desc = ind.get("description", "")
                lines.append(f"- {label}: {desc}")
                sources.append(label.replace(" ", ""))
            lines.append("")

        if not billing_signals and not provider_signals:
            lines.append(
                "The current indicators do not strongly suggest a specific "
                "abuse type. A more detailed review of billing records and "
                "claim documentation would be needed to classify the abuse type."
            )

        if avg_claim > 0:
            lines.append(
                f"The average claim amount of ${avg_claim:,.2f} across "
                f"{total_claims:,} claims ({inpatient} inpatient, "
                f"{outpatient} outpatient) provides additional context "
                "for the abuse assessment."
            )
            sources.append("AverageClaimAmount")

        return InvestigateResponse(answer="\n".join(lines), sources=sources)

    def _handle_summary(
        self, provider: Dict[str, Any], q: str
    ) -> Optional[InvestigateResponse]:
        patterns = [
            r"summariz",
            r"summary",
            r"overview",
            r"tell.*about",
            r"what.*know",
            r"give.*overview",
        ]
        if not any(re.search(p, q) for p in patterns):
            return None

        provider_name = provider.get("provider_name", "Unknown Provider")
        provider_id = provider.get("provider_id", "N/A")
        risk_score = provider.get("risk_score", 0)
        prediction = provider.get("prediction", "N/A")
        confidence = provider.get("confidence", 0)
        total_claims = provider.get("total_claims", 0)
        total_reimb = provider.get("total_reimbursement", 0)
        avg_claim = provider.get("average_claim_amount", 0)
        inpatient = provider.get("inpatient_claims", 0)
        outpatient = provider.get("outpatient_claims", 0)
        beneficiaries = provider.get("unique_beneficiaries", 0)
        physicians = provider.get("unique_physicians", 0)

        indicators = provider.get("fraud_indicators", [])
        flagged_count = len([i for i in indicators if i.get("status") == "flagged"])
        warning_count = len([i for i in indicators if i.get("status") == "warning"])
        recommendation = provider.get("recommendation", {})
        rec_level = recommendation.get("level", "N/A")

        confidence_pct = f"{confidence * 100:.0f}%" if isinstance(confidence, (int, float)) and confidence <= 1 else str(confidence)

        lines = [
            f"**{provider_name}** ({provider_id})",
            "",
            f"- **Risk Score:** {risk_score}",
            f"- **Prediction:** {prediction}",
            f"- **Confidence:** {confidence_pct}",
            f"- **Total Claims:** {total_claims:,}",
            f"- **Total Reimbursement:** ${total_reimb:,.2f}",
            f"- **Average Claim:** ${avg_claim:,.2f}",
            f"- **Inpatient / Outpatient:** {inpatient:,} / {outpatient:,}",
            f"- **Unique Beneficiaries:** {beneficiaries:,}",
            f"- **Unique Physicians:** {physicians:,}",
            "",
            f"**Fraud Indicators:** {flagged_count} flagged, {warning_count} warnings "
            f"(out of {len(indicators)} total)",
            "",
            f"**Recommendation:** {rec_level}",
        ]

        if recommendation.get("description"):
            lines.append(recommendation["description"])

        sources = [
            "ProviderSummary", "RiskScore", "FraudIndicators", "Recommendation",
        ]

        return InvestigateResponse(answer="\n".join(lines), sources=sources)

    def _handle_prediction(
        self, provider: Dict[str, Any], q: str
    ) -> Optional[InvestigateResponse]:
        patterns = [
            r"what.*prediction",
            r"what.*classified",
            r"prediction.*result",
            r"model.*predict",
        ]
        if not any(re.search(p, q) for p in patterns):
            return None

        prediction = provider.get("prediction", "N/A")
        confidence = provider.get("confidence", 0)
        confidence_pct = f"{confidence * 100:.0f}%" if isinstance(confidence, (int, float)) and confidence <= 1 else str(confidence)

        lines = [
            f"The ML model classified this provider as **{prediction}** "
            f"with **{confidence_pct}** confidence.",
            "",
            "This prediction is based on the engineered features derived "
            "from the provider's claim history, including claim volume, "
            "reimbursement patterns, beneficiary distribution, and diagnosis "
            "diversity.",
        ]

        return InvestigateResponse(
            answer="\n".join(lines),
            sources=["RiskScore", "Prediction"],
        )

    def _handle_risk_score(
        self, provider: Dict[str, Any], q: str
    ) -> Optional[InvestigateResponse]:
        patterns = [
            r"risk\s*score",
            r"what.*score",
            r"how.*high.*risk",
            r"score.*breakdown",
        ]
        if not any(re.search(p, q) for p in patterns):
            return None

        risk_score = provider.get("risk_score", 0)
        prediction = provider.get("prediction", "N/A")

        if isinstance(risk_score, (int, float)):
            if risk_score >= 70:
                risk_label = "High Risk"
            elif risk_score >= 30:
                risk_label = "Medium Risk"
            else:
                risk_label = "Low Risk"
        else:
            risk_label = "Unknown"

        lines = [
            f"The risk score for this provider is **{risk_score}** ({risk_label}).",
            "",
            "The score reflects the aggregate assessment of:",
            "- Claim volume and frequency",
            "- Reimbursement magnitude",
            "- Inpatient-to-outpatient ratio",
            "- Beneficiary and physician concentration",
            "- Diagnosis code diversity",
            "- Chronic condition distribution",
        ]

        return InvestigateResponse(
            answer="\n".join(lines),
            sources=["RiskScore", "InvestigationSummary"],
        )

    def _handle_recommendation(
        self, provider: Dict[str, Any], q: str
    ) -> Optional[InvestigateResponse]:
        patterns = [
            r"recommend",
            r"next\s*step",
            r"action.*(?:item|plan)",
            r"what.*(?:do|should).*next",
        ]
        if not any(re.search(p, q) for p in patterns):
            return None

        recommendation = provider.get("recommendation", {})
        rec_level = recommendation.get("level", "N/A")
        rec_desc = recommendation.get("description", "")

        lines = [f"**Recommendation:** {rec_level}"]
        if rec_desc:
            lines.append("")
            lines.append(rec_desc)

        return InvestigateResponse(
            answer="\n".join(lines),
            sources=["Recommendation"],
        )

    def _handle_claims(
        self, provider: Dict[str, Any], q: str
    ) -> Optional[InvestigateResponse]:
        patterns = [
            r"claim.*volume",
            r"how.*many.*claim",
            r"total.*claim",
            r"number.*claim",
            r"claim.*count",
        ]
        if not any(re.search(p, q) for p in patterns):
            return None

        total = provider.get("total_claims", 0)
        inpatient = provider.get("inpatient_claims", 0)
        outpatient = provider.get("outpatient_claims", 0)
        beneficiaries = provider.get("unique_beneficiaries", 0)
        physicians = provider.get("unique_physicians", 0)

        lines = [
            f"**Claim Volume Summary:**",
            "",
            f"- Total Claims: {total:,}",
            f"- Inpatient Claims: {inpatient:,}",
            f"- Outpatient Claims: {outpatient:,}",
            f"- Unique Beneficiaries: {beneficiaries:,}",
            f"- Unique Attending Physicians: {physicians:,}",
        ]

        if inpatient > 0 and outpatient > 0:
            ratio = inpatient / outpatient
            lines.append("")
            lines.append(f"- Inpatient/Outpatient Ratio: {ratio:.1f}")

        return InvestigateResponse(
            answer="\n".join(lines),
            sources=["TotalClaims", "InpatientClaims", "UniqueBeneficiaries"],
        )

    def _handle_reimbursement(
        self, provider: Dict[str, Any], q: str
    ) -> Optional[InvestigateResponse]:
        patterns = [
            r"reimbursement",
            r"total.*paid",
            r"amount.*paid",
            r"billing.*amount",
            r"how.*much",
        ]
        if not any(re.search(p, q) for p in patterns):
            return None

        total_reimb = provider.get("total_reimbursement", 0)
        avg_claim = provider.get("average_claim_amount", 0)
        total_claims = provider.get("total_claims", 0)

        lines = [
            f"**Reimbursement Summary:**",
            "",
            f"- Total Reimbursement: ${total_reimb:,.2f}",
            f"- Average Claim Amount: ${avg_claim:,.2f}",
            f"- Total Claims: {total_claims:,}",
        ]

        return InvestigateResponse(
            answer="\n".join(lines),
            sources=["TotalReimbursement", "AverageClaimAmount"],
        )

    def _handle_indicators_detail(
        self, provider: Dict[str, Any], q: str
    ) -> Optional[InvestigateResponse]:
        patterns = [
            r"tell.*indicator",
            r"explain.*indicator",
            r"detail.*indicator",
            r"what.*each.*indicator",
            r"list.*indicator",
        ]
        if not any(re.search(p, q) for p in patterns):
            return None

        indicators = provider.get("fraud_indicators", [])
        if not indicators:
            return InvestigateResponse(
                answer="No fraud indicators were identified for this provider.",
                sources=[],
            )

        lines = [f"**Detailed Fraud Indicators ({len(indicators)} total):**", ""]
        sources = ["FraudIndicators"]

        for i, ind in enumerate(indicators, 1):
            label = ind.get("label") or ind.get("title", "Unknown")
            severity = ind.get("severity", "unknown")
            status = ind.get("status", "unknown")
            desc = ind.get("description", "No description available.")
            lines.append(f"{i}. **{label}**")
            lines.append(f"   Severity: {severity} | Status: {status}")
            lines.append(f"   {desc}")
            lines.append("")
            sources.append(label.replace(" ", ""))

        return InvestigateResponse(answer="\n".join(lines), sources=sources)

    def _handle_fallback(
        self, provider: Dict[str, Any], q: str
    ) -> Optional[InvestigateResponse]:
        return InvestigateResponse(
            answer=(
                "I can answer questions about this provider's investigation results. "
                "Here are some things I can help with:\n\n"
                "- Why was this provider flagged?\n"
                "- Which fraud indicators contributed most?\n"
                "- What should an investigator review first?\n"
                "- Is this likely billing abuse or provider abuse?\n"
                "- Summarize this investigation.\n"
                "- What is the risk score and prediction?\n"
                "- What are the recommended next steps?"
            ),
            sources=[],
        )


# ---------------------------------------------------------------------------
# Investigation Agent
# ---------------------------------------------------------------------------

class InvestigationAgent:
    """Answers investigator questions about a provider.

    The agent is a thin orchestrator that:

    1. Validates the request.
    2. Builds a structured context from the provider data.
    3. Delegates to a ``ResponseGenerator`` to produce the answer.

    Parameters
    ----------
    generator : ResponseGenerator | None
        The response generation strategy.  Defaults to
        ``TemplateResponseGenerator`` when ``None``.
    """

    def __init__(
        self,
        generator: Optional[ResponseGenerator] = None,
    ) -> None:
        self._generator = generator or TemplateResponseGenerator()

    @property
    def generator(self) -> ResponseGenerator:
        return self._generator

    def investigate(
        self,
        provider: Dict[str, Any],
        question: str,
    ) -> InvestigateResponse:
        """Answer a question about a provider using investigation data.

        Parameters
        ----------
        provider : dict
            The structured investigation result for a provider.  Must contain
            at minimum ``provider_id`` and ``risk_score``.
        question : str
            The investigator's question.

        Returns
        -------
        InvestigateResponse
            An answer built from the provider data and a list of data
            source keys referenced in the response.

        Raises
        ------
        InvestigationAgentError
            If the provider data is invalid or the question is empty.
        """
        self._validate_request(provider, question)

        logger.info(
            "[investigation_agent] Question about %s: %s",
            provider.get("provider_id", "unknown"),
            question[:80],
        )

        response = self._generator.generate(provider, question)

        logger.info(
            "[investigation_agent] Answer generated (%d sources)",
            len(response.sources),
        )

        return response

    @staticmethod
    def _validate_request(
        provider: Dict[str, Any], question: str
    ) -> None:
        if not isinstance(provider, dict):
            raise InvestigationAgentError(
                f"Provider must be a dict, got {type(provider).__name__}"
            )
        if not question or not question.strip():
            raise InvestigationAgentError("Question cannot be empty")
        if "provider_id" not in provider:
            raise InvestigationAgentError(
                "Provider data must contain 'provider_id'"
            )


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class InvestigationAgentError(Exception):
    """Raised when the investigation agent encounters invalid input."""
