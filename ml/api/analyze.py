"""
FastAPI endpoint for the fraud detection analysis pipeline.

This is a **thin** HTTP layer — all business logic lives in
``services/pipeline.py``.  The endpoint:

1. Receives an uploaded CSV file.
2. Validates the request.
3. Converts the CSV to a pandas DataFrame.
4. Calls ``Pipeline.run(df)``.
5. Returns the structured JSON response.

Start the server
----------------
::

    cd ml
    uvicorn api.analyze:app --reload --port 8000
"""

from __future__ import annotations

import io
import logging
import sys
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

import pandas as pd

# ---------------------------------------------------------------------------
# Path setup — ensure ``services`` is importable when running via uvicorn.
# ---------------------------------------------------------------------------

_SERVICES_DIR = Path(__file__).resolve().parent.parent / "services"
if str(_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVICES_DIR))

from pipeline import Pipeline, PipelineError  # noqa: E402

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

# Lazy-loaded pipeline instance — created once on first request.
_pipeline: Pipeline | None = None


def _get_pipeline() -> Pipeline:
    """Return the singleton Pipeline, initialising on first call."""
    global _pipeline  # noqa: PLW0603
    if _pipeline is None:
        _pipeline = Pipeline()
        logger.info("[ml/api] Pipeline initialised")
    return _pipeline


# ---------------------------------------------------------------------------
# Allowed file types and size limits
# ---------------------------------------------------------------------------

_ALLOWED_EXTENSIONS: set[str] = {".csv"}
_MAX_FILE_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/api/ml/health")
async def health() -> Dict[str, str]:
    """Simple health-check endpoint."""
    return {"status": "ok"}


@app.post("/api/ml/analyze")
async def analyze(
    file: UploadFile = File(..., description="Claims CSV file"),
) -> Dict[str, Any]:
    """Analyse an uploaded CSV of healthcare claims.

    The CSV must contain the columns required by the FeatureBuilder
    (``beneficiary_id``, ``attending_physician``, ``claim_amount``,
    ``deductible``, ``claim_type``, ``claim_duration``,
    ``diagnosis_codes``, ``chronic_condition_count``).

    Returns
    -------
    200 — ``{"success": true, "data": { ... }}``
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

    # --- 5. Return structured response -----------------------------------
    response = result.to_dict()

    if not result.success:
        # Map pipeline failures to 422 (unprocessable) for validation
        # errors and 500 for everything else.
        error_msg = result.error or ""
        if "missing" in error_msg.lower() or "column" in error_msg.lower():
            raise HTTPException(status_code=422, detail=error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

    return response
