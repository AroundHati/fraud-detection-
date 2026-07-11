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
ExplainabilityEngine
      │
      ▼
Return enriched prediction results with explanations

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
from services.explainability import ExplainabilityEngine, ExplainabilityError

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
    """Orchestrates FeatureBuilder → Predictor → RiskScorer → ExplainabilityEngine.

    Parameters
    ----------
    risk_config : RiskConfig | None
        Optional custom risk thresholds forwarded to ``RiskScorer``.
    """

    def __init__(self, risk_config: Optional[RiskConfig] = None) -> None:
        self._feature_builder = FeatureBuilder()
        self._predictor = Predictor()
        self._risk_scorer = RiskScorer(config=risk_config)
        self._explainability = ExplainabilityEngine()

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
            Enriched prediction results with risk metadata and
            explainability, or an error result on failure.
        """
        # --- 1. Feature engineering ---------------------------------------
        try:
            features_df, provider_ids = self._build_features(
                df, group_by=group_by
            )
        except (FeatureBuilderError, ValueError) as exc:
            logger.error("[ml/pipeline] Feature building failed: %s", exc)
            return PipelineResult(success=False, error=str(exc))

        if features_df.empty:
            logger.info("[ml/pipeline] No features generated")
            return PipelineResult(
                success=True, results=[], total_providers=0, summary={}
            )

        # Convert feature rows to dicts for the explainability engine.
        features_list: List[Dict[str, Any]] = [
            row.to_dict() for _, row in features_df.iterrows()
        ]

        # --- 2. Prediction -----------------------------------------------
        try:
            predictions = self._predictor.predict(
                features_df,
                group_by=None,
                provider_ids=(
                    pd.Series(provider_ids) if provider_ids else None
                ),
            )
        except (PredictorError, ValueError) as exc:
            logger.error("[ml/pipeline] Prediction failed: %s", exc)
            return PipelineResult(success=False, error=str(exc))

        if not predictions:
            logger.info("[ml/pipeline] No predictions generated")
            return PipelineResult(
                success=True, results=[], total_providers=0, summary={}
            )

        # --- 3. Risk scoring ---------------------------------------------
        try:
            scored = self._risk_scorer.score(predictions)
        except RiskScorerError as exc:
            logger.error("[ml/pipeline] Risk scoring failed: %s", exc)
            return PipelineResult(success=False, error=str(exc))

        # --- 4. Explainability -------------------------------------------
        try:
            explanations = self._explainability.explain_batch(
                features_list, scored
            )
            for item, explanation in zip(scored, explanations):
                item.update(explanation)
        except ExplainabilityError as exc:
            logger.error("[ml/pipeline] Explainability failed: %s", exc)
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

    def _build_features(
        self,
        df: pd.DataFrame,
        *,
        group_by: Optional[str],
    ) -> tuple[pd.DataFrame, Optional[list]]:
        """Build the model feature matrix and extract provider IDs.

        Returns
        -------
        (features_df, provider_ids_list)
        """
        provider_ids: Optional[list] = None
        if group_by is not None and group_by in df.columns:
            provider_ids = list(df[group_by].drop_duplicates())

        features_df = self._feature_builder.build_features(df, group_by=group_by)
        return features_df, provider_ids

    @staticmethod
    def _build_summary(scored: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count providers by risk level."""
        summary: Dict[str, int] = {}
        for item in scored:
            level = item.get("risk_level", "Unknown")
            summary[level] = summary.get(level, 0) + 1
        return summary
