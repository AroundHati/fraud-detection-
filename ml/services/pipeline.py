"""
Pipeline — orchestrates the complete fraud detection workflow.

CSV DataFrame
      │
      ▼
FeatureBuilder
      │
      ▼
Predictor
      │
      ▼
RiskScorer
      │
      ▼
Return enriched prediction results

This module owns the orchestration logic.  The API layer calls
``Pipeline.run()`` and receives a structured result dictionary — it
never needs to import the individual services.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd

from services.feature_builder import FeatureBuilder, FeatureBuilderError
from services.predictor import Predictor, PredictorError
from services.risk_scorer import RiskScorer, RiskConfig, RiskScorerError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class PipelineResult:
    """Structured result returned by ``Pipeline.run()``.

    Attributes
    ----------
    success : bool
        Whether the pipeline completed without error.
    results : list[dict]
        Enriched prediction dicts (one per provider).
    total_providers : int
        Number of providers scored.
    summary : dict
        Aggregate counts by risk level.
    error : str | None
        Error message when *success* is ``False``.
    """

    success: bool
    results: List[Dict[str, Any]] = field(default_factory=list)
    total_providers: int = 0
    summary: Dict[str, int] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dict suitable for JSON responses."""
        out: Dict[str, Any] = {"success": self.success}
        if self.success:
            out["data"] = {
                "results": self.results,
                "total_providers": self.total_providers,
                "summary": self.summary,
            }
        else:
            out["error"] = self.error or "Unknown pipeline error"
        return out


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class PipelineError(Exception):
    """Raised when the pipeline fails at any stage."""


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class Pipeline:
    """Orchestrates FeatureBuilder → Predictor → RiskScorer.

    Parameters
    ----------
    risk_config : RiskConfig | None
        Optional custom risk thresholds forwarded to ``RiskScorer``.
    """

    def __init__(self, risk_config: Optional[RiskConfig] = None) -> None:
        self._feature_builder = FeatureBuilder()
        self._predictor = Predictor()
        self._risk_scorer = RiskScorer(config=risk_config)

    @property
    def feature_columns(self) -> List[str]:
        """Feature names expected by the model."""
        return self._predictor.feature_columns

    def run(
        self,
        df: pd.DataFrame,
        *,
        group_by: Optional[str] = "provider_id",
    ) -> PipelineResult:
        """Execute the full fraud detection pipeline.

        Parameters
        ----------
        df : pd.DataFrame
            Raw claims data.  Must contain the eight columns required
            by ``FeatureBuilder`` (e.g. ``beneficiary_id``,
            ``claim_amount``, ``claim_type``, …).
        group_by : str | None
            Column to group claims by before feature engineering.
            Pass ``None`` to treat the entire DataFrame as one group.

        Returns
        -------
        PipelineResult
            Enriched prediction results with risk metadata, or an
            error result on failure.
        """
        try:
            predictions = self._predictor.predict(df, group_by=group_by)
        except (PredictorError, FeatureBuilderError, ValueError) as exc:
            logger.error("[ml/pipeline] Prediction failed: %s", exc)
            return PipelineResult(success=False, error=str(exc))

        if not predictions:
            logger.info("[ml/pipeline] No predictions generated")
            return PipelineResult(
                success=True, results=[], total_providers=0, summary={}
            )

        try:
            scored = self._risk_scorer.score(predictions)
        except RiskScorerError as exc:
            logger.error("[ml/pipeline] Risk scoring failed: %s", exc)
            return PipelineResult(success=False, error=str(exc))

        summary = self._build_summary(scored)

        logger.info(
            "[ml/pipeline] Completed — %d provider(s) scored, summary: %s",
            len(scored),
            summary,
        )

        return PipelineResult(
            success=True,
            results=scored,
            total_providers=len(scored),
            summary=summary,
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _build_summary(scored: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count providers by risk level."""
        summary: Dict[str, int] = {}
        for item in scored:
            level = item.get("risk_level", "Unknown")
            summary[level] = summary.get(level, 0) + 1
        return summary
