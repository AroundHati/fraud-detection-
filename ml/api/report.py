"""
FastAPI endpoint for PDF investigation report generation.

Routes
------
POST /api/ml/investigations/{investigation_id}/report
    Generate a PDF report for a specific investigation and provider.

Start the server
----------------
::

    cd ml
    uvicorn api.analyze:app --reload --port 8000

This module is mounted into the main ``analyze:app`` via ``include_router``.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from pydantic import BaseModel

from ml.services.report_generator import generate_report

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter()


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------


class ReportRequest(BaseModel):
    provider_id: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post(
    "/api/ml/investigations/{investigation_id}/report",
    response_class=Response,
)
async def generate_investigation_report(
    investigation_id: str,
    request: ReportRequest,
) -> Response:
    """Generate a PDF investigation report.

    Parameters
    ----------
    investigation_id : str
        The investigation to report on.
    request : ReportRequest
        Body containing ``provider_id``.

    Returns
    -------
    Response
        PDF binary content with ``application/pdf`` content type.

    Raises
    ------
    400 — Invalid investigation ID.
    404 — Investigation not found.
    404 — Provider not found in investigation results.
    500 — PDF generation failure.
    """
    # Lazy-import the repository to avoid circular imports.
    from ml.services.investigation_repository import (
        InvestigationRepository,
        InvalidInvestigationError,
        InvestigationNotFoundError,
    )

    repo = InvestigationRepository()
    repo.initialize_database()

    try:
        inv = repo.get(investigation_id)
    except InvalidInvestigationError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid investigation ID: {investigation_id}",
        )
    except InvestigationNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Investigation not found: {investigation_id}",
        )

    results = inv.results or []
    provider = None
    for r in results:
        if r.get("provider_id") == request.provider_id:
            provider = r
            break

    if provider is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Provider {request.provider_id} not found in "
                f"investigation {investigation_id}"
            ),
        )

    # Build investigation dict matching the repository structure
    investigation_dict: Dict[str, Any] = {
        "investigation_id": inv.investigation_id,
        "created_at": inv.created_at,
        "updated_at": inv.updated_at,
        "uploaded_filename": inv.uploaded_filename,
        "status": inv.status,
        "provider_count": inv.provider_count,
        "high_risk": inv.high_risk,
        "medium_risk": inv.medium_risk,
        "low_risk": inv.low_risk,
        "summary": inv.summary,
        "results": inv.results,
    }

    try:
        pdf_bytes = generate_report(investigation_dict, provider)
    except Exception as exc:
        logger.error(
            "[report/api] PDF generation failed for %s / %s: %s",
            investigation_id,
            request.provider_id,
            exc,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to generate report PDF",
        )

    filename = f"FraudShield-Report-{investigation_id}-{request.provider_id}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
