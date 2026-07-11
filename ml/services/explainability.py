"""
Explainability Engine — generates investigator-friendly explanations from
engineered features and risk predictions.

This is a **pure enrichment layer**: it receives the 12-model feature
vector produced by ``FeatureBuilder`` and the scored prediction dict
produced by ``RiskScorer``, then appends three new fields:

- ``investigation_summary`` — aggregate claim statistics
- ``fraud_indicators`` — rule-based explainable risk signals
- ``recommendation`` — suggested next action based on risk level

All logic is deterministic (no LLMs).  Thresholds live in
``ExplainabilityConfig`` so they can be tuned without touching
the explanation logic.
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
class ExplainabilityConfig:
    """Thresholds that control when indicators fire and at what severity.

    Every indicator follows the same pattern:
    - ``normal`` when the value is within the threshold
    - ``warning`` when the value exceeds the warning threshold
    - ``flagged`` when the value exceeds the critical threshold

    Thresholds are expressed as raw feature values (not percentages)
    unless the field name includes ``pct``.
    """

    # Claim volume thresholds.
    claim_volume_warning: int = 500
    claim_volume_critical: int = 2000

    # Total reimbursement thresholds (USD).
    reimbursement_warning: float = 500_000.0
    reimbursement_critical: float = 2_000_000.0

    # Average claim amount thresholds (USD).
    avg_claim_warning: float = 3_000.0
    avg_claim_critical: float = 10_000.0

    # Inpatient-to-outpatient ratio thresholds.
    ratio_warning: float = 2.0
    ratio_critical: float = 5.0

    # Beneficiary concentration — minimum unique beneficiaries relative
    # to claim count before flagging.  Expressed as a fraction (0.0–1.0).
    beneficiary_min_fraction_warning: float = 0.20
    beneficiary_min_fraction_critical: float = 0.10
    # Absolute minimum below which concentration is always flagged.
    beneficiary_absolute_critical: int = 10
    # Only evaluate when total claims exceed this floor.
    beneficiary_eval_floor: int = 50

    # Physician concentration — same logic as beneficiary concentration.
    physician_min_fraction_warning: float = 0.10
    physician_min_fraction_critical: float = 0.05
    physician_absolute_critical: int = 5
    physician_eval_floor: int = 50

    # Chronic condition concentration (fraction of beneficiaries with
    # 3+ chronic conditions).
    chronic_pct_warning: float = 0.40
    chronic_pct_critical: float = 0.70

    # Distinct diagnosis codes thresholds.
    diagnosis_diversity_warning: int = 20
    diagnosis_diversity_critical: int = 60

    # Average claim duration thresholds (days).
    claim_duration_warning: float = 10.0
    claim_duration_critical: float = 25.0

    def __post_init__(self) -> None:
        """Validate that warning thresholds are strictly less than critical."""
        checks = [
            ("claim_volume", self.claim_volume_warning, self.claim_volume_critical),
            ("reimbursement", self.reimbursement_warning, self.reimbursement_critical),
            ("avg_claim", self.avg_claim_warning, self.avg_claim_critical),
            ("ratio", self.ratio_warning, self.ratio_critical),
            ("chronic_pct", self.chronic_pct_warning, self.chronic_pct_critical),
            ("diagnosis_diversity", self.diagnosis_diversity_warning, self.diagnosis_diversity_critical),
            ("claim_duration", self.claim_duration_warning, self.claim_duration_critical),
        ]
        for name, warn, crit in checks:
            if warn >= crit:
                raise ValueError(
                    f"{name}_warning ({warn}) must be less than "
                    f"{name}_critical ({crit})"
                )


DEFAULT_CONFIG = ExplainabilityConfig()


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class ExplainabilityError(Exception):
    """Raised when explanation generation fails due to invalid input."""


# ---------------------------------------------------------------------------
# Types (plain dicts — no LLM involvement)
# ---------------------------------------------------------------------------

# Indicator status values.
STATUS_NORMAL: str = "normal"
STATUS_WARNING: str = "warning"
STATUS_FLAGGED: str = "flagged"

# Severity values.
SEVERITY_LOW: str = "low"
SEVERITY_MEDIUM: str = "medium"
SEVERITY_HIGH: str = "high"
SEVERITY_CRITICAL: str = "critical"


# ---------------------------------------------------------------------------
# Explainability Engine
# ---------------------------------------------------------------------------

class ExplainabilityEngine:
    """Generates investigator-friendly explanations from features and predictions.

    Parameters
    ----------
    config : ExplainabilityConfig | None
        Threshold configuration.  Uses ``DEFAULT_CONFIG`` when ``None``.
    """

    def __init__(self, config: Optional[ExplainabilityConfig] = None) -> None:
        self._config = config or DEFAULT_CONFIG

    @property
    def config(self) -> ExplainabilityConfig:
        """Return the active configuration (read-only)."""
        return self._config

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def explain(
        self,
        features: Dict[str, Any],
        scored_prediction: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate explanation for a single provider.

        Parameters
        ----------
        features : dict
            The 12-model feature vector produced by ``FeatureBuilder``.
            Keys must match ``feature_columns.json`` exactly.
        scored_prediction : dict
            The enriched prediction dict produced by ``RiskScorer``.
            Must contain ``risk_level`` and ``investigation_priority``.

        Returns
        -------
        dict
            Three new keys to merge into the scored prediction:

            - ``investigation_summary`` — aggregate claim stats
            - ``fraud_indicators`` — list of indicator dicts
            - ``recommendation`` — level + description dict

        Raises
        ------
        ExplainabilityError
            If required fields are missing from either input.
        """
        self._validate_features(features)
        self._validate_scored(scored_prediction)

        summary = self._build_summary(features)
        indicators = self._build_indicators(features, scored_prediction)
        recommendation = self._build_recommendation(scored_prediction)

        return {
            "investigation_summary": summary,
            "fraud_indicators": indicators,
            "recommendation": recommendation,
        }

    def explain_batch(
        self,
        features_list: Sequence[Dict[str, Any]],
        scored_predictions: Sequence[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Generate explanations for a batch of providers.

        Parameters
        ----------
        features_list : sequence of dict
            Feature vectors, one per provider.  Must be the same length
            as *scored_predictions*.
        scored_predictions : sequence of dict
            Scored prediction dicts, one per provider.

        Returns
        -------
        list[dict]
            Explanation dicts (one per provider).

        Raises
        ------
        ExplainabilityError
            If the two sequences have different lengths.
        """
        if len(features_list) != len(scored_predictions):
            raise ExplainabilityError(
                f"Features ({len(features_list)}) and predictions "
                f"({len(scored_predictions)}) must have the same length"
            )

        return [
            self.explain(feat, pred)
            for feat, pred in zip(features_list, scored_predictions)
        ]

    # ------------------------------------------------------------------
    # Internal — validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_features(features: Any) -> None:
        """Ensure *features* is a dict with the required model columns."""
        if not isinstance(features, dict):
            raise ExplainabilityError(
                f"Features must be a dict, got {type(features).__name__}"
            )

    @staticmethod
    def _validate_scored(scored: Any) -> None:
        """Ensure *scored* is a dict with risk metadata."""
        if not isinstance(scored, dict):
            raise ExplainabilityError(
                f"Scored prediction must be a dict, got {type(scored).__name__}"
            )
        if "risk_level" not in scored:
            raise ExplainabilityError(
                "Scored prediction is missing required field 'risk_level'"
            )
        if "investigation_priority" not in scored:
            raise ExplainabilityError(
                "Scored prediction is missing required field "
                "'investigation_priority'"
            )

    # ------------------------------------------------------------------
    # Internal — investigation summary
    # ------------------------------------------------------------------

    def _build_summary(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Map the 12-model features to an investigator-friendly summary."""
        return {
            "totalClaims": int(features.get("TotalClaims", 0)),
            "totalReimbursement": round(
                float(features.get("TotalReimbursement", 0.0)), 2
            ),
            "averageClaimAmount": round(
                float(features.get("AverageClaimAmount", 0.0)), 2
            ),
            "inpatientClaims": int(features.get("InpatientClaims", 0)),
            "outpatientClaims": int(features.get("OutpatientClaims", 0)),
            "uniqueBeneficiaries": int(features.get("UniqueBeneficiaries", 0)),
            "uniquePhysicians": int(
                features.get("UniqueAttendingPhysicians", 0)
            ),
        }

    # ------------------------------------------------------------------
    # Internal — fraud indicators
    # ------------------------------------------------------------------

    def _build_indicators(
        self,
        features: Dict[str, Any],
        scored: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """Generate all fraud indicators from features and risk metadata."""
        cfg = self._config
        indicators: List[Dict[str, str]] = []

        # 1. Claim Volume
        total_claims = int(features.get("TotalClaims", 0))
        status, severity, desc = self._eval_thresholds(
            total_claims,
            cfg.claim_volume_warning,
            cfg.claim_volume_critical,
            low_label="Claim volume is within the normal range for this provider.",
            mid_label=(
                f"Provider submitted {total_claims:,} claims, "
                "which is above the expected volume."
            ),
            high_label=(
                f"Provider submitted {total_claims:,} claims, "
                "significantly exceeding normal activity levels."
            ),
        )
        indicators.append(self._make_indicator(
            "Claim Volume", status, severity, desc,
        ))

        # 2. Reimbursement Volume
        total_reimb = float(features.get("TotalReimbursement", 0.0))
        status, severity, desc = self._eval_thresholds(
            total_reimb,
            cfg.reimbursement_warning,
            cfg.reimbursement_critical,
            low_label="Total reimbursement is within the normal provider range.",
            mid_label=(
                f"Total reimbursement of ${total_reimb:,.2f} "
                "is above the expected range for this provider type."
            ),
            high_label=(
                f"Total reimbursement of ${total_reimb:,.2f} "
                "is significantly elevated and warrants investigation."
            ),
        )
        indicators.append(self._make_indicator(
            "Reimbursement Volume", status, severity, desc,
        ))

        # 3. Average Claim Amount
        avg_claim = float(features.get("AverageClaimAmount", 0.0))
        status, severity, desc = self._eval_thresholds(
            avg_claim,
            cfg.avg_claim_warning,
            cfg.avg_claim_critical,
            low_label="Average claim amount is within the normal range.",
            mid_label=(
                f"Average claim of ${avg_claim:,.2f} "
                "exceeds the typical range for this provider."
            ),
            high_label=(
                f"Average claim of ${avg_claim:,.2f} "
                "is unusually high and may indicate upcoding."
            ),
        )
        indicators.append(self._make_indicator(
            "Average Claim Amount", status, severity, desc,
        ))

        # 4. Inpatient-to-Outpatient Ratio
        ratio = float(features.get("Ratio", 0.0))
        inpatient = int(features.get("InpatientClaims", 0))
        outpatient = int(features.get("OutpatientClaims", 0))
        status, severity, desc = self._eval_thresholds(
            ratio,
            cfg.ratio_warning,
            cfg.ratio_critical,
            low_label=(
                "Inpatient-to-outpatient ratio is within the expected range."
            ),
            mid_label=(
                f"Inpatient-to-outpatient ratio of {ratio:.1f} "
                f"({inpatient} IP / {outpatient} OP) "
                "is higher than typical for this facility type."
            ),
            high_label=(
                f"Inpatient-to-outpatient ratio of {ratio:.1f} "
                f"({inpatient} IP / {outpatient} OP) "
                "is excessively high, suggesting potential inpatient upcoding."
            ),
        )
        indicators.append(self._make_indicator(
            "Inpatient Ratio", status, severity, desc,
        ))

        # 5. Beneficiary Concentration
        status, severity, desc = self._eval_concentration(
            total_claims,
            int(features.get("UniqueBeneficiaries", 0)),
            cfg.beneficiary_eval_floor,
            cfg.beneficiary_min_fraction_warning,
            cfg.beneficiary_min_fraction_critical,
            cfg.beneficiary_absolute_critical,
            entity_label="beneficiaries",
        )
        indicators.append(self._make_indicator(
            "Beneficiary Concentration", status, severity, desc,
        ))

        # 6. Physician Concentration
        status, severity, desc = self._eval_concentration(
            total_claims,
            int(features.get("UniqueAttendingPhysicians", 0)),
            cfg.physician_eval_floor,
            cfg.physician_min_fraction_warning,
            cfg.physician_min_fraction_critical,
            cfg.physician_absolute_critical,
            entity_label="attending physicians",
        )
        indicators.append(self._make_indicator(
            "Physician Concentration", status, severity, desc,
        ))

        # 7. Chronic Condition Concentration
        chronic_pct = float(features.get("PctBeneficiaries3PlusChronic", 0.0))
        status, severity, desc = self._eval_thresholds(
            chronic_pct,
            cfg.chronic_pct_warning,
            cfg.chronic_pct_critical,
            low_label="Chronic condition concentration is within normal bounds.",
            mid_label=(
                f"{chronic_pct:.0%} of beneficiaries have 3+ chronic conditions, "
                "which is above the expected concentration."
            ),
            high_label=(
                f"{chronic_pct:.0%} of beneficiaries have 3+ chronic conditions, "
                "indicating a potentially abnormal case mix."
            ),
        )
        indicators.append(self._make_indicator(
            "Chronic Condition Concentration", status, severity, desc,
        ))

        # 8. Diagnosis Diversity
        diag_codes = int(features.get("DistinctDiagnosisCodes", 0))
        status, severity, desc = self._eval_thresholds(
            diag_codes,
            cfg.diagnosis_diversity_warning,
            cfg.diagnosis_diversity_critical,
            low_label="Diagnosis code diversity is within the expected range.",
            mid_label=(
                f"Provider uses {diag_codes} distinct diagnosis codes, "
                "which is higher than typical and may suggest upcoding."
            ),
            high_label=(
                f"Provider uses {diag_codes} distinct diagnosis codes, "
                "significantly above normal diversity — strong upcoding signal."
            ),
        )
        indicators.append(self._make_indicator(
            "Diagnosis Diversity", status, severity, desc,
        ))

        # 9. Claim Duration
        avg_duration = float(features.get("AverageClaimDuration", 0.0))
        status, severity, desc = self._eval_thresholds(
            avg_duration,
            cfg.claim_duration_warning,
            cfg.claim_duration_critical,
            low_label="Average claim duration is within the normal range.",
            mid_label=(
                f"Average claim duration of {avg_duration:.1f} days "
                "is above the typical range for this provider."
            ),
            high_label=(
                f"Average claim duration of {avg_duration:.1f} days "
                "is unusually long and may indicate inflated billing."
            ),
        )
        indicators.append(self._make_indicator(
            "Claim Duration", status, severity, desc,
        ))

        return indicators

    # ------------------------------------------------------------------
    # Internal — recommendation
    # ------------------------------------------------------------------

    def _build_recommendation(self, scored: Dict[str, Any]) -> Dict[str, str]:
        """Derive the recommended action from the investigation priority."""
        priority = scored["investigation_priority"]
        risk_level = scored["risk_level"]

        if priority in ("Critical", "Urgent"):
            return {
                "level": "Immediate Investigation",
                "description": (
                    f"Risk level is {risk_level} with {priority.lower()} "
                    "priority. Recommend launching a full investigation with "
                    "detailed billing review and potential on-site audit."
                ),
            }

        if priority == "Standard":
            return {
                "level": "Manual Review",
                "description": (
                    f"Risk level is {risk_level} with standard priority. "
                    "Recommend a focused manual review of recent claims "
                    "and billing patterns before determining next steps."
                ),
            }

        return {
            "level": "Routine Monitoring",
            "description": (
                f"Risk level is {risk_level} with routine priority. "
                "Continue standard monitoring and periodic audits."
            ),
        }

    # ------------------------------------------------------------------
    # Internal — threshold evaluation helpers
    # ------------------------------------------------------------------

    def _eval_thresholds(
        self,
        value: float,
        warning_threshold: float,
        critical_threshold: float,
        *,
        low_label: str,
        mid_label: str,
        high_label: str,
    ) -> tuple[str, str, str]:
        """Evaluate a value against warning/critical thresholds.

        Returns
        -------
        (status, severity, description)
        """
        if value >= critical_threshold:
            return STATUS_FLAGGED, SEVERITY_HIGH, high_label
        if value >= warning_threshold:
            return STATUS_WARNING, SEVERITY_MEDIUM, mid_label
        return STATUS_NORMAL, SEVERITY_LOW, low_label

    def _eval_concentration(
        self,
        total_claims: int,
        unique_entities: int,
        eval_floor: int,
        min_fraction_warning: float,
        min_fraction_critical: float,
        absolute_critical: int,
        *,
        entity_label: str,
    ) -> tuple[str, str, str]:
        """Evaluate beneficiary/physician concentration.

        A provider with many claims but very few unique entities
        (beneficiaries or physicians) is suspicious.

        Returns
        -------
        (status, severity, description)
        """
        if total_claims < eval_floor:
            return (
                STATUS_NORMAL,
                SEVERITY_LOW,
                f"Insufficient claim volume ({total_claims}) to evaluate "
                f"{entity_label} concentration.",
            )

        fraction = unique_entities / total_claims if total_claims > 0 else 1.0

        if unique_entities <= absolute_critical or fraction < min_fraction_critical:
            return (
                STATUS_FLAGGED,
                SEVERITY_HIGH,
                f"Only {unique_entities} unique {entity_label} across "
                f"{total_claims:,} claims (ratio: {fraction:.1%}), "
                f"suggesting concentrated billing from a small network.",
            )

        if fraction < min_fraction_warning:
            return (
                STATUS_WARNING,
                SEVERITY_MEDIUM,
                f"{unique_entities} unique {entity_label} across "
                f"{total_claims:,} claims (ratio: {fraction:.1%}), "
                f"which is below the expected distribution.",
            )

        return (
            STATUS_NORMAL,
            SEVERITY_LOW,
            f"{entity_label.capitalize()} distribution is within "
            f"the normal range ({unique_entities} across "
            f"{total_claims:,} claims).",
        )

    # ------------------------------------------------------------------
    # Internal — indicator factory
    # ------------------------------------------------------------------

    @staticmethod
    def _make_indicator(
        label: str,
        status: str,
        severity: str,
        description: str,
    ) -> Dict[str, str]:
        """Create a single indicator dict."""
        return {
            "title": label,
            "status": status,
            "severity": severity,
            "description": description,
        }
