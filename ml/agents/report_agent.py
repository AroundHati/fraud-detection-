"""
Report agent for the FraudShield multi-agent system.

The Report Agent assembles all validated outputs from the ML pipeline,
Investigation Agent, and Fraud Intelligence Agent into a structured
report, then generates a professional PDF using the existing
``report_generator`` service.

This module provides two interfaces:

1. ``ReportAgent`` (``BaseAgent`` subclass) — used by the legacy
   ``SupervisorAgent`` orchestration pipeline.

2. ``run_report_node`` (standalone function) — the LangGraph
   node function consumed by ``StateGraph``.  This is the primary
   interface for the new workflow.

Design
------
- The agent does **not** generate new investigative conclusions.
- It consolidates existing validated outputs into report sections.
- PDF generation is attempted but failures are non-fatal — the
  structured report dict is always populated.
- The legacy ``ReportAgent`` interface preserves backward
  compatibility with ``AgentState``-based orchestration.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from ml.agents.base_agent import BaseAgent
from ml.agents.state import InvestigationState
from ml.agents.utils import (
    STATUS_COMPLETED,
    STATUS_REPORTING,
    append_log,
    begin_node,
    complete_node,
    fail_node,
)
from ml.schemas.agent_state import AgentState

logger = logging.getLogger(__name__)


# =====================================================================
# Exception
# =====================================================================


class ReportAgentError(Exception):
    """Raised when the Report Agent encounters a processing failure."""


# =====================================================================
# State → report dict mapping
# =====================================================================


def _build_report_metadata(state: InvestigationState) -> dict[str, Any]:
    """Build report metadata from the workflow state.

    Parameters
    ----------
    state : InvestigationState
        The current workflow state.

    Returns
    -------
    dict[str, Any]
        Report metadata dict matching the ``ReportMetadata`` schema.
    """
    investigation_id = state.get("investigation_id", "unknown")
    report_id = f"RPT-{uuid4().hex[:8].upper()}"

    return {
        "report_id": report_id,
        "investigation_id": investigation_id,
        "title": "FraudShield Investigation Report",
        "author": "FraudShield AI",
        "classification": "Confidential",
        "version": "2.0",
        "status": "final",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def _build_executive_summary(state: InvestigationState) -> str:
    """Build the executive summary paragraph from the workflow state.

    Parameters
    ----------
    state : InvestigationState
        The current workflow state with pipeline outputs and agent
        findings.

    Returns
    -------
    str
        A multi-paragraph executive summary string.
    """
    provider_id = state.get("provider_id", "this provider")
    risk_level = state.get("risk_level", "N/A")
    fraud_score = state.get("fraud_score", 0.0)
    prediction = state.get("prediction", {})
    indicators = state.get("indicators", [])
    ai_findings = state.get("ai_findings", [])
    recommendations = state.get("recommendations", [])

    model_prediction = prediction.get("prediction", "N/A")
    confidence = prediction.get("confidence", 0.0)
    fraud_probability = prediction.get("fraud_probability", 0.0)

    flagged_count = sum(
        1 for i in indicators
        if isinstance(i, dict) and i.get("status") == "flagged"
    )
    warning_count = sum(
        1 for i in indicators
        if isinstance(i, dict) and i.get("status") == "warning"
    )

    paragraphs: list[str] = []

    paragraphs.append(
        f"This report presents the findings of the healthcare fraud "
        f"investigation for Provider <b>{provider_id}</b>. "
        f"The analysis reviewed claims submitted by this provider and "
        f"assessed fraud risk using the FraudShield machine learning "
        f"pipeline and multi-agent analysis system."
    )

    paragraphs.append(
        f"Provider {provider_id} has been classified as "
        f"<b>{risk_level} risk</b> with a fraud probability of "
        f"<b>{fraud_probability * 100:.1f}%</b> "
        f"(model confidence: {confidence:.1f}%). "
        f"The overall prediction is <b>{model_prediction}</b>."
    )

    if flagged_count > 0 or warning_count > 0:
        flag_parts: list[str] = []
        if flagged_count > 0:
            flag_parts.append(f"{flagged_count} indicator(s) flagged")
        if warning_count > 0:
            flag_parts.append(f"{warning_count} indicator(s) in warning status")
        paragraphs.append(
            f"Of the {len(indicators)} fraud indicators evaluated, "
            f"{', '.join(flag_parts)}."
        )

    if ai_findings:
        paragraphs.append(
            f"The investigation identified <b>{len(ai_findings)} "
            f"finding(s)</b> across multiple analysis dimensions. "
            f"The Fraud Intelligence Agent cross-referenced findings "
            f"with regulatory knowledge base documents and prior case "
            f"patterns to produce an actionable intelligence assessment."
        )

    if recommendations:
        paragraphs.append(
            f"The analysis produced <b>{len(recommendations)} "
            f"recommendation(s)</b> for follow-up action, prioritised "
            f"by investigation urgency."
        )

    return " ".join(paragraphs)


def _build_provider_tables(state: InvestigationState) -> list[dict[str, Any]]:
    """Build provider summary tables from the workflow state.

    Parameters
    ----------
    state : InvestigationState
        The current workflow state.

    Returns
    -------
    list[dict[str, Any]]
        A list of provider table dicts for the report.
    """
    provider_id = state.get("provider_id", "N/A")
    statistics = state.get("provider_statistics", {})

    if not statistics:
        return []

    return [
        {
            "provider_id": provider_id,
            "total_claims": statistics.get("total_claims", 0),
            "total_reimbursement": statistics.get(
                "total_reimbursement",
                statistics.get("total_payments", 0),
            ),
            "average_claim_amount": statistics.get(
                "average_claim_amount",
                statistics.get("avg_claim_amount", 0),
            ),
            "unique_beneficiaries": statistics.get("unique_beneficiaries", 0),
            "unique_physicians": statistics.get("unique_physicians", 0),
        }
    ]


def _build_recommendation_summary(
    recommendations: list[dict[str, Any]],
) -> str:
    """Build a consolidated recommendation summary string.

    Parameters
    ----------
    recommendations : list[dict[str, Any]]
        All accumulated recommendations from the workflow.

    Returns
    -------
    str
        A human-readable summary of the recommendations.
    """
    if not recommendations:
        return "No recommendations generated."

    by_priority: dict[str, int] = {}
    for rec in recommendations:
        priority = rec.get("priority", "Unknown")
        by_priority[priority] = by_priority.get(priority, 0) + 1

    parts: list[str] = []
    for priority in ["Immediate", "High", "Medium", "Low"]:
        count = by_priority.get(priority, 0)
        if count > 0:
            parts.append(f"{count} {priority}-priority")

    return f"{len(recommendations)} recommendation(s): {', '.join(parts)}."


def _build_report_sections(state: InvestigationState) -> list[dict[str, Any]]:
    """Build the ordered report sections from the workflow state.

    Parameters
    ----------
    state : InvestigationState
        The current workflow state.

    Returns
    -------
    list[dict[str, Any]]
        A list of section dicts matching the ``ReportSection`` schema.
    """
    report_id = state.get("investigation_id", "RPT")
    sections: list[dict[str, Any]] = []

    # --- Section 1: Executive Summary ---
    sections.append({
        "section_id": f"{report_id}-SEC-001",
        "title": "Executive Summary",
        "content": _build_executive_summary(state),
        "order": 1,
        "section_type": "summary",
        "subsections": [],
    })

    # --- Section 2: Provider Information ---
    provider_id = state.get("provider_id", "N/A")
    statistics = state.get("provider_statistics", {})
    stats_text = (
        f"Provider {provider_id} statistics: "
        + ", ".join(f"{k}={v}" for k, v in statistics.items())
        if statistics
        else "No provider statistics available."
    )
    sections.append({
        "section_id": f"{report_id}-SEC-002",
        "title": "Provider Information",
        "content": stats_text,
        "order": 2,
        "section_type": "text",
        "subsections": [],
    })

    # --- Section 3: Risk Assessment ---
    risk_level = state.get("risk_level", "N/A")
    fraud_score = state.get("fraud_score", 0.0)
    prediction = state.get("prediction", {})
    risk_text = (
        f"Risk Level: {risk_level}. "
        f"Fraud Score: {fraud_score}. "
        f"Model Prediction: {prediction.get('prediction', 'N/A')}. "
        f"Fraud Probability: {prediction.get('fraud_probability', 0) * 100:.1f}%. "
        f"Confidence: {prediction.get('confidence', 0):.1f}%."
    )
    sections.append({
        "section_id": f"{report_id}-SEC-003",
        "title": "Risk Assessment",
        "content": risk_text,
        "order": 3,
        "section_type": "summary",
        "subsections": [],
    })

    # --- Section 4: Investigation Findings ---
    ai_findings = state.get("ai_findings", [])
    if ai_findings:
        finding_lines: list[str] = []
        for i, f in enumerate(ai_findings, 1):
            cat = f.get("category", "unknown")
            sev = f.get("severity", "unknown")
            desc = f.get("description", "")
            conf = f.get("confidence", 0.0)
            impact = f.get("estimated_impact")
            finding_lines.append(
                f"{i}. [{sev}] {cat} (confidence: {conf:.2f}): {desc}"
                + (f" — Estimated impact: ${impact:,.2f}" if impact else "")
            )
        findings_text = "\n".join(finding_lines)
    else:
        findings_text = "No investigation findings available."

    sections.append({
        "section_id": f"{report_id}-SEC-004",
        "title": "Investigation Findings",
        "content": findings_text,
        "order": 4,
        "section_type": "text",
        "subsections": [],
    })

    # --- Section 5: Fraud Intelligence Assessment ---
    intelligence = state.get("metadata", {}).get(
        "fraud_intelligence_assessment", {}
    )
    if intelligence:
        intel_parts: list[str] = []
        overall = intelligence.get("overall_assessment", "")
        if overall:
            intel_parts.append(overall)
        priority = intelligence.get("investigation_priority", "")
        if priority:
            intel_parts.append(f"Investigation Priority: {priority}.")
        risk_factors = intelligence.get("risk_factors", [])
        if risk_factors:
            intel_parts.append("Risk Factors: " + "; ".join(risk_factors) + ".")
        mitigating = intelligence.get("mitigating_factors", [])
        if mitigating:
            intel_parts.append(
                "Mitigating Factors: " + "; ".join(mitigating) + "."
            )
        intel_text = " ".join(intel_parts)
    else:
        intel_text = "No fraud intelligence assessment available."

    sections.append({
        "section_id": f"{report_id}-SEC-005",
        "title": "Fraud Intelligence Assessment",
        "content": intel_text,
        "order": 5,
        "section_type": "summary",
        "subsections": [],
    })

    # --- Section 6: Fraud Indicators ---
    indicators = state.get("indicators", [])
    if indicators:
        ind_lines: list[str] = []
        for i, ind in enumerate(indicators, 1):
            title = ind.get("title", "Unknown")
            status = ind.get("status", "unknown")
            sev = ind.get("severity", "unknown")
            desc = ind.get("description", "")
            ind_lines.append(
                f"{i}. {title} — status: {status}, severity: {sev}. {desc}"
            )
        ind_text = "\n".join(ind_lines)
    else:
        ind_text = "No fraud indicators available."

    sections.append({
        "section_id": f"{report_id}-SEC-006",
        "title": "Fraud Indicators",
        "content": ind_text,
        "order": 6,
        "section_type": "text",
        "subsections": [],
    })

    # --- Section 7: Provider Statistics ---
    if statistics:
        stat_lines: list[str] = []
        for k, v in statistics.items():
            stat_lines.append(f"- {k}: {v}")
        stat_text = "\n".join(stat_lines)
    else:
        stat_text = "No provider statistics available."

    sections.append({
        "section_id": f"{report_id}-SEC-007",
        "title": "Provider Statistics",
        "content": stat_text,
        "order": 7,
        "section_type": "text",
        "subsections": [],
    })

    # --- Section 8: Recommendations ---
    recommendations = state.get("recommendations", [])
    if recommendations:
        rec_lines: list[str] = []
        for i, rec in enumerate(recommendations, 1):
            cat = rec.get("category", "unknown")
            priority = rec.get("priority", "unknown")
            desc = rec.get("description", "")
            rec_lines.append(f"{i}. [{priority}] {cat}: {desc}")
        rec_text = "\n".join(rec_lines)
    else:
        rec_text = "No recommendations generated."

    sections.append({
        "section_id": f"{report_id}-SEC-008",
        "title": "Recommendations",
        "content": rec_text,
        "order": 8,
        "section_type": "text",
        "subsections": [],
    })

    return sections


# =====================================================================
# State → PDF input mapping (for report_generator.generate_report)
# =====================================================================


def _map_state_to_investigation_dict(
    state: InvestigationState,
) -> dict[str, Any]:
    """Map the workflow state to the ``investigation`` dict expected by
    ``report_generator.generate_report()``.

    Parameters
    ----------
    state : InvestigationState
        The current workflow state.

    Returns
    -------
    dict[str, Any]
        A dict matching the InvestigationRepository structure.
    """
    return {
        "investigation_id": state.get("investigation_id", "unknown"),
        "created_at": state.get("metadata", {}).get(
            "created_at", datetime.now(timezone.utc).isoformat()
        ),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "uploaded_filename": state.get("metadata", {}).get(
            "uploaded_filename", "N/A"
        ),
        "status": state.get("status", "completed"),
        "provider_count": 1,
        "high_risk": 1 if state.get("risk_level") in ("Critical", "High") else 0,
        "medium_risk": 1 if state.get("risk_level") == "Medium" else 0,
        "low_risk": 1 if state.get("risk_level") == "Low" else 0,
        "summary": {},
        "results": [],
    }


def _map_state_to_provider_dict(
    state: InvestigationState,
) -> dict[str, Any]:
    """Map the workflow state to the ``provider`` dict expected by
    ``report_generator.generate_report()``.

    Parameters
    ----------
    state : InvestigationState
        The current workflow state.

    Returns
    -------
    dict[str, Any]
        A dict matching the provider result structure used by the
        existing PDF generator.
    """
    prediction = state.get("prediction", {})
    statistics = state.get("provider_statistics", {})
    indicators = state.get("indicators", [])

    investigation_summary: dict[str, Any] = {}
    if statistics:
        investigation_summary = {
            "totalClaims": statistics.get("total_claims", 0),
            "totalReimbursement": statistics.get(
                "total_reimbursement",
                statistics.get("total_payments", 0),
            ),
            "averageClaimAmount": statistics.get(
                "average_claim_amount",
                statistics.get("avg_claim_amount", 0),
            ),
            "uniqueBeneficiaries": statistics.get("unique_beneficiaries", 0),
            "uniquePhysicians": statistics.get("unique_physicians", 0),
        }

    flagged_count = sum(
        1 for i in indicators
        if isinstance(i, dict) and i.get("status") == "flagged"
    )

    risk_level = state.get("risk_level", "N/A")
    if risk_level in ("Critical", "High"):
        recommendation = {
            "level": "Immediate — Full Investigation Required",
            "description": (
                f"Provider {state.get('provider_id', 'N/A')} has been "
                f"classified as {risk_level} risk. Immediate investigation "
                f"of billing practices is recommended."
            ),
        }
    elif risk_level == "Medium":
        recommendation = {
            "level": "Manual Review Recommended",
            "description": (
                f"Provider {state.get('provider_id', 'N/A')} shows "
                f"moderate risk indicators. A focused review of recent "
                f"claims history is recommended."
            ),
        }
    else:
        recommendation = {
            "level": "Routine Monitoring",
            "description": (
                f"Provider {state.get('provider_id', 'N/A')} is within "
                f"normal parameters. Continue standard monitoring."
            ),
        }

    return {
        "provider_id": state.get("provider_id", "N/A"),
        "risk_level": risk_level,
        "fraud_probability": prediction.get("fraud_probability", 0.0),
        "confidence": prediction.get("confidence", 0.0),
        "prediction": prediction.get("prediction", "N/A"),
        "investigation_summary": investigation_summary,
        "fraud_indicators": indicators,
        "recommendation": recommendation,
        "requires_manual_review": risk_level in ("Critical", "High"),
        "review_reason": (
            f"Classified as {risk_level} risk"
            if risk_level in ("Critical", "High")
            else ""
        ),
        "investigation_priority": _derive_investigation_priority(risk_level),
        "investigation_score": state.get("fraud_score", 0.0) * 100,
    }


def _derive_investigation_priority(risk_level: str) -> str:
    """Derive an investigation priority label from the risk level.

    Parameters
    ----------
    risk_level : str
        The risk level classification.

    Returns
    -------
    str
        A human-readable priority label.
    """
    priority_map = {
        "Critical": "Immediate",
        "High": "High",
        "Medium": "Medium",
        "Low": "Low",
    }
    return priority_map.get(risk_level, "N/A")


# =====================================================================
# PDF generation
# =====================================================================


def _generate_pdf(
    state: InvestigationState,
) -> Optional[bytes]:
    """Generate the PDF report using the existing report_generator service.

    Parameters
    ----------
    state : InvestigationState
        The current workflow state.

    Returns
    -------
    bytes or None
        The PDF bytes if generation succeeded, ``None`` otherwise.
    """
    try:
        from ml.services.report_generator import generate_report

        investigation_dict = _map_state_to_investigation_dict(state)
        provider_dict = _map_state_to_provider_dict(state)

        pdf_bytes = generate_report(investigation_dict, provider_dict)

        logger.info(
            "[report_agent] PDF generated — %d bytes", len(pdf_bytes)
        )
        return pdf_bytes

    except Exception as exc:
        logger.warning(
            "[report_agent] PDF generation failed (non-fatal): %s", exc
        )
        return None


# =====================================================================
# LangGraph node function
# =====================================================================


def run_report_node(state: InvestigationState) -> InvestigationState:
    """LangGraph node: assemble the investigation report and generate PDF.

    This function is registered as a node in the LangGraph ``StateGraph``.
    It reads all accumulated investigation data from prior agents and
    assembles it into a structured report with PDF output.

    Steps:
        1. Build report metadata and sections from state data.
        2. Generate the executive summary from findings and indicators.
        3. Attempt PDF generation via the existing report_generator.
        4. Populate ``state["report"]`` with the structured report dict.
        5. Store PDF bytes in ``state["report"]["output_bytes"]``.
        6. Update status to ``"completed"``.
        7. Record structured log entries.

    Parameters
    ----------
    state : InvestigationState
        The current workflow state.  Should contain outputs from all
        prior agents (Investigation, Knowledge, Fraud Intelligence).

    Returns
    -------
    InvestigationState
        The updated state with ``report`` populated, ``status`` set to
        ``"completed"``, and execution log entries appended.

    Raises
    ------
    No exceptions are raised — errors are captured in the execution log.
    """
    start_time = begin_node(state, "report_agent", STATUS_REPORTING)

    try:
        investigation_id = state.get("investigation_id", "unknown")
        provider_id = state.get("provider_id", "unknown")
        ai_findings = state.get("ai_findings", [])
        retrieved_documents = state.get("retrieved_documents", [])
        recommendations = state.get("recommendations", [])

        logger.info(
            "[report_agent] Assembling report — investigation=%s provider=%s "
            "findings=%d documents=%d recommendations=%d",
            investigation_id,
            provider_id,
            len(ai_findings),
            len(retrieved_documents),
            len(recommendations),
        )

        # ------------------------------------------------------------------
        # Build report data from state
        # ------------------------------------------------------------------
        report_metadata = _build_report_metadata(state)
        report_id = report_metadata["report_id"]

        executive_summary = _build_executive_summary(state)
        sections = _build_report_sections(state)
        provider_tables = _build_provider_tables(state)
        recommendation_summary = _build_recommendation_summary(recommendations)

        report_content: dict[str, Any] = {
            "metadata": report_metadata,
            "executive_summary": executive_summary,
            "sections": sections,
            "provider_tables": provider_tables,
            "recommendation_summary": recommendation_summary,
            "disclaimer": (
                "This report is generated by AI and should be reviewed "
                "by a qualified investigator. The findings and "
                "recommendations are based on automated analysis and "
                "do not constitute legal or medical advice."
            ),
        }

        # ------------------------------------------------------------------
        # Attempt PDF generation (non-fatal)
        # ------------------------------------------------------------------
        pdf_bytes = _generate_pdf(state)
        if pdf_bytes is not None:
            report_content["output_bytes"] = pdf_bytes
            logger.info(
                "[report_agent] PDF attached — report_id=%s size=%d bytes",
                report_id,
                len(pdf_bytes),
            )

        # ------------------------------------------------------------------
        # Populate state
        # ------------------------------------------------------------------
        state["report"] = report_content

        # ------------------------------------------------------------------
        # Log report assembly completion
        # ------------------------------------------------------------------
        append_log(
            state,
            agent_name="report_agent",
            status="completed",
            message=(
                f"Report assembled — id={report_id} sections={len(sections)} "
                f"pdf={'yes' if pdf_bytes is not None else 'no'}"
            ),
        )

        # ------------------------------------------------------------------
        # Mark workflow as completed
        # ------------------------------------------------------------------
        state["status"] = STATUS_COMPLETED
        append_log(
            state,
            agent_name="workflow",
            status="completed",
            message=(
                f"Workflow finished — investigation={investigation_id} "
                f"provider={provider_id} "
                f"log_entries={len(state.get('execution_log', []))}"
            ),
        )

        return complete_node(
            state,
            "report_agent",
            start_time,
            extra_message=f"report_id={report_id}",
        )

    except Exception as exc:
        logger.exception(
            "[report_agent] Report assembly failed — %s", exc
        )
        return fail_node(state, "report_agent", start_time, str(exc))


# =====================================================================
# Legacy BaseAgent subclass
# =====================================================================


class ReportAgent(BaseAgent):
    """Agent that assembles investigation results into a structured report.

    Uses the existing ``report_generator`` service for PDF generation
    and the ``ReportTool`` wrapper for data preparation.

    Attributes:
        name: ``"report"``
        description: Brief description of the agent's responsibility.
    """

    name: str = "report"
    description: str = (
        "Assembles investigation results into a structured report "
        "and generates a professional PDF."
    )

    async def execute(self, state: AgentState) -> AgentState:
        """Execute the report preparation workflow.

        Steps:
            1. Validate that ``state.investigation_summary`` is present.
            2. Prepare report metadata (ID, timestamps, author).
            3. Assemble report sections from available data.
            4. Populate ``state.report_metadata`` and ``state.report``.
            5. Return the updated state.

        Note:
            This agent does NOT generate PDFs directly.  PDF generation
            is handled by the downstream ``report_generator`` service
            or the LangGraph ``run_report_node`` function.

        Args:
            state: The shared agent state with investigation data.

        Returns:
            The updated agent state with report content populated.

        Raises:
            ReportAgentError: If the report cannot be assembled.
        """
        logger.info(
            "[%s] execute() called — investigation_summary present=%s",
            self.name,
            state.investigation_summary is not None,
        )

        if state.investigation_summary is None:
            raise ReportAgentError(
                "Cannot prepare report — state.investigation_summary is None."
            )

        return state
