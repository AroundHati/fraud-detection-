"""
FastAPI endpoint for the fraud detection analysis pipeline and
investigation repository.

This is a **thin** HTTP layer — all business logic lives in
``services/pipeline.py`` and ``services/investigation_repository.py``.

Routes
------
POST /api/ml/analyze          — Analyse a CSV and persist the investigation.
GET  /api/ml/investigations   — List all investigations.
GET  /api/ml/investigations/stats — Aggregate counts.
GET  /api/ml/investigations/{id}  — Fetch a single investigation.

Start the server
----------------
::

    cd ml
    uvicorn api.analyze:app --reload --port 8000
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import pandas as pd

from ml.services.pipeline import Pipeline, PipelineError
from ml.services.investigation_repository import (
    InvestigationRepository,
    InvestigationCreate,
    InvestigationRepositoryError,
    InvestigationNotFoundError,
    InvalidInvestigationError,
)
from ml.api.report import router as report_router

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="FraudShield ML API",
    description="Healthcare fraud detection pipeline endpoint",
    version="0.1.0",
)

# Allow the Next.js dev server to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the report generation router.
app.include_router(report_router)

# ---------------------------------------------------------------------------
# Lazy-loaded singletons
# ---------------------------------------------------------------------------

_pipeline: Pipeline | None = None
_repo: InvestigationRepository | None = None


def _get_pipeline() -> Pipeline:
    global _pipeline  # noqa: PLW0603
    if _pipeline is None:
        _pipeline = Pipeline()
        logger.info("[ml/api] Pipeline initialised")
    return _pipeline


def _get_repo() -> InvestigationRepository:
    global _repo  # noqa: PLW0603
    if _repo is None:
        _repo = InvestigationRepository()
        _repo.initialize_database()
        logger.info("[ml/api] Investigation repository initialised")
    return _repo


# ---------------------------------------------------------------------------
# Allowed file types and size limits
# ---------------------------------------------------------------------------

_ALLOWED_EXTENSIONS: set[str] = {".csv"}
_MAX_FILE_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB


# ---------------------------------------------------------------------------
# Pydantic response models
# ---------------------------------------------------------------------------

class InvestigationResponse(BaseModel):
    investigation_id: str
    created_at: str
    updated_at: str
    uploaded_filename: Optional[str] = None
    status: str
    provider_count: int
    high_risk: int
    medium_risk: int
    low_risk: int
    summary: Optional[Dict[str, Any]] = None
    results: Optional[List[Dict[str, Any]]] = None


class InvestigationStats(BaseModel):
    total: int
    pending: int
    running: int
    completed: int
    failed: int
    high_risk_total: int
    medium_risk_total: int
    low_risk_total: int


# ---------------------------------------------------------------------------
# Routes — Health
# ---------------------------------------------------------------------------


@app.get("/api/ml/health")
async def health() -> Dict[str, str]:
    """Simple health-check endpoint."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Routes — Analyze (with repository persistence)
# ---------------------------------------------------------------------------


@app.post("/api/ml/analyze")
async def analyze(
    file: UploadFile = File(..., description="Claims CSV file"),
) -> Dict[str, Any]:
    """Analyse an uploaded CSV of healthcare claims and persist the result.

    Returns
    -------
    200 — ``{"success": true, "data": { ... }, "investigation_id": "INV-..."}``
    400 — Bad file type or empty file.
    422 — Missing required columns in the CSV.
    500 — Pipeline or prediction failure.
    """
    # --- 1. Validate file type -------------------------------------------
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Only CSV files are accepted.",
        )

    # --- 2. Read and validate file size ----------------------------------
    try:
        raw_bytes = await file.read()
    except Exception as exc:
        logger.error("[ml/api] Failed to read uploaded file: %s", exc)
        raise HTTPException(status_code=400, detail="Failed to read uploaded file")

    if len(raw_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if len(raw_bytes) > _MAX_FILE_SIZE_BYTES:
        max_mb = _MAX_FILE_SIZE_BYTES // (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum size of {max_mb} MB",
        )

    # --- 3. Parse CSV into DataFrame -------------------------------------
    try:
        df = pd.read_csv(io.BytesIO(raw_bytes))
    except Exception as exc:
        logger.error("[ml/api] Failed to parse CSV: %s", exc)
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse CSV file: {exc}",
        )

    if df.empty:
        raise HTTPException(
            status_code=400,
            detail="CSV file contains no data rows",
        )

    logger.info(
        "[ml/api] Received CSV '%s' — %d rows, %d columns",
        file.filename,
        len(df),
        len(df.columns),
    )

    # --- 4. Run the ML pipeline ------------------------------------------
    try:
        pipeline = _get_pipeline()
        result = pipeline.run(df, group_by="provider_id")
    except PipelineError as exc:
        logger.error("[ml/api] Pipeline error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Pipeline error: {exc}")
    except Exception as exc:
        logger.error("[ml/api] Unexpected error: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during analysis",
        )

    if not result.success:
        error_msg = result.error or ""
        if "missing" in error_msg.lower() or "column" in error_msg.lower():
            raise HTTPException(status_code=422, detail=error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

    # --- 5. Persist to Investigation Repository --------------------------
    repo = _get_repo()

    high = sum(1 for r in result.results if r.get("risk_level") == "High")
    med = sum(1 for r in result.results if r.get("risk_level") == "Medium")
    low = sum(1 for r in result.results if r.get("risk_level") == "Low")

    inv = repo.create_investigation(
        InvestigationCreate(
            uploaded_filename=file.filename,
            status="completed",
            provider_count=result.total_providers,
            high_risk=high,
            medium_risk=med,
            low_risk=low,
            summary=result.summary,
            results=result.results,
        )
    )

    logger.info(
        "[ml/api] Investigation %s saved — %d providers",
        inv.investigation_id,
        result.total_providers,
    )

    # --- 6. Return structured response -----------------------------------
    response = result.to_dict()
    response["investigation_id"] = inv.investigation_id
    return response


# ---------------------------------------------------------------------------
# Routes — Investigation read operations
# ---------------------------------------------------------------------------


@app.get("/api/ml/investigations")
async def list_investigations() -> List[Dict[str, Any]]:
    """Return all investigations, newest first."""
    repo = _get_repo()
    investigations = repo.list()
    return [
        {
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
        }
        for inv in investigations
    ]


@app.get("/api/ml/investigations/stats")
async def investigation_stats() -> Dict[str, Any]:
    """Return aggregate investigation counts."""
    repo = _get_repo()
    investigations = repo.list()

    total = len(investigations)
    pending = sum(1 for i in investigations if i.status == "pending")
    running = sum(1 for i in investigations if i.status == "running")
    completed = sum(1 for i in investigations if i.status == "completed")
    failed = sum(1 for i in investigations if i.status == "failed")
    high_risk_total = sum(i.high_risk for i in investigations)
    medium_risk_total = sum(i.medium_risk for i in investigations)
    low_risk_total = sum(i.low_risk for i in investigations)

    return {
        "total": total,
        "pending": pending,
        "running": running,
        "completed": completed,
        "failed": failed,
        "high_risk_total": high_risk_total,
        "medium_risk_total": medium_risk_total,
        "low_risk_total": low_risk_total,
    }


@app.get("/api/ml/investigations/{investigation_id}")
async def get_investigation(investigation_id: str) -> Dict[str, Any]:
    """Fetch a single investigation by ID."""
    repo = _get_repo()
    try:
        inv = repo.get(investigation_id)
    except InvalidInvestigationError:
        raise HTTPException(status_code=400, detail=f"Invalid investigation ID: {investigation_id}")
    except InvestigationNotFoundError:
        raise HTTPException(status_code=404, detail=f"Investigation not found: {investigation_id}")

    return {
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
