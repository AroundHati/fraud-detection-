"""
Risk Scorer — enriches prediction results with business-level investigation metadata.

This module is a **pure enrichment layer**: it reads the output of
``predictor.py`` and appends risk classification fields without
modifying any original prediction values.

All thresholds and business rules live in a single ``RiskConfig``
dataclass so they can be tuned without touching scoring logic.

Design note — extensibility
---------------------------
The ``RiskConfig`` dataclass and the ``RiskScorer`` interface are
deliberately generalised so that future business signals (claim
volume, reimbursement totals, repeat investigations, provider
history, etc.) can be incorporated by extending ``RiskConfig``
and the ``_compute_metadata`` method without changing callers.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RiskConfig:
    """Centralised thresholds and rules for risk classification.

    All numeric thresholds are expressed on the same scale as
    ``fraud_probability`` (0.0 – 1.0).  Changing any value here
    automatically propagates through the scoring logic.

    Attributes
    ----------
    high_threshold : float
        Minimum ``fraud_probability`` for **High** risk.
    medium_threshold : float
        Minimum ``fraud_probability`` for **Medium** risk.
        Values below this are classified as **Low** risk.
    manual_review_threshold : float
        Minimum ``fraud_probability`` that triggers a manual review
        recommendation regardless of the predicted label.
    manual_review_labels : frozenset[str]
        Prediction labels that always trigger manual review.
    critical_priority_threshold : float
        Minimum ``fraud_probability`` for **Critical** priority.
    urgent_priority_threshold : float
        Minimum ``fraud_probability`` for **Urgent** priority.
    standard_priority_threshold : float
        Minimum ``fraud_probability`` for **Standard** priority.
        Values below this are classified as **Routine** priority.
    """

    # Risk level boundaries (fraud_probability scale 0.0 – 1.0).
    high_threshold: float = 0.7
    medium_threshold: float = 0.3

    # Manual review triggers.
    manual_review_threshold: float = 0.5
    manual_review_labels: frozenset[str] = field(
        default_factory=lambda: frozenset({"Yes"})
    )

    # Investigation priority boundaries.
    critical_priority_threshold: float = 0.85
    urgent_priority_threshold: float = 0.7
    standard_priority_threshold: float = 0.4

    def __post_init__(self) -> None:
        """Validate configuration consistency."""
        # frozen=True, so we use object.__setattr__ for any corrections
        # if needed in the future.  For now just validate.
        if not (0.0 <= self.medium_threshold <= self.high_threshold <= 1.0):
            raise ValueError(
                f"Thresholds must satisfy 0 <= medium ({self.medium_threshold}) "
                f"<= high ({self.high_threshold}) <= 1"
            )
        if not (0.0 <= self.standard_priority_threshold <= 1.0):
            raise ValueError(
                f"standard_priority_threshold must be in [0, 1], "
                f"got {self.standard_priority_threshold}"
            )
        if not (0.0 <= self.urgent_priority_threshold <= 1.0):
            raise ValueError(
                f"urgent_priority_threshold must be in [0, 1], "
                f"got {self.urgent_priority_threshold}"
            )
        if not (0.0 <= self.critical_priority_threshold <= 1.0):
            raise ValueError(
                f"critical_priority_threshold must be in [0, 1], "
                f"got {self.critical_priority_threshold}"
            )


# Default configuration — mirrors the project risk thresholds defined in
# context/ml-pipeline.md without importing frontend constants.
DEFAULT_CONFIG = RiskConfig()


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class RiskScorerError(Exception):
    """Raised when scoring fails due to invalid input."""


# ---------------------------------------------------------------------------
# Risk Scorer
# ---------------------------------------------------------------------------

class RiskScorer:
    """Enriches prediction results with risk classification metadata.

    Parameters
    ----------
    config : RiskConfig | None
        Threshold configuration.  Uses ``DEFAULT_CONFIG`` when ``None``.

    Examples
    --------
    >>> scorer = RiskScorer()
    >>> scored = scorer.score([
    ...     {"provider_id": "P001", "prediction": "Yes",
    ...      "fraud_probability": 0.91, "confidence": 91.0}
    ... ])
    >>> scored[0]["risk_level"]
    'High'
    """

    def __init__(self, config: Optional[RiskConfig] = None) -> None:
        self._config = config or DEFAULT_CONFIG

    @property
    def config(self) -> RiskConfig:
        """Return the active configuration (read-only)."""
        return self._config

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score(
        self,
        predictions: Sequence[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Score a batch of prediction results.

        Parameters
        ----------
        predictions : sequence of dict
            Output from ``predictor.Predictor.predict()``.  Each dict
            must contain at least ``fraud_probability`` and
            ``prediction``.  All existing fields are preserved.

        Returns
        -------
        list[dict]
            The same dicts with five additional keys:

            - ``risk_level`` — ``"High"`` / ``"Medium"`` / ``"Low"``
            - ``investigation_priority`` — ``"Critical"`` / ``"Urgent"``
              / ``"Standard"`` / ``"Routine"``
            - ``requires_manual_review`` — ``bool``
            - ``review_reason`` — human-readable explanation
            - ``investigation_score`` — ``fraud_probability * 100``

        Raises
        ------
        RiskScorerError
            If *predictions* is not a sequence, contains non-dict
            items, or is missing required fields.
        """
        if not isinstance(predictions, (list, tuple)):
            raise RiskScorerError(
                f"Expected a list or tuple of dicts, got {type(predictions).__name__}"
            )

        results: List[Dict[str, Any]] = []
        for idx, item in enumerate(predictions):
            self._validate_item(item, idx)
            enriched = dict(item)  # shallow copy — never mutate input
            metadata = self._compute_metadata(item)
            enriched.update(metadata)
            results.append(enriched)

        logger.info(
            "[ml/risk_scorer] Scored %d prediction(s)", len(results)
        )
        return results

    # ------------------------------------------------------------------
    # Internal — validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_item(item: Any, index: int) -> None:
        """Ensure *item* is a dict with the required fields."""
        if not isinstance(item, dict):
            raise RiskScorerError(
                f"Item at index {index} is not a dict: {type(item).__name__}"
            )
        if "fraud_probability" not in item:
            raise RiskScorerError(
                f"Item at index {index} is missing required field "
                f"'fraud_probability'"
            )
        if "prediction" not in item:
            raise RiskScorerError(
                f"Item at index {index} is missing required field 'prediction'"
            )

    # ------------------------------------------------------------------
    # Internal — metadata computation
    # ------------------------------------------------------------------

    def _compute_metadata(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Derive all business metadata from a single prediction dict.

        This is the primary extension point for future business signals.
        To add new enrichment fields (e.g. claim volume, provider
        history), add new private ``_compute_*`` methods and merge
        their output here — callers need not change.
        """
        prob: float = float(item["fraud_probability"])
        prediction: str = str(item["prediction"])

        return {
            "risk_level": self._determine_risk_level(prob),
            "investigation_priority": self._determine_priority(prob),
            "requires_manual_review": self._determine_manual_review(
                prob, prediction
            ),
            "review_reason": self._determine_review_reason(prob, prediction),
            "investigation_score": round(prob * 100, 2),
        }

    def _determine_risk_level(self, prob: float) -> str:
        """Map fraud_probability to a risk level string."""
        cfg = self._config
        if prob >= cfg.high_threshold:
            return "High"
        if prob >= cfg.medium_threshold:
            return "Medium"
        return "Low"

    def _determine_priority(self, prob: float) -> str:
        """Map fraud_probability to an investigation priority string."""
        cfg = self._config
        if prob >= cfg.critical_priority_threshold:
            return "Critical"
        if prob >= cfg.urgent_priority_threshold:
            return "Urgent"
        if prob >= cfg.standard_priority_threshold:
            return "Standard"
        return "Routine"

    def _determine_manual_review(self, prob: float, prediction: str) -> bool:
        """Decide whether human review is required.

        Triggers when the probability exceeds the reviewer threshold
        *or* the predicted label matches a known high-risk category.
        """
        cfg = self._config
        if prob >= cfg.manual_review_threshold:
            return True
        if prediction in cfg.manual_review_labels:
            return True
        return False

    def _determine_review_reason(self, prob: float, prediction: str) -> str:
        """Generate a human-readable explanation for the review decision."""
        cfg = self._config

        if prob >= cfg.high_threshold:
            return "High fraud probability"
        if prediction in cfg.manual_review_labels:
            return f"Model predicted '{prediction}' — flagged for review"
        if prob >= cfg.medium_threshold:
            return "Medium fraud probability — monitoring recommended"
        if prob >= cfg.manual_review_threshold:
            return "Elevated fraud probability"
        return "No review required"
