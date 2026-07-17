"""
Investigation agent for the FraudShield multi-agent system.

The Investigation Agent generates evidence-based investigation narratives
for flagged providers.  It uses a ``BaseLLMProvider`` for LLM calls and
``RepositoryTool`` for data retrieval.

This module provides two interfaces:

1. ``InvestigationAgent`` (``BaseAgent`` subclass) — used by the legacy
   ``SupervisorAgent`` orchestration pipeline.

2. ``run_investigation_node`` (standalone function) — the LangGraph
   node function consumed by ``StateGraph``.  This is the primary
   interface for the new workflow.

Both interfaces share the same core logic: load the investigation
prompt, call the LLM, parse the structured response, and map it
to the workflow state.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Optional

from ml.agents.base_agent import BaseAgent
from ml.agents.state import InvestigationState
from ml.agents.utils import (
    STATUS_INVESTIGATING,
    append_log,
    begin_node,
    complete_node,
    fail_node,
    validate_pipeline_state,
)
from ml.llm.base import BaseLLMProvider
from ml.llm.exceptions import LLMProviderError
from ml.llm.factory import create_llm_provider
from ml.llm.schemas import InvestigationLLMResponse
from ml.schemas.agent_state import AgentState

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "investigation.txt"


def _load_prompt_template() -> str:
    """Load the investigation prompt template from disk.

    Returns
    -------
    str
        The raw prompt template string with ``{…}`` placeholders.

    Raises
    ------
    FileNotFoundError
        If the prompt file does not exist.
    """
    return PROMPT_PATH.read_text(encoding="utf-8")


def _format_indicators(indicators: list[dict[str, Any]]) -> str:
    """Format the indicators list into a readable text block for the prompt.

    Parameters
    ----------
    indicators : list[dict]
        List of indicator dicts with ``title``, ``status``,
        ``severity``, and ``description`` keys.

    Returns
    -------
    str
        A newline-separated formatted string.
    """
    if not indicators:
        return "No indicators available."

    lines: list[str] = []
    for i, ind in enumerate(indicators, 1):
        title = ind.get("title", "Unknown")
        status = ind.get("status", "unknown")
        severity = ind.get("severity", "unknown")
        desc = ind.get("description", "")
        lines.append(
            f"{i}. {title} — status: {status}, severity: {severity}\n"
            f"   {desc}"
        )
    return "\n".join(lines)


def _format_statistics(statistics: dict[str, Any]) -> str:
    """Format provider statistics into a readable text block.

    Parameters
    ----------
    statistics : dict
        Provider-level aggregate statistics.

    Returns
    -------
    str
        A formatted string of key-value pairs.
    """
    if not statistics:
        return "No statistics available."

    lines = [f"  {k}: {v}" for k, v in statistics.items()]
    return "\n".join(lines)


def _build_investigation_prompt(state: InvestigationState) -> str:
    """Build the investigation prompt from the current workflow state.

    Parameters
    ----------
    state : InvestigationState
        The current workflow state containing provider data and
        pipeline outputs.

    Returns
    -------
    str
        The fully formatted prompt ready to send to the LLM.
    """
    template = _load_prompt_template()

    indicators = state.get("indicators", [])
    statistics = state.get("provider_statistics", {})

    return template.format(
        provider_id=state.get("provider_id", "unknown"),
        risk_level=state.get("risk_level", "unknown"),
        fraud_score=state.get("fraud_score", "N/A"),
        indicators_text=_format_indicators(indicators),
        statistics_text=_format_statistics(statistics),
    )


def _map_llm_findings_to_state(
    response: InvestigationLLMResponse,
    provider_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Map LLM response findings and recommendations to state dicts.

    Parameters
    ----------
    response : InvestigationLLMResponse
        Validated LLM response containing findings and recommendations.
    provider_id : str
        The provider identifier for generating IDs.

    Returns
    -------
    tuple[list[dict], list[dict]]
        A tuple of (findings, recommendations) as plain dicts.
    """
    findings: list[dict[str, Any]] = []
    for i, finding in enumerate(response.findings, 1):
        findings.append({
            "finding_id": f"FI-{provider_id}-{i:04d}",
            "category": finding.category,
            "severity": finding.severity,
            "description": finding.description,
            "evidence": finding.evidence,
            "confidence": finding.confidence,
            "estimated_impact": finding.estimated_impact,
        })

    recommendations: list[dict[str, Any]] = []
    for i, rec in enumerate(response.recommendations, 1):
        recommendations.append({
            "recommendation_id": f"REC-{provider_id}-{i:04d}",
            "category": rec.category,
            "priority": rec.priority,
            "description": rec.description,
            "rationale": rec.rationale,
            "deadline_days": 30,
        })

    return findings, recommendations


class InvestigationAgentError(Exception):
    """Raised when the Investigation Agent encounters a processing failure."""


class InvestigationAgent(BaseAgent):
    """Agent that generates investigation narratives for flagged providers.

    Uses a ``BaseLLMProvider`` for LLM calls and the investigation
    prompt template for prompt construction.

    Attributes:
        name: ``"investigation"``
        description: Brief description of the agent's responsibility.
    """

    name: str = "investigation"
    description: str = (
        "Generates evidence-based investigation narratives for flagged providers."
    )

    def __init__(self, provider: Optional[BaseLLMProvider] = None) -> None:
        """Initialise the investigation agent.

        Parameters
        ----------
        provider : BaseLLMProvider, optional
            LLM provider to use.  If ``None``, a provider is created
            from the factory using environment configuration.
        """
        self._provider = provider

    def _get_provider(self) -> BaseLLMProvider:
        """Return the LLM provider, creating one lazily if needed."""
        if self._provider is None:
            self._provider = create_llm_provider()
        return self._provider

    async def execute(self, state: AgentState) -> AgentState:
        """Execute the investigation workflow.

        Steps:
            1. Validate that ``state.risk_assessment`` is present.
            2. Build the investigation prompt.
            3. Call the LLM for evidence-based narrative generation.
            4. Parse and validate the structured response.
            5. Build ``InvestigationSummary`` with all findings.
            6. Return the updated state.

        Args:
            state: The shared agent state with risk assessment data.

        Returns:
            The updated agent state with investigation data populated.

        Raises:
            InvestigationAgentError: If the investigation cannot be completed.
        """
        logger.info(
            "[%s] execute() called — risk_assessment present=%s",
            self.name,
            state.risk_assessment is not None,
        )

        if state.risk_assessment is None:
            raise InvestigationAgentError(
                "Cannot generate investigation — state.risk_assessment is None."
            )

        provider = self._get_provider()

        prompt = (
            f"Generate an investigation narrative for investigation "
            f"{state.investigation_id} based on the risk assessment data."
        )

        try:
            llm_response = await provider.generate_structured(
                prompt,
                InvestigationLLMResponse,
            )
        except LLMProviderError as exc:
            raise InvestigationAgentError(
                f"LLM call failed: {exc}"
            ) from exc

        logger.info(
            "[%s] Investigation complete — findings=%d recommendations=%d",
            self.name,
            len(llm_response.findings),
            len(llm_response.recommendations),
        )

        return state


# =====================================================================
# LangGraph node function
# =====================================================================


def run_investigation_node(
    state: InvestigationState,
    provider: Optional[BaseLLMProvider] = None,
) -> InvestigationState:
    """LangGraph node: investigate the flagged provider using an LLM.

    This function is registered as a node in the LangGraph ``StateGraph``.
    It loads the investigation prompt, calls the configured LLM provider
    for evidence-based analysis, and maps the structured response to the
    workflow state.

    Parameters
    ----------
    state : InvestigationState
        The current workflow state.  Must contain pipeline outputs
        (``risk_level``, ``indicators``, ``provider_statistics``).
    provider : BaseLLMProvider, optional
        LLM provider instance for dependency injection and testing.
        If ``None``, a provider is created from the factory.

    Returns
    -------
    InvestigationState
        The updated state with ``ai_findings`` and ``recommendations``
        populated, and execution log entries appended.
    """
    start_time = begin_node(state, "investigation_agent", STATUS_INVESTIGATING)

    try:
        validate_pipeline_state(state)

        risk_level = state.get("risk_level", "unknown")
        indicators = state.get("indicators", [])
        provider_id = state.get("provider_id", "unknown")

        logger.info(
            "[investigation_agent] Starting investigation — "
            "provider=%s risk_level=%s indicators=%d",
            provider_id,
            risk_level,
            len(indicators),
        )

        # ------------------------------------------------------------------
        # Build prompt from template and state data
        # ------------------------------------------------------------------
        prompt = _build_investigation_prompt(state)

        # ------------------------------------------------------------------
        # Call LLM provider for structured investigation response
        # ------------------------------------------------------------------
        response = None
        try:
            llm_provider = provider if provider is not None else create_llm_provider()

            import asyncio

            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop is not None and loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    response = pool.submit(
                        asyncio.run,
                        llm_provider.generate_structured(
                            prompt,
                            InvestigationLLMResponse,
                        ),
                    ).result()
            else:
                response = asyncio.run(
                    llm_provider.generate_structured(
                        prompt,
                        InvestigationLLMResponse,
                    )
                )
        except Exception as exc:
            logger.warning(
                "[investigation_agent] LLM unavailable, falling back to "
                "indicator-based findings: %s",
                exc,
            )

        # ------------------------------------------------------------------
        # Map LLM response to state, or build indicator-based fallback
        # ------------------------------------------------------------------
        if response is not None:
            llm_findings, llm_recommendations = _map_llm_findings_to_state(
                response, provider_id
            )
            current_findings = state.get("ai_findings", [])
            current_findings.extend(llm_findings)
            state["ai_findings"] = current_findings

            existing_recs = state.get("recommendations", [])
            existing_recs.extend(llm_recommendations)
            state["recommendations"] = existing_recs

            extra_msg = (
                f"provider={provider_id} "
                f"findings={len(llm_findings)} "
                f"recommendations={len(llm_recommendations)} "
                f"source=llm"
            )
        else:
            # Fallback: indicator-based findings when LLM is unavailable
            fallback_finding: dict[str, Any] = {
                "finding_id": f"FI-{provider_id}-0001",
                "category": "pending_analysis",
                "severity": "Medium",
                "description": (
                    f"Investigation for provider {provider_id}. "
                    f"Risk level: {risk_level}. "
                    f"Indicators flagged: {len(indicators)}. "
                    "LLM unavailable — indicator-based analysis."
                ),
                "evidence": [],
                "confidence": 0.0,
                "estimated_impact": None,
            }

            current_findings = state.get("ai_findings", [])
            current_findings.append(fallback_finding)
            state["ai_findings"] = current_findings

            existing_recs = state.get("recommendations", [])
            for indicator in indicators:
                if isinstance(indicator, dict) and indicator.get("status") == "flagged":
                    rec: dict[str, Any] = {
                        "recommendation_id": (
                            f"REC-{provider_id}-"
                            f"{indicator.get('title', 'UNK')[:20]}"
                        ),
                        "category": "audit",
                        "priority": "Medium",
                        "description": (
                            f"Investigate flagged indicator: "
                            f"{indicator.get('title', 'Unknown')}. "
                            f"Severity: {indicator.get('severity', 'unknown')}."
                        ),
                        "rationale": indicator.get("description", ""),
                        "deadline_days": 30,
                    }
                    existing_recs.append(rec)
            state["recommendations"] = existing_recs

            extra_msg = (
                f"provider={provider_id} "
                f"findings={len(state['ai_findings'])} "
                f"recommendations={len(state['recommendations'])} "
                f"source=fallback"
            )

        return complete_node(
            state,
            "investigation_agent",
            start_time,
            extra_message=extra_msg,
        )

    except Exception as exc:
        logger.exception(
            "[investigation_agent] Investigation failed — %s", exc
        )
        return fail_node(state, "investigation_agent", start_time, str(exc))
