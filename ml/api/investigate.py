"""
FastAPI endpoint for the Investigation Agent.

This is a **thin** HTTP layer — all business logic lives in
``services/investigation_agent.py``.  The endpoint:

1. Receives a provider investigation result and a question.
2. Validates the request.
3. Calls ``InvestigationAgent.investigate()``.
4. Returns the structured JSON response.

Start the server
----------------
::

    cd ml
    uvicorn api.investigate:app --reload --port 8000
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Path setup — ensure ``services`` is importable when running via uvicorn.
# ---------------------------------------------------------------------------

_SERVICES_DIR = Path(__file__).resolve().parent.parent / "services"
if str(_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVICES_DIR))

from investigation_agent import (  # noqa: E402
    InvestigationAgent,
    InvestigationAgentError,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Investigation Agent API",
    description="AI-powered investigation assistant for healthcare fraud analysis",
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

# Lazy-loaded agent instance — created once on first request.
_agent: InvestigationAgent | None = None


def _get_agent() -> InvestigationAgent:
    """Return the singleton InvestigationAgent, initialising on first call."""
    global _agent  # noqa: PLW0603
    if _agent is None:
        _agent = InvestigationAgent()
        logger.info("[ml/api] InvestigationAgent initialised")
    return _agent


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class InvestigateRequest(BaseModel):
    """Request body for the investigate endpoint."""

    provider: Dict[str, Any] = Field(
        ...,
        description="Structured investigation result for a provider",
    )
    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="The investigator's question about the provider",
    )


class InvestigateResponse(BaseModel):
    """Response body for the investigate endpoint."""

    answer: str
    sources: List[str]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/api/ml/health")
async def health() -> Dict[str, str]:
    """Simple health-check endpoint."""
    return {"status": "ok"}


@app.post("/api/ml/investigate", response_model=Dict[str, Any])
async def investigate(request: InvestigateRequest) -> Dict[str, Any]:
    """Answer an investigator question about a provider.

    The request must include:

    - ``provider`` — the complete investigation result dict (prediction,
      risk score, fraud indicators, recommendation, etc.)
    - ``question`` — the investigator's question.

    Returns
    -------
    200 — ``{"success": true, "data": {"answer": "...", "sources": [...]}}``
    400 — Missing required fields or empty question.
    422 — Invalid provider data.
    500 — Agent processing failure.
    """
    # --- 1. Validate provider data ----------------------------------------
    provider = request.provider
    if not isinstance(provider, dict):
        raise HTTPException(
            status_code=400,
            detail="provider must be an object",
        )

    if "provider_id" not in provider:
        raise HTTPException(
            status_code=422,
            detail="provider data must contain 'provider_id'",
        )

    # --- 2. Run the investigation agent -----------------------------------
    try:
        agent = _get_agent()
        result = agent.investigate(provider, request.question)
    except InvestigationAgentError as exc:
        logger.error("[ml/api] Investigation agent error: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error("[ml/api] Unexpected error: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during investigation",
        )

    # --- 3. Return structured response ------------------------------------
    return {
        "success": True,
        "data": {
            "answer": result.answer,
            "sources": result.sources,
        },
    }
