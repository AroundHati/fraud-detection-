"""
Report Generator — produces professional PDF investigation reports using
reportlab.

Design
~~~~~~
The PDF mirrors the FraudShield brand language: clean typography,
structured sections, color-coded risk indicators, and a formal
header/footer.  The report is suitable for investigators, supervisors,
auditors, and documentation.

Sections
~~~~~~~~
1. Header — branding, investigation ID, provider, status, date.
2. Executive Summary — auto-generated narrative paragraph.
3. Provider Information — aggregate claim statistics table.
4. AI Assessment — risk level, probability, confidence, manual review.
5. Fraud Indicators — full table of all 9 indicators.
6. AI Explanation — explainability narrative from the engine.
7. Recommendation — suggested next actions.
8. Footer — legal disclaimer.
"""

from __future__ import annotations

import io
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Brand colors (from ui-tokens.md)
# ---------------------------------------------------------------------------

_COLOR_PRIMARY = colors.HexColor("#2563EB")
_COLOR_PRIMARY_DARK = colors.HexColor("#1D4ED8")
_COLOR_PRIMARY_LIGHT = colors.HexColor("#DBEAFE")
_COLOR_SUCCESS = colors.HexColor("#10B981")
_COLOR_SUCCESS_LIGHT = colors.HexColor("#D1FAE5")
_COLOR_WARNING = colors.HexColor("#F59E0B")
_COLOR_WARNING_LIGHT = colors.HexColor("#FEF3C7")
_COLOR_ERROR = colors.HexColor("#EF4444")
_COLOR_ERROR_LIGHT = colors.HexColor("#FEE2E2")
_COLOR_TEXT_PRIMARY = colors.HexColor("#0F172A")
_COLOR_TEXT_SECONDARY = colors.HexColor("#475569")
_COLOR_TEXT_MUTED = colors.HexColor("#94A3B8")
_COLOR_BORDER = colors.HexColor("#E2E8F0")
_COLOR_SURFACE = colors.HexColor("#FFFFFF")
_COLOR_SURFACE_SECONDARY = colors.HexColor("#F1F5F9")

# Risk level color mapping
_RISK_COLORS: Dict[str, tuple[colors.HexColor, colors.HexColor]] = {
    "High": (_COLOR_ERROR, _COLOR_ERROR_LIGHT),
    "Medium": (_COLOR_WARNING, _COLOR_WARNING_LIGHT),
    "Low": (_COLOR_SUCCESS, _COLOR_SUCCESS_LIGHT),
}

# Indicator status color mapping
_STATUS_COLORS: Dict[str, tuple[colors.HexColor, colors.HexColor]] = {
    "flagged": (_COLOR_ERROR, _COLOR_ERROR_LIGHT),
    "warning": (_COLOR_WARNING, _COLOR_WARNING_LIGHT),
    "normal": (_COLOR_SUCCESS, _COLOR_SUCCESS_LIGHT),
}

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

_PAGE_WIDTH, _PAGE_HEIGHT = A4
_MARGIN_LEFT = 0.75 * inch
_MARGIN_RIGHT = 0.75 * inch
_MARGIN_TOP = 0.9 * inch
_MARGIN_BOTTOM = 0.9 * inch
_CONTENT_WIDTH = _PAGE_WIDTH - _MARGIN_LEFT - _MARGIN_RIGHT


def _build_styles() -> Dict[str, ParagraphStyle]:
    """Create all paragraph styles used in the report."""
    base = getSampleStyleSheet()

    styles: Dict[str, ParagraphStyle] = {}

    styles["brand_name"] = ParagraphStyle(
        "brand_name",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=_COLOR_PRIMARY,
        alignment=TA_LEFT,
        spaceAfter=2,
    )

    styles["report_subtitle"] = ParagraphStyle(
        "report_subtitle",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=15,
        textColor=_COLOR_TEXT_SECONDARY,
        alignment=TA_LEFT,
        spaceAfter=4,
    )

    styles["section_heading"] = ParagraphStyle(
        "section_heading",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=_COLOR_TEXT_PRIMARY,
        spaceBefore=16,
        spaceAfter=8,
    )

    styles["sub_heading"] = ParagraphStyle(
        "sub_heading",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=_COLOR_TEXT_PRIMARY,
        spaceBefore=10,
        spaceAfter=4,
    )

    styles["body"] = ParagraphStyle(
        "body",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=_COLOR_TEXT_SECONDARY,
        spaceAfter=6,
    )

    styles["body_bold"] = ParagraphStyle(
        "body_bold",
        parent=styles["body"],
        fontName="Helvetica-Bold",
        textColor=_COLOR_TEXT_PRIMARY,
    )

    styles["meta_label"] = ParagraphStyle(
        "meta_label",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=_COLOR_TEXT_MUTED,
    )

    styles["meta_value"] = ParagraphStyle(
        "meta_value",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=_COLOR_TEXT_PRIMARY,
    )

    styles["table_header"] = ParagraphStyle(
        "table_header",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.white,
    )

    styles["table_cell"] = ParagraphStyle(
        "table_cell",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=_COLOR_TEXT_SECONDARY,
    )

    styles["table_cell_bold"] = ParagraphStyle(
        "table_cell_bold",
        parent=styles["table_cell"],
        fontName="Helvetica-Bold",
        textColor=_COLOR_TEXT_PRIMARY,
    )

    styles["footer_brand"] = ParagraphStyle(
        "footer_brand",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=_COLOR_TEXT_MUTED,
        alignment=TA_CENTER,
    )

    styles["footer_disclaimer"] = ParagraphStyle(
        "footer_disclaimer",
        parent=base["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=_COLOR_TEXT_MUTED,
        alignment=TA_CENTER,
    )

    styles["meta_info"] = ParagraphStyle(
        "meta_info",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=_COLOR_TEXT_SECONDARY,
    )

    return styles


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------


def _build_header(
    investigation: Dict[str, Any],
    provider: Dict[str, Any],
    styles: Dict[str, ParagraphStyle],
) -> List[Any]:
    """Build the header section: branding, title, and metadata."""
    elements: List[Any] = []

    # Brand + title row
    elements.append(Paragraph("FraudShield", styles["brand_name"]))
    elements.append(
        Paragraph("Healthcare Fraud Investigation Report", styles["report_subtitle"])
    )
    elements.append(HRFlowable(width="100%", thickness=2, color=_COLOR_PRIMARY))
    elements.append(Spacer(1, 10))

    # Metadata grid
    inv_id = investigation.get("investigation_id", "N/A")
    provider_id = provider.get("provider_id", "N/A")
    status = investigation.get("status", "N/A")
    created = investigation.get("created_at", "")
    gen_date = datetime.now(timezone.utc).strftime("%B %d, %Y")

    if created:
        try:
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            created_formatted = dt.strftime("%B %d, %Y at %H:%M UTC")
        except (ValueError, TypeError):
            created_formatted = created
    else:
        created_formatted = "N/A"

    meta_data = [
        [
            Paragraph("Investigation ID", styles["meta_label"]),
            Paragraph("Provider ID", styles["meta_label"]),
            Paragraph("Investigation Status", styles["meta_label"]),
            Paragraph("Report Generated", styles["meta_label"]),
        ],
        [
            Paragraph(str(inv_id), styles["meta_value"]),
            Paragraph(str(provider_id), styles["meta_value"]),
            Paragraph(str(status), styles["meta_value"]),
            Paragraph(gen_date, styles["meta_value"]),
        ],
    ]

    meta_table = Table(
        meta_data,
        colWidths=[
            _CONTENT_WIDTH * 0.25,
            _CONTENT_WIDTH * 0.25,
            _CONTENT_WIDTH * 0.25,
            _CONTENT_WIDTH * 0.25,
        ],
    )
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _COLOR_SURFACE_SECONDARY),
                ("BACKGROUND", (0, 1), (-1, 1), _COLOR_SURFACE),
                ("BOX", (0, 0), (-1, -1), 0.5, _COLOR_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, _COLOR_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elements.append(meta_table)
    elements.append(Spacer(1, 6))

    # Additional context row
    filename = investigation.get("uploaded_filename", "N/A")
    provider_count = investigation.get("provider_count", 0)
    info_parts = [f"Source File: {filename}"]
    info_parts.append(f"Providers Analyzed: {provider_count}")
    created_label = f"Created: {created_formatted}"
    info_parts.append(created_label)
    elements.append(
        Paragraph("  |  ".join(info_parts), styles["meta_info"])
    )

    return elements


def _build_executive_summary(
    investigation: Dict[str, Any],
    provider: Dict[str, Any],
    styles: Dict[str, ParagraphStyle],
) -> List[Any]:
    """Build the Executive Summary section."""
    elements: List[Any] = []
    elements.append(Paragraph("Executive Summary", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=_COLOR_BORDER))
    elements.append(Spacer(1, 6))

    provider_id = provider.get("provider_id", "this provider")
    risk_level = provider.get("risk_level", "N/A")
    fraud_prob = provider.get("fraud_probability", 0)
    confidence = provider.get("confidence", 0)
    prediction = provider.get("prediction", "N/A")
    manual_review = provider.get("requires_manual_review", False)
    review_reason = provider.get("review_reason", "")

    summary = investigation.get("summary") or {}
    results = investigation.get("results") or []
    high_risk_count = investigation.get("high_risk", 0)
    medium_risk_count = investigation.get("medium_risk", 0)
    low_risk_count = investigation.get("low_risk", 0)

    indicators = provider.get("fraud_indicators") or []
    flagged_count = sum(1 for ind in indicators if ind.get("status") == "flagged")
    warning_count = sum(1 for ind in indicators if ind.get("status") == "warning")

    risk_label = risk_level.lower()
    flagged_pct = fraud_prob * 100

    parts = []
    parts.append(
        f"This report presents the findings of the healthcare fraud investigation "
        f"for Provider <b>{provider_id}</b>. "
        f"The analysis reviewed claims submitted by this provider and assessed "
        f"fraud risk using the FraudShield machine learning pipeline."
    )
    parts.append(
        f"Provider {provider_id} has been classified as <b>{risk_label} risk</b> "
        f"with a fraud probability of <b>{flagged_pct:.1f}%</b> "
        f"(model confidence: {confidence:.1f}%). "
        f"The overall prediction is <b>{prediction}</b>."
    )

    if flagged_count > 0 or warning_count > 0:
        flag_desc = []
        if flagged_count > 0:
            flag_desc.append(f"{flagged_count} indicator(s) flagged")
        if warning_count > 0:
            flag_desc.append(f"{warning_count} indicator(s) in warning status")
        parts.append(
            f"Of the {len(indicators)} fraud indicators evaluated, "
            f"{', '.join(flag_desc)}."
        )

    if manual_review:
        reason_text = f" ({review_reason})" if review_reason else ""
        parts.append(
            f"<b>Manual review is recommended</b>{reason_text}."
        )
    else:
        parts.append(
            "No manual review is currently required based on the model assessment."
        )

    if len(results) > 1:
        parts.append(
            f"This investigation included {len(results)} providers in total. "
            f"{high_risk_count} were classified as high risk, "
            f"{medium_risk_count} as medium risk, "
            f"and {low_risk_count} as low risk."
        )

    elements.append(Paragraph(" ".join(parts), styles["body"]))

    return elements


def _build_provider_information(
    provider: Dict[str, Any],
    styles: Dict[str, ParagraphStyle],
) -> List[Any]:
    """Build the Provider Information section."""
    elements: List[Any] = []
    elements.append(Paragraph("Provider Information", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=_COLOR_BORDER))
    elements.append(Spacer(1, 6))

    summary = provider.get("investigation_summary") or {}
    if not summary:
        elements.append(
            Paragraph(
                "Provider statistics are not available for this investigation.",
                styles["body"],
            )
        )
        return elements

    provider_id = provider.get("provider_id", "N/A")
    claims = summary.get("totalClaims", 0)
    reimbursement = summary.get("totalReimbursement", 0)
    avg_claim = summary.get("averageClaimAmount", 0)
    beneficiaries = summary.get("uniqueBeneficiaries", 0)
    physicians = summary.get("uniquePhysicians", 0)

    table_data = [
        [
            Paragraph("Field", styles["table_header"]),
            Paragraph("Value", styles["table_header"]),
        ],
        [
            Paragraph("Provider ID", styles["table_cell_bold"]),
            Paragraph(str(provider_id), styles["table_cell"]),
        ],
        [
            Paragraph("Total Claims Reviewed", styles["table_cell_bold"]),
            Paragraph(f"{claims:,}", styles["table_cell"]),
        ],
        [
            Paragraph("Unique Beneficiaries", styles["table_cell_bold"]),
            Paragraph(f"{beneficiaries:,}", styles["table_cell"]),
        ],
        [
            Paragraph("Unique Physicians", styles["table_cell_bold"]),
            Paragraph(f"{physicians:,}", styles["table_cell"]),
        ],
        [
            Paragraph("Total Reimbursement", styles["table_cell_bold"]),
            Paragraph(f"${reimbursement:,.2f}", styles["table_cell"]),
        ],
        [
            Paragraph("Average Claim Amount", styles["table_cell_bold"]),
            Paragraph(f"${avg_claim:,.2f}", styles["table_cell"]),
        ],
    ]

    table = Table(
        table_data,
        colWidths=[_CONTENT_WIDTH * 0.40, _CONTENT_WIDTH * 0.60],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _COLOR_PRIMARY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (0, -1), _COLOR_SURFACE_SECONDARY),
                ("ROWBACKGROUNDS", (1, 1), (-1, -1), [_COLOR_SURFACE, _COLOR_SURFACE_SECONDARY]),
                ("BOX", (0, 0), (-1, -1), 0.5, _COLOR_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, _COLOR_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elements.append(table)

    return elements


def _build_ai_assessment(
    provider: Dict[str, Any],
    styles: Dict[str, ParagraphStyle],
) -> List[Any]:
    """Build the AI Assessment section."""
    elements: List[Any] = []
    elements.append(Paragraph("AI Assessment", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=_COLOR_BORDER))
    elements.append(Spacer(1, 6))

    risk_level = provider.get("risk_level", "N/A")
    fraud_prob = provider.get("fraud_probability", 0)
    confidence = provider.get("confidence", 0)
    manual_review = provider.get("requires_manual_review", False)
    investigation_score = provider.get("investigation_score", 0)
    prediction = provider.get("prediction", "N/A")
    priority = provider.get("investigation_priority", "N/A")

    manual_text = "Yes" if manual_review else "No"

    table_data = [
        [
            Paragraph("Metric", styles["table_header"]),
            Paragraph("Value", styles["table_header"]),
        ],
        [
            Paragraph("Risk Level", styles["table_cell_bold"]),
            Paragraph(str(risk_level), styles["table_cell"]),
        ],
        [
            Paragraph("Fraud Probability", styles["table_cell_bold"]),
            Paragraph(f"{fraud_prob * 100:.1f}%", styles["table_cell"]),
        ],
        [
            Paragraph("Investigation Score", styles["table_cell_bold"]),
            Paragraph(f"{investigation_score:.1f} / 100", styles["table_cell"]),
        ],
        [
            Paragraph("Model Confidence", styles["table_cell_bold"]),
            Paragraph(f"{confidence:.1f}%", styles["table_cell"]),
        ],
        [
            Paragraph("Prediction", styles["table_cell_bold"]),
            Paragraph(str(prediction), styles["table_cell"]),
        ],
        [
            Paragraph("Investigation Priority", styles["table_cell_bold"]),
            Paragraph(str(priority), styles["table_cell"]),
        ],
        [
            Paragraph("Manual Review Required", styles["table_cell_bold"]),
            Paragraph(manual_text, styles["table_cell"]),
        ],
    ]

    table = Table(
        table_data,
        colWidths=[_CONTENT_WIDTH * 0.40, _CONTENT_WIDTH * 0.60],
    )

    risk_color, risk_bg = _RISK_COLORS.get(
        risk_level, (_COLOR_TEXT_MUTED, _COLOR_SURFACE_SECONDARY)
    )

    row_styles = [
        ("BACKGROUND", (0, 0), (-1, 0), _COLOR_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (0, -1), _COLOR_SURFACE_SECONDARY),
        ("ROWBACKGROUNDS", (1, 1), (-1, -1), [_COLOR_SURFACE, _COLOR_SURFACE_SECONDARY]),
        ("BOX", (0, 0), (-1, -1), 0.5, _COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, _COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        # Color the risk level row
        ("BACKGROUND", (1, 1), (1, 1), risk_bg),
    ]

    table.setStyle(TableStyle(row_styles))
    elements.append(table)

    return elements


def _build_fraud_indicators(
    provider: Dict[str, Any],
    styles: Dict[str, ParagraphStyle],
) -> List[Any]:
    """Build the Fraud Indicators section."""
    elements: List[Any] = []
    elements.append(Paragraph("Fraud Indicators", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=_COLOR_BORDER))
    elements.append(Spacer(1, 6))

    indicators = provider.get("fraud_indicators") or []
    if not indicators:
        elements.append(
            Paragraph(
                "No fraud indicators available for this provider.",
                styles["body"],
            )
        )
        return elements

    table_data = [
        [
            Paragraph("Indicator", styles["table_header"]),
            Paragraph("Status", styles["table_header"]),
            Paragraph("Explanation", styles["table_header"]),
        ]
    ]

    for ind in indicators:
        title = ind.get("title", "N/A")
        status = ind.get("status", "N/A")
        description = ind.get("description", "N/A")

        status_display = status.upper()
        table_data.append(
            [
                Paragraph(str(title), styles["table_cell_bold"]),
                Paragraph(str(status_display), styles["table_cell"]),
                Paragraph(str(description), styles["table_cell"]),
            ]
        )

    table = Table(
        table_data,
        colWidths=[
            _CONTENT_WIDTH * 0.18,
            _CONTENT_WIDTH * 0.12,
            _CONTENT_WIDTH * 0.70,
        ],
    )

    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), _COLOR_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_COLOR_SURFACE, _COLOR_SURFACE_SECONDARY]),
        ("BOX", (0, 0), (-1, -1), 0.5, _COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, _COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]

    # Color-code status column cells
    for i, ind in enumerate(indicators, start=1):
        status = ind.get("status", "normal")
        _, bg = _STATUS_COLORS.get(status, (_COLOR_TEXT_MUTED, _COLOR_SURFACE_SECONDARY))
        style_cmds.append(("BACKGROUND", (1, i), (1, i), bg))

    table.setStyle(TableStyle(style_cmds))
    elements.append(table)

    return elements


def _build_ai_explanation(
    provider: Dict[str, Any],
    styles: Dict[str, ParagraphStyle],
) -> List[Any]:
    """Build the AI Explanation section using the explainability narrative."""
    elements: List[Any] = []
    elements.append(Paragraph("AI Explanation", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=_COLOR_BORDER))
    elements.append(Spacer(1, 6))

    indicators = provider.get("fraud_indicators") or []
    risk_level = provider.get("risk_level", "N/A")
    fraud_prob = provider.get("fraud_probability", 0)
    priority = provider.get("investigation_priority", "N/A")
    provider_id = provider.get("provider_id", "this provider")

    if not indicators:
        elements.append(
            Paragraph(
                "Detailed explanation data is not available for this provider.",
                styles["body"],
            )
        )
        return elements

    # Build narrative from indicators
    flagged = [i for i in indicators if i.get("status") == "flagged"]
    warnings = [i for i in indicators if i.get("status") == "warning"]
    normal = [i for i in indicators if i.get("status") == "normal"]

    sections: List[str] = []

    sections.append(
        f"The FraudShield explainability engine analyzed {len(indicators)} fraud "
        f"indicators for Provider {provider_id}. The provider was classified at "
        f"<b>{risk_level}</b> risk with a fraud probability of "
        f"<b>{fraud_prob * 100:.1f}%</b> "
        f"and an investigation priority of <b>{priority}</b>."
    )

    if flagged:
        titles = ", ".join(i.get("title", "") for i in flagged)
        sections.append(
            f"The following indicators were <b>flagged</b> as high concern: "
            f"{titles}. These elevated signals are the primary drivers behind "
            f"the {risk_level.lower()} risk classification."
        )

    if warnings:
        titles = ", ".join(i.get("title", "") for i in warnings)
        sections.append(
            f"The following indicators raised <b>warnings</b>: "
            f"{titles}. While not individually critical, these patterns "
            f"contribute to the overall risk profile."
        )

    if normal:
        titles = ", ".join(i.get("title", "") for i in normal)
        sections.append(
            f"Indicators assessed as <b>normal</b>: {titles}. "
            f"These values fall within expected ranges."
        )

    sections.append(
        "These findings are based on rule-based threshold analysis applied "
        "to the 12-model feature vector. Thresholds are defined in the "
        "ExplainabilityConfig and can be adjusted for different provider "
        "types or regulatory requirements."
    )

    elements.append(Paragraph(" ".join(sections), styles["body"]))

    return elements


def _build_recommendation(
    provider: Dict[str, Any],
    styles: Dict[str, ParagraphStyle],
) -> List[Any]:
    """Build the Recommendation section."""
    elements: List[Any] = []
    elements.append(Paragraph("Recommendation", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=_COLOR_BORDER))
    elements.append(Spacer(1, 6))

    recommendation = provider.get("recommendation") or {}
    level = recommendation.get("level", "N/A")
    description = recommendation.get("description", "")

    if not description:
        elements.append(
            Paragraph(
                "Recommendation data is not available for this provider.",
                styles["body"],
            )
        )
        return elements

    # Level-specific color
    level_color = _COLOR_TEXT_MUTED
    if "Immediate" in level:
        level_color = _COLOR_ERROR
    elif "Manual" in level:
        level_color = _COLOR_WARNING
    elif "Routine" in level:
        level_color = _COLOR_SUCCESS

    elements.append(Paragraph(f"<b>Recommended Action: {level}</b>", styles["body_bold"]))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(description, styles["body"]))

    # Next actions based on level
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Recommended Next Actions", styles["sub_heading"]))

    if "Immediate" in level:
        actions = [
            "Initiate a full investigation into the provider's billing practices.",
            "Request detailed billing records for the flagged period.",
            "Conduct a comprehensive review of all submitted claims.",
            "Consider scheduling an on-site audit of the provider facility.",
            "Notify the compliance and legal teams for further guidance.",
            "Place a temporary hold on pending reimbursements if warranted.",
        ]
    elif "Manual" in level:
        actions = [
            "Conduct a focused review of the provider's recent claims history.",
            "Verify beneficiary relationships and service documentation.",
            "Cross-reference with other providers in the same geographic area.",
            "Document findings and determine if escalation is needed.",
        ]
    else:
        actions = [
            "Continue standard monitoring of the provider's claim patterns.",
            "Include in the next scheduled periodic audit cycle.",
            "No immediate action required at this time.",
        ]

    for i, action in enumerate(actions, start=1):
        elements.append(
            Paragraph(f"{i}. {action}", styles["body"])
        )

    return elements


def _build_footer(
    styles: Dict[str, ParagraphStyle],
) -> List[Any]:
    """Build the footer section with disclaimer."""
    elements: List[Any] = []
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", thickness=1, color=_COLOR_BORDER))
    elements.append(Spacer(1, 8))
    elements.append(
        Paragraph("Generated by FraudShield AI", styles["footer_brand"])
    )
    elements.append(Spacer(1, 4))
    elements.append(
        Paragraph(
            "This report supports investigator decision-making and should not "
            "replace professional human judgment.",
            styles["footer_disclaimer"],
        )
    )

    return elements


# ---------------------------------------------------------------------------
# Page decorations
# ---------------------------------------------------------------------------


def _header_footer(canvas: Any, doc: Any) -> None:
    """Draw header line and footer on every page."""
    canvas.saveState()

    # Header line
    canvas.setStrokeColor(_COLOR_PRIMARY)
    canvas.setLineWidth(1.5)
    canvas.line(_MARGIN_LEFT, _PAGE_HEIGHT - _MARGIN_TOP + 10, _PAGE_WIDTH - _MARGIN_RIGHT, _PAGE_HEIGHT - _MARGIN_TOP + 10)

    # Footer
    canvas.setStrokeColor(_COLOR_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(_MARGIN_LEFT, _MARGIN_BOTTOM - 10, _PAGE_WIDTH - _MARGIN_RIGHT, _MARGIN_BOTTOM - 10)

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(_COLOR_TEXT_MUTED)

    # Left footer: FraudShield
    canvas.drawString(_MARGIN_LEFT, _MARGIN_BOTTOM - 22, "FraudShield AI")

    # Center footer: disclaimer
    disclaimer = "This report supports investigator decision-making and should not replace professional human judgment."
    text_width = canvas.stringWidth(disclaimer, "Helvetica", 7)
    center_x = (_PAGE_WIDTH - text_width) / 2
    canvas.setFont("Helvetica-Oblique", 7)
    canvas.drawString(center_x, _MARGIN_BOTTOM - 22, disclaimer)

    # Right footer: page number
    page_num = f"Page {doc.page}"
    num_width = canvas.stringWidth(page_num, "Helvetica", 8)
    canvas.drawString(_PAGE_WIDTH - _MARGIN_RIGHT - num_width, _MARGIN_BOTTOM - 22, page_num)

    canvas.restoreState()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_report(
    investigation: Dict[str, Any],
    provider: Dict[str, Any],
) -> bytes:
    """Generate a professional PDF investigation report.

    Parameters
    ----------
    investigation : dict
        The full investigation record (from InvestigationRepository).
    provider : dict
        A single provider result dict (from investigation.results).

    Returns
    -------
    bytes
        The raw PDF content.
    """
    logger.info(
        "[report_generator] Generating report for investigation %s, provider %s",
        investigation.get("investigation_id", "unknown"),
        provider.get("provider_id", "unknown"),
    )

    styles = _build_styles()

    buffer = io.BytesIO()

    doc = BaseDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=_MARGIN_LEFT,
        rightMargin=_MARGIN_RIGHT,
        topMargin=_MARGIN_TOP,
        bottomMargin=_MARGIN_BOTTOM,
        title=f"FraudShield Investigation Report - {investigation.get('investigation_id', 'N/A')}",
        author="FraudShield AI",
    )

    frame = Frame(
        _MARGIN_LEFT,
        _MARGIN_BOTTOM,
        _CONTENT_WIDTH,
        _PAGE_HEIGHT - _MARGIN_TOP - _MARGIN_BOTTOM,
        id="main_frame",
    )

    template = PageTemplate(
        id="main",
        frames=[frame],
        onPage=_header_footer,
    )
    doc.addPageTemplates([template])

    # Build story
    story: List[Any] = []

    # 1. Header
    story.extend(_build_header(investigation, provider, styles))
    story.append(Spacer(1, 12))

    # 2. Executive Summary
    story.extend(_build_executive_summary(investigation, provider, styles))
    story.append(Spacer(1, 12))

    # 3. Provider Information
    story.extend(_build_provider_information(provider, styles))
    story.append(Spacer(1, 12))

    # 4. AI Assessment
    story.extend(_build_ai_assessment(provider, styles))
    story.append(Spacer(1, 12))

    # 5. Fraud Indicators
    story.extend(_build_fraud_indicators(provider, styles))
    story.append(Spacer(1, 12))

    # 6. AI Explanation
    story.extend(_build_ai_explanation(provider, styles))
    story.append(Spacer(1, 12))

    # 7. Recommendation
    story.extend(_build_recommendation(provider, styles))

    # 8. Footer
    story.extend(_build_footer(styles))

    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    logger.info(
        "[report_generator] Report generated — %d bytes",
        len(pdf_bytes),
    )

    return pdf_bytes
