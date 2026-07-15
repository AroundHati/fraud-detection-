"""
Risk agent for the FraudShield multi-agent system.

The Risk Agent converts ML pipeline output into a strongly typed
``RiskAssessment`` that downstream Investigation and Report agents
consume.  All reasoning is **deterministic** — no LLMs, no prompt
engineering, no probabilistic logic.

Workflow
--------
1. Validate ``AgentState`` (pipeline results must be present).
2. Extract per-provider prediction records.
3. Map each record to a ``ProviderRisk`` model.
4. Compute aggregate statistics (counts, averages, extremes).
5. Determine overall investigation priority.
6. Generate a concise deterministic summary string.
7. Populate ``AgentState.risk_assessment`` and return.
"""

from __future__ import annotations

import logging
import statistics
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ml.agents.base_agent import BaseAgent
from ml.schemas.agent_state import AgentState
from ml.schemas.risk import (
    FraudIndicator,
    InvestigationPriority,
    ProviderRisk,
    RiskAssessment,
    RiskLevel,
)
from ml.tools.pipeline_tools import PipelineTool, PipelineToolError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class RiskAgentError(Exception):
    """Raised when the Risk Agent encounters a processing failure."""


# ---------------------------------------------------------------------------
# Risk Agent
# ---------------------------------------------------------------------------


class RiskAgent(BaseAgent):
    """Agent that analyses pipeline predictions and produces a risk assessment.

    The agent is completely deterministic: it reads pipeline output,
    applies classification thresholds already baked into the pipeline
    (via ``RiskScorer``), and structures the results into a typed
    ``RiskAssessment``.

    Attributes:
        name: ``"risk"``
        description: Brief description of the agent's responsibility.
    """

    name: str = "risk"
    description: str = (
        "Analyses pipeline predictions and produces structured risk assessments."
    )

    def __init__(self, pipeline_tool: Optional[PipelineTool] = None) -> None:
        """Initialise the Risk Agent.

        Args:
            pipeline_tool: Optional pre-configured ``PipelineTool``
                instance.  A new instance is created when *None*.
        """
        self._pipeline_tool = pipeline_tool or PipelineTool()

    # ==================================================================
    # Public interface
    # ==================================================================

    async def execute(self, state: AgentState) -> AgentState:
        """Execute the full risk assessment workflow.

        Steps:
            1. Validate that ``state`` contains pipeline results.
            2. Extract per-provider prediction records.
            3. Build ``ProviderRisk`` models for every provider.
            4. Calculate aggregate statistics.
            5. Determine overall investigation priority.
            6. Generate a deterministic summary.
            7. Assemble and attach a ``RiskAssessment`` to *state*.

        Args:
            state: The shared agent state.  Must contain a populated
                ``pipeline_result`` field (set by the API layer or a
                prior agent).

        Returns:
            The updated agent state with ``risk_assessment`` populated.

        Raises:
            RiskAgentError: If the pipeline result is missing, empty,
                or structurally invalid.
        """
        self._validate_state(state)

        results, summary_dict = self._extract_pipeline_data(state)

        if not results:
            raise RiskAgentError(
                "Pipeline returned zero provider results — nothing to assess."
            )

        provider_risks = self._build_provider_risks(results)

        stats = self._calculate_statistics(provider_risks, summary_dict)

        priority = self._determine_priority(stats)

        requires_review = self._determine_requires_review(stats)

        overall_risk = self._determine_overall_risk_level(stats)

        summary_text = self._generate_summary(stats)

        assessment = self._build_risk_assessment(
            provider_risks=provider_risks,
            stats=stats,
            priority=priority,
            requires_review=requires_review,
            overall_risk=overall_risk,
            summary_text=summary_text,
            pipeline_summary=summary_dict,
        )

        state.risk_assessment = assessment

        logger.info(
            "[%s] Risk assessment created — %d providers, overall=%s, "
            "priority=%s, high=%d, med=%d, low=%d",
            self.name,
            stats["total_providers"],
            overall_risk.value,
            priority.value,
            stats["high_risk_count"],
            stats["medium_risk_count"],
            stats["low_risk_count"],
        )

        return state

    # ==================================================================
    # Step 1 — Validation
    # ==================================================================

    def _validate_state(self, state: AgentState) -> None:
        """Validate that the agent state contains usable pipeline results.

        Checks:
            - ``state.pipeline_result`` is not ``None``.
            - ``state.pipeline_result`` is a ``dict``.
            - The dict contains a truthy ``"data"`` key.

        Args:
            state: The shared agent state.

        Raises:
            RiskAgentError: If validation fails.
        """
        if state.pipeline_result is None:
            raise RiskAgentError(
                "Cannot assess risk — state.pipeline_result is None. "
                "Ensure the pipeline has been executed before the Risk Agent."
            )

        if not isinstance(state.pipeline_result, dict):
            raise RiskAgentError(
                f"state.pipeline_result must be a dict, got "
                f"{type(state.pipeline_result).__name__}."
            )

        has_data = bool(state.pipeline_result.get("data"))
        has_results = bool(state.pipeline_result.get("results"))
        if not has_data and not has_results:
            raise RiskAgentError(
                "state.pipeline_result contains neither 'data' nor 'results' key."
            )

    # ==================================================================
    # Step 2 — Data extraction
    # ==================================================================

    def _extract_pipeline_data(
        self,
        state: AgentState,
    ) -> tuple[List[Dict[str, Any]], Dict[str, int]]:
        """Extract the results list and summary dict from pipeline output.

        Handles both the serialised format produced by
        ``PipelineResult.to_dict()`` (``{"success": ..., "data": {...}}``)
        and a raw dict with ``results`` / ``summary`` keys directly.

        Args:
            state: The shared agent state.

        Returns:
            A tuple of ``(results_list, summary_dict)``.

        Raises:
            RiskAgentError: If the data structure is unrecognised.
        """
        pr = state.pipeline_result  # already validated as dict

        # Format A: {"success": True, "data": {"results": [...], "summary": {...}}}
        data = pr.get("data")
        if isinstance(data, dict):
            results: List[Dict[str, Any]] = data.get("results", [])
            summary_dict: Dict[str, int] = data.get("summary", {})
            return results, summary_dict

        # Format B: {"results": [...], "summary": {...}} (flat)
        if "results" in pr:
            results = pr.get("results", [])
            summary_dict = pr.get("summary", {})
            return results, summary_dict

        raise RiskAgentError(
            "Unrecognised pipeline_result structure — expected 'data' or "
            "'results' key."
        )

    # ==================================================================
    # Step 3 — Build provider risks
    # ==================================================================

    def _build_provider_risks(
        self,
        results: List[Dict[str, Any]],
    ) -> List[ProviderRisk]:
        """Convert each pipeline result dict into a ``ProviderRisk`` model.

        Each result dict is expected to contain at minimum:
            ``provider_id``, ``fraud_probability``, ``prediction``,
            ``confidence``, ``risk_level``, ``investigation_priority``,
            ``requires_manual_review``, ``review_reason``.

        Optionally, explainability fields are included:
            ``fraud_indicators``, ``investigation_summary``,
            ``recommendation``.

        Args:
            results: List of per-provider pipeline result dicts.

        Returns:
            A list of ``ProviderRisk`` models, one per provider.
        """
        risks: List[ProviderRisk] = []

        for record in results:
            risk = self._map_single_provider_risk(record)
            risks.append(risk)

        logger.debug(
            "[%s] Mapped %d provider risk(s).", self.name, len(risks)
        )
        return risks

    def _map_single_provider_risk(
        self,
        record: Dict[str, Any],
    ) -> ProviderRisk:
        """Map a single pipeline result dict to a ``ProviderRisk``.

        Args:
            record: A per-provider pipeline result dict.

        Returns:
            A populated ``ProviderRisk`` model.
        """
        provider_id: str = str(record.get("provider_id", "unknown"))
        fraud_prob: float = float(record.get("fraud_probability", 0.0))
        confidence: float = float(record.get("confidence", 0.0))
        predicted_label: str = str(record.get("prediction", "Unknown"))
        risk_level_str: str = str(record.get("risk_level", "Low"))
        priority_str: str = str(record.get("investigation_priority", "Routine"))
        requires_review: bool = bool(record.get("requires_manual_review", False))
        review_reason: Optional[str] = record.get("review_reason")
        inv_score: float = float(record.get("investigation_score", fraud_prob * 100))

        # Parse enums with fallback to safe defaults.
        try:
            risk_level = RiskLevel(risk_level_str)
        except ValueError:
            risk_level = RiskLevel.LOW

        try:
            priority = InvestigationPriority(priority_str)
        except ValueError:
            priority = InvestigationPriority.ROUTINE

        # Extract fraud indicators (list of dicts from explainability).
        fraud_indicators: List[FraudIndicator] = []
        raw_indicators = record.get("fraud_indicators", [])
        if isinstance(raw_indicators, list):
            for ind in raw_indicators:
                if isinstance(ind, dict):
                    fraud_indicators.append(
                        FraudIndicator(
                            title=str(ind.get("title", "")),
                            status=str(ind.get("status", "normal")),
                            severity=str(ind.get("severity", "low")),
                            description=str(ind.get("description", "")),
                        )
                    )

        # Extract investigation summary and recommendation (pass through).
        inv_summary: Optional[dict] = None
        raw_summary = record.get("investigation_summary")
        if isinstance(raw_summary, dict):
            inv_summary = raw_summary

        recommendation: Optional[dict] = None
        raw_rec = record.get("recommendation")
        if isinstance(raw_rec, dict):
            recommendation = raw_rec

        return ProviderRisk(
            provider_id=provider_id,
            fraud_probability=round(fraud_prob, 6),
            predicted_label=predicted_label,
            confidence=round(confidence, 2),
            risk_level=risk_level,
            priority=priority,
            requires_manual_review=requires_review,
            review_reason=review_reason,
            fraud_indicators=fraud_indicators,
            investigation_score=round(inv_score, 2),
            investigation_summary=inv_summary,
            recommendation=recommendation,
        )

    # ==================================================================
    # Step 4 — Statistics
    # ==================================================================

    def _calculate_statistics(
        self,
        provider_risks: List[ProviderRisk],
        pipeline_summary: Dict[str, int],
    ) -> Dict[str, Any]:
        """Compute aggregate statistics across all provider risks.

        Uses the pipeline's pre-computed summary counts when available
        (they are authoritative) and falls back to recounting from
        ``provider_risks`` when the summary is incomplete.

        Args:
            provider_risks: List of ``ProviderRisk`` models.
            pipeline_summary: Summary dict from the pipeline (e.g.
                ``{"High": 12, "Medium": 5, "Low": 47}``).

        Returns:
            A dictionary of statistics with keys:
                ``total_providers``, ``high_risk_count``,
                ``medium_risk_count``, ``low_risk_count``,
                ``requires_manual_review_count``,
                ``highest_risk_provider``, ``highest_probability``,
                ``average_probability``, ``probabilities``.
        """
        total = len(provider_risks)

        # Use pipeline summary when it covers all risk levels.
        high = pipeline_summary.get("High", 0)
        med = pipeline_summary.get("Medium", 0)
        low = pipeline_summary.get("Low", 0)
        summary_total = high + med + low

        # If the summary total doesn't match, recount from models.
        if summary_total != total or total == 0:
            high = sum(
                1 for r in provider_risks
                if r.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
            )
            med = sum(
                1 for r in provider_risks if r.risk_level == RiskLevel.MEDIUM
            )
            low = sum(
                1 for r in provider_risks if r.risk_level == RiskLevel.LOW
            )

        review_count = sum(
            1 for r in provider_risks if r.requires_manual_review
        )

        # Highest-risk provider.
        highest_provider: Optional[str] = None
        highest_prob: float = 0.0
        if provider_risks:
            top = max(provider_risks, key=lambda r: r.fraud_probability)
            highest_provider = top.provider_id
            highest_prob = top.fraud_probability

        # Average probability.
        probs = [r.fraud_probability for r in provider_risks]
        avg_prob: float = statistics.mean(probs) if probs else 0.0

        return {
            "total_providers": total,
            "high_risk_count": high,
            "medium_risk_count": med,
            "low_risk_count": low,
            "requires_manual_review_count": review_count,
            "highest_risk_provider": highest_provider,
            "highest_probability": round(highest_prob, 6),
            "average_probability": round(avg_prob, 6),
            "probabilities": probs,
        }

    # ==================================================================
    # Step 5 — Priority determination
    # ==================================================================

    @staticmethod
    def _determine_priority(stats: Dict[str, Any]) -> InvestigationPriority:
        """Determine the overall investigation priority from aggregate stats.

        Rules (evaluated in order):
            - Critical: any provider has probability >= 0.85.
            - Urgent: any provider has probability >= 0.7 OR
              high_risk_count >= 5.
            - Standard: high_risk_count > 0 OR average >= 0.4.
            - Routine: everything else.

        Args:
            stats: Statistics dictionary from ``_calculate_statistics``.

        Returns:
            The determined ``InvestigationPriority``.
        """
        highest_prob: float = stats.get("highest_probability", 0.0)
        high_count: int = stats.get("high_risk_count", 0)
        avg_prob: float = stats.get("average_probability", 0.0)

        if highest_prob >= 0.85:
            return InvestigationPriority.CRITICAL

        if highest_prob >= 0.7 or high_count >= 5:
            return InvestigationPriority.URGENT

        if high_count > 0 or avg_prob >= 0.4:
            return InvestigationPriority.STANDARD

        return InvestigationPriority.ROUTINE

    @staticmethod
    def _determine_requires_review(stats: Dict[str, Any]) -> bool:
        """Decide whether the cohort as a whole requires manual review.

        Triggers when:
            - Any individual provider requires review, OR
            - The highest fraud probability exceeds 0.5, OR
            - There are 3 or more high-risk providers.

        Args:
            stats: Statistics dictionary.

        Returns:
            ``True`` if manual review is recommended.
        """
        if stats.get("requires_manual_review_count", 0) > 0:
            return True
        if stats.get("highest_probability", 0.0) >= 0.5:
            return True
        if stats.get("high_risk_count", 0) >= 3:
            return True
        return False

    @staticmethod
    def _determine_overall_risk_level(stats: Dict[str, Any]) -> RiskLevel:
        """Determine the cohort-wide overall risk level.

        Rules:
            - Critical: highest probability >= 0.85.
            - High: any high-risk provider exists.
            - Medium: medium_risk_count > 0 and no high-risk.
            - Low: all providers are low-risk.

        Args:
            stats: Statistics dictionary.

        Returns:
            The overall ``RiskLevel``.
        """
        highest_prob: float = stats.get("highest_probability", 0.0)
        high_count: int = stats.get("high_risk_count", 0)
        med_count: int = stats.get("medium_risk_count", 0)

        if highest_prob >= 0.85:
            return RiskLevel.CRITICAL

        if high_count > 0:
            return RiskLevel.HIGH

        if med_count > 0:
            return RiskLevel.MEDIUM

        return RiskLevel.LOW

    # ==================================================================
    # Step 6 — Summary generation
    # ==================================================================

    @staticmethod
    def _generate_summary(stats: Dict[str, Any]) -> str:
        """Generate a concise, deterministic summary of the risk landscape.

        The summary is assembled entirely from numeric stats — no LLM,
        no templates, no free-text generation.

        Args:
            stats: Statistics dictionary.

        Returns:
            A multi-line summary string.
        """
        total: int = stats.get("total_providers", 0)
        high: int = stats.get("high_risk_count", 0)
        med: int = stats.get("medium_risk_count", 0)
        low: int = stats.get("low_risk_count", 0)
        highest_prob: float = stats.get("highest_probability", 0.0)
        avg_prob: float = stats.get("average_probability", 0.0)
        review_count: int = stats.get("requires_manual_review_count", 0)

        if total == 0:
            return "No providers were analysed."

        lines: List[str] = []

        lines.append(f"{total} provider{'s' if total != 1 else ''} analysed.")

        # Risk breakdown.
        breakdown_parts: List[str] = []
        if high > 0:
            breakdown_parts.append(
                f"{high} provider{'s' if high != 1 else ''} classified as High Risk"
            )
        if med > 0:
            breakdown_parts.append(
                f"{med} provider{'s' if med != 1 else ''} classified as Medium Risk"
            )
        if low > 0:
            breakdown_parts.append(
                f"{low} provider{'s' if low != 1 else ''} classified as Low Risk"
            )
        if breakdown_parts:
            lines.append("; ".join(breakdown_parts) + ".")

        # Extremes.
        lines.append(
            f"Highest fraud probability: {highest_prob:.1%}."
        )
        lines.append(
            f"Average fraud probability: {avg_prob:.1%}."
        )

        # Review recommendation.
        if review_count > 0:
            lines.append(
                f"{review_count} provider{'s' if review_count != 1 else ''} "
                f"flagged for immediate manual review."
            )

        return " ".join(lines)

    # ==================================================================
    # Step 7 — Assembly
    # ==================================================================

    def _build_risk_assessment(
        self,
        provider_risks: List[ProviderRisk],
        stats: Dict[str, Any],
        priority: InvestigationPriority,
        requires_review: bool,
        overall_risk: RiskLevel,
        summary_text: str,
        pipeline_summary: Dict[str, int],
    ) -> RiskAssessment:
        """Assemble the final ``RiskAssessment`` model.

        Args:
            provider_risks: Per-provider risk models.
            stats: Aggregate statistics.
            priority: Overall investigation priority.
            requires_review: Whether manual review is required.
            overall_risk: Overall risk level.
            summary_text: Deterministic summary string.
            pipeline_summary: Raw pipeline summary dict.

        Returns:
            A fully populated ``RiskAssessment``.
        """
        assessment = RiskAssessment(
            assessment_id=f"RA-{uuid4().hex[:12].upper()}",
            total_providers=stats["total_providers"],
            overall_risk_level=overall_risk,
            highest_risk_provider=stats["highest_risk_provider"],
            highest_probability=stats["highest_probability"],
            average_probability=stats["average_probability"],
            high_risk_count=stats["high_risk_count"],
            medium_risk_count=stats["medium_risk_count"],
            low_risk_count=stats["low_risk_count"],
            requires_manual_review_count=stats["requires_manual_review_count"],
            investigation_priority=priority,
            requires_manual_review=requires_review,
            provider_risks=provider_risks,
            summary=summary_text,
            processing_metadata={
                "pipeline_summary": pipeline_summary,
                "agent": self.name,
                "version": "1.0.0",
            },
        )

        logger.debug(
            "[%s] RiskAssessment assembled — id=%s providers=%d",
            self.name,
            assessment.assessment_id,
            assessment.total_providers,
        )
        return assessment
