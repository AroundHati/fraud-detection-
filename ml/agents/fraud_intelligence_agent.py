"""
Fraud intelligence agent for the FraudShield multi-agent workflow.

The Fraud Intelligence Agent performs deep analysis of investigation
findings, knowledge base context, and ML pipeline outputs to identify
fraud patterns, estimate financial impact, and generate actionable
intelligence.  It uses ``BaseLLMProvider`` for LLM calls.

This module provides two interfaces:

1. ``FraudIntelligenceAgent`` (``BaseAgent`` subclass) — used by the
   legacy ``SupervisorAgent`` orchestration pipeline.

2. ``run_fraud_intelligence_node`` (standalone function) — the LangGraph
   node function consumed by ``StateGraph``.  This is the primary
   interface for the new workflow.

Both interfaces share the same core logic: load the fraud analysis
prompt, build comprehensive context from all prior agent outputs,
call the LLM, parse the structured response, and map it to the
workflow state.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from ml.agents.base_agent import BaseAgent
from ml.agents.state import InvestigationState
from ml.agents.utils import (
    STATUS_INTELLIGENCE_COMPLETE,
    begin_node,
    complete_node,
    fail_node,
    validate_state,
)
from ml.llm.base import BaseLLMProvider
from ml.llm.exceptions import LLMProviderError
from ml.llm.factory import create_llm_provider
from ml.llm.schemas import FraudIntelligenceLLMResponse
from ml.schemas.agent_state import AgentState

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "fraud.txt"


# =====================================================================
# Prompt construction helpers
# =====================================================================


def _load_prompt_template() -> str:
    """Load the fraud intelligence prompt template from disk.

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


def _format_findings(findings: list[dict[str, Any]]) -> str:
    """Format investigation findings into a readable text block.

    Parameters
    ----------
    findings : list[dict]
        Investigation finding dicts with ``finding_id``, ``category``,
        ``severity``, ``description``, ``evidence``, ``confidence``,
        and ``estimated_impact`` keys.

    Returns
    -------
    str
        A newline-separated formatted string.
    """
    if not findings:
        return "No investigation findings available."

    lines: list[str] = []
    for i, f in enumerate(findings, 1):
        fid = f.get("finding_id", "unknown")
        category = f.get("category", "unknown")
        severity = f.get("severity", "unknown")
        description = f.get("description", "")
        confidence = f.get("confidence", 0.0)
        impact = f.get("estimated_impact")
        evidence = f.get("evidence", [])

        lines.append(
            f"{i}. [{fid}] {category} — severity: {severity}, "
            f"confidence: {confidence:.2f}"
        )
        if impact is not None:
            lines.append(f"   Estimated impact: ${impact:,.2f}")
        lines.append(f"   {description}")
        if evidence:
            lines.append(f"   Evidence: {', '.join(str(e) for e in evidence)}")

    return "\n".join(lines)


def _format_documents(documents: list[dict[str, Any]]) -> str:
    """Format retrieved knowledge base documents into a readable text block.

    Parameters
    ----------
    documents : list[dict]
        Document dicts with ``source``, ``content``, and
        ``relevance_score`` keys.

    Returns
    -------
    str
        A formatted string of document summaries.
    """
    if not documents:
        return "No knowledge base documents available."

    lines: list[str] = []
    for i, doc in enumerate(documents, 1):
        source = doc.get("source", "unknown")
        content = doc.get("content", "")
        score = doc.get("relevance_score", 0.0)

        lines.append(f"{i}. Source: {source} (relevance: {score:.2f})")
        # Truncate long document content for prompt efficiency.
        preview = content[:500] + "..." if len(content) > 500 else content
        lines.append(f"   {preview}")

    return "\n".join(lines)


def _format_indicators(indicators: list[dict[str, Any]]) -> str:
    """Format fraud indicators into a readable text block.

    Parameters
    ----------
    indicators : list[dict]
        Indicator dicts with ``title``, ``status``, ``severity``,
        and ``description`` keys.

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


def _format_prediction(prediction: dict[str, Any]) -> str:
    """Format the ML prediction into a readable text block.

    Parameters
    ----------
    prediction : dict
        Prediction result dict with ``prediction``, ``fraud_probability``,
        and ``confidence`` keys.

    Returns
    -------
    str
        A formatted string of prediction details.
    """
    if not prediction:
        return "No prediction available."

    parts: list[str] = []
    if "prediction" in prediction:
        parts.append(f"  Prediction: {prediction['prediction']}")
    if "fraud_probability" in prediction:
        prob = prediction["fraud_probability"]
        parts.append(f"  Fraud probability: {prob:.4f}")
    if "confidence" in prediction:
        conf = prediction["confidence"]
        parts.append(f"  Model confidence: {conf:.2f}%")
    if "provider_id" in prediction:
        parts.append(f"  Provider: {prediction['provider_id']}")

    return "\n".join(parts) if parts else "No prediction available."


def _build_intelligence_prompt(state: InvestigationState) -> str:
    """Build the fraud intelligence prompt from the current workflow state.

    Parameters
    ----------
    state : InvestigationState
        The current workflow state containing pipeline outputs,
        investigation findings, and knowledge base documents.

    Returns
    -------
    str
        The fully formatted prompt ready to send to the LLM.
    """
    template = _load_prompt_template()

    indicators = state.get("indicators", [])
    statistics = state.get("provider_statistics", {})
    findings = state.get("ai_findings", [])
    documents = state.get("retrieved_documents", [])
    prediction = state.get("prediction", {})

    return template.format(
        provider_id=state.get("provider_id", "unknown"),
        risk_level=state.get("risk_level", "unknown"),
        fraud_score=state.get("fraud_score", "N/A"),
        prediction_text=_format_prediction(prediction),
        findings_text=_format_findings(findings),
        documents_text=_format_documents(documents),
        indicators_text=_format_indicators(indicators),
        statistics_text=_format_statistics(statistics),
    )


# =====================================================================
# Response mapping helpers
# =====================================================================


def _map_intelligence_response_to_state(
    response: FraudIntelligenceLLMResponse,
    provider_id: str,
    state: InvestigationState,
) -> None:
    """Map a validated LLM response into the investigation state.

    This function mutates ``state`` in-place, adding:
    - Intelligence-enriched findings to ``ai_findings``
    - Consolidated recommendations to ``recommendations``
    - The full assessment to ``metadata["fraud_intelligence_assessment"]``

    Parameters
    ----------
    response : FraudIntelligenceLLMResponse
        Validated LLM response from the fraud intelligence analysis.
    provider_id : str
        The provider identifier for generating finding/rec IDs.
    state : InvestigationState
        The current workflow state (mutated in-place).
    """
    # --- Map critical findings into ai_findings ---
    current_findings = list(state.get("ai_findings", []))
    for i, cf in enumerate(response.critical_findings, 1):
        current_findings.append({
            "finding_id": f"INT-{provider_id}-{i:04d}",
            "category": cf.finding_type,
            "severity": cf.severity,
            "description": cf.description,
            "evidence": cf.evidence,
            "confidence": cf.confidence,
            "estimated_impact": cf.estimated_impact,
        })
    state["ai_findings"] = current_findings

    # --- Map recommended actions into recommendations ---
    existing_recs = list(state.get("recommendations", []))
    for i, action in enumerate(response.recommended_actions, 1):
        existing_recs.append({
            "recommendation_id": f"REC-INT-{provider_id}-{i:04d}",
            "category": action.category,
            "priority": action.priority,
            "description": action.description,
            "rationale": action.rationale,
            "deadline_days": action.deadline_days,
        })
    state["recommendations"] = existing_recs

    # --- Store full assessment in metadata for the Report Agent ---
    metadata = dict(state.get("metadata", {}))
    metadata["fraud_intelligence_assessment"] = {
        "overall_assessment": response.overall_assessment,
        "confidence": response.confidence,
        "investigation_priority": response.investigation_priority,
        "supporting_evidence": response.supporting_evidence,
        "risk_factors": response.risk_factors,
        "mitigating_factors": response.mitigating_factors,
        "critical_findings_count": len(response.critical_findings),
        "recommended_actions_count": len(response.recommended_actions),
    }
    state["metadata"] = metadata


# =====================================================================
# Exception class
# =====================================================================


class FraudIntelligenceAgentError(Exception):
    """Raised when the Fraud Intelligence Agent encounters a failure."""


# =====================================================================
# Legacy BaseAgent subclass
# =====================================================================


class FraudIntelligenceAgent(BaseAgent):
    """Agent that performs deep fraud intelligence analysis.

    Uses a ``BaseLLMProvider`` for LLM calls and the fraud intelligence
    prompt template for prompt construction.

    Attributes:
        name: ``"fraud_intelligence"``
        description: Brief description of the agent's responsibility.
    """

    name: str = "fraud_intelligence"
    description: str = (
        "Performs deep analysis of investigation findings and knowledge "
        "base context to identify fraud patterns and generate intelligence."
    )

    def __init__(self, provider: Optional[BaseLLMProvider] = None) -> None:
        """Initialise the fraud intelligence agent.

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
        """Execute the fraud intelligence analysis workflow.

        Steps:
            1. Validate that the state contains investigation data.
            2. Build the fraud intelligence prompt.
            3. Call the LLM for structured intelligence analysis.
            4. Parse and validate the response.
            5. Return the updated state.

        Args:
            state: The shared agent state with investigation data.

        Returns:
            The updated agent state.

        Raises:
            FraudIntelligenceAgentError: If the analysis cannot be completed.
        """
        logger.info(
            "[%s] execute() called", self.name,
        )

        provider = self._get_provider()

        prompt = (
            "Perform fraud intelligence analysis based on "
            "the available investigation data."
        )

        try:
            llm_response = await provider.generate_structured(
                prompt,
                FraudIntelligenceLLMResponse,
            )
        except LLMProviderError as exc:
            raise FraudIntelligenceAgentError(
                f"LLM call failed: {exc}"
            ) from exc

        logger.info(
            "[%s] Intelligence analysis complete — "
            "findings=%d actions=%d confidence=%.2f",
            self.name,
            len(llm_response.critical_findings),
            len(llm_response.recommended_actions),
            llm_response.confidence,
        )

        return state


# =====================================================================
# LangGraph node function
# =====================================================================


def run_fraud_intelligence_node(
    state: InvestigationState,
    provider: Optional[BaseLLMProvider] = None,
) -> InvestigationState:
    """LangGraph node: perform fraud intelligence analysis.

    This function is registered as a node in the LangGraph ``StateGraph``.
    It reads investigation findings, knowledge base documents, and pipeline
    outputs, then performs deep analysis to identify fraud patterns,
    estimate financial impact, and generate actionable intelligence.

    Parameters
    ----------
    state : InvestigationState
        The current workflow state.  Should contain ``ai_findings``
        from the Investigation Agent and ``retrieved_documents``
        from the Knowledge Agent.
    provider : BaseLLMProvider, optional
        LLM provider instance for dependency injection and testing.
        If ``None``, a provider is created from the factory.

    Returns
    -------
    InvestigationState
        The updated state with consolidated ``ai_findings``,
        ``recommendations``, and ``metadata["fraud_intelligence_assessment"]``
        populated, and execution log entries appended.
    """
    start_time = begin_node(
        state, "fraud_intelligence_agent", STATUS_INTELLIGENCE_COMPLETE
    )

    try:
        provider_id = state.get("provider_id", "unknown")
        risk_level = state.get("risk_level", "unknown")
        indicators = state.get("indicators", [])
        ai_findings = state.get("ai_findings", [])
        retrieved_documents = state.get("retrieved_documents", [])

        logger.info(
            "[fraud_intelligence_agent] Analysing intelligence — "
            "provider=%s risk_level=%s findings=%d documents=%d",
            provider_id,
            risk_level,
            len(ai_findings),
            len(retrieved_documents),
        )

        # ------------------------------------------------------------------
        # Build prompt from template and state data
        # ------------------------------------------------------------------
        prompt = _build_intelligence_prompt(state)

        # ------------------------------------------------------------------
        # Call LLM provider for structured intelligence response
        # ------------------------------------------------------------------
        response = None
        try:
            llm_provider = (
                provider if provider is not None else create_llm_provider()
            )

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
                            FraudIntelligenceLLMResponse,
                        ),
                    ).result()
            else:
                response = asyncio.run(
                    llm_provider.generate_structured(
                        prompt,
                        FraudIntelligenceLLMResponse,
                    )
                )
        except Exception as exc:
            logger.warning(
                "[fraud_intelligence_agent] LLM unavailable, falling back "
                "to indicator-based intelligence: %s",
                exc,
            )

        # ------------------------------------------------------------------
        # Map LLM response to state, or build indicator-based fallback
        # ------------------------------------------------------------------
        if response is not None:
            _map_intelligence_response_to_state(response, provider_id, state)

            extra_msg = (
                f"provider={provider_id} "
                f"findings={len(state['ai_findings'])} "
                f"recommendations={len(state['recommendations'])} "
                f"source=llm"
            )
        else:
            # Fallback: indicator-based intelligence when LLM is unavailable
            _build_fallback_intelligence(
                provider_id, risk_level, indicators, state
            )

            extra_msg = (
                f"provider={provider_id} "
                f"findings={len(state['ai_findings'])} "
                f"recommendations={len(state['recommendations'])} "
                f"source=fallback"
            )

        return complete_node(
            state,
            "fraud_intelligence_agent",
            start_time,
            extra_message=extra_msg,
        )

    except Exception as exc:
        logger.exception(
            "[fraud_intelligence_agent] Intelligence analysis failed — %s",
            exc,
        )
        return fail_node(
            state, "fraud_intelligence_agent", start_time, str(exc)
        )


# =====================================================================
# Fallback logic (when LLM is unavailable)
# =====================================================================


def _build_fallback_intelligence(
    provider_id: str,
    risk_level: str,
    indicators: list[dict[str, Any]],
    state: InvestigationState,
) -> None:
    """Build indicator-based fallback intelligence when the LLM is unavailable.

    Produces a deterministic intelligence assessment based solely on
    the indicators and existing findings, without any LLM calls.

    Parameters
    ----------
    provider_id : str
        The provider identifier.
    risk_level : str
        The risk level classification.
    indicators : list[dict]
        The fraud indicators from the pipeline.
    state : InvestigationState
        The current workflow state (mutated in-place).
    """
    flagged_count = len([
        i for i in indicators
        if isinstance(i, dict) and i.get("status") == "flagged"
    ])

    # Determine investigation priority from risk level.
    priority_map = {
        "Critical": "Immediate",
        "High": "High",
        "Medium": "Medium",
        "Low": "Low",
    }
    investigation_priority = priority_map.get(risk_level, "Medium")

    # Build risk factors from indicators.
    risk_factors: list[str] = []
    for ind in indicators:
        if isinstance(ind, dict) and ind.get("status") == "flagged":
            risk_factors.append(
                f"Flagged indicator: {ind.get('title', 'Unknown')} "
                f"(severity: {ind.get('severity', 'unknown')})"
            )

    # Create fallback finding.
    fallback_finding: dict[str, Any] = {
        "finding_id": f"INT-{provider_id}-0001",
        "category": "pending_intelligence_analysis",
        "severity": risk_level,
        "description": (
            f"Fallback intelligence analysis for provider {provider_id}. "
            f"Risk level: {risk_level}. "
            f"Indicators flagged: {flagged_count}. "
            f"LLM unavailable — indicator-based analysis only."
        ),
        "evidence": [
            f"Provider risk level: {risk_level}",
            f"Indicators flagged: {flagged_count}",
        ],
        "confidence": 0.0,
        "estimated_impact": None,
    }

    current_findings = list(state.get("ai_findings", []))
    current_findings.append(fallback_finding)
    state["ai_findings"] = current_findings

    # Build fallback recommendation.
    existing_recs = list(state.get("recommendations", []))
    fallback_rec: dict[str, Any] = {
        "recommendation_id": f"REC-INT-{provider_id}-0001",
        "category": "fraud_intelligence",
        "priority": investigation_priority,
        "description": (
            f"Complete fraud intelligence analysis for provider {provider_id}. "
            f"Cross-reference findings with known fraud patterns and "
            "estimate financial impact."
        ),
        "rationale": (
            f"Risk level {risk_level} with {flagged_count} flagged indicator(s). "
            "Intelligence analysis limited without LLM."
        ),
        "deadline_days": 14,
    }
    existing_recs.append(fallback_rec)
    state["recommendations"] = existing_recs

    # Store fallback assessment in metadata.
    metadata = dict(state.get("metadata", {}))
    metadata["fraud_intelligence_assessment"] = {
        "overall_assessment": (
            f"Fallback assessment for provider {provider_id}. "
            f"Risk level: {risk_level}. "
            f"{flagged_count} indicator(s) flagged. "
            "Full LLM-powered analysis was unavailable."
        ),
        "confidence": 0.0,
        "investigation_priority": investigation_priority,
        "supporting_evidence": [],
        "risk_factors": risk_factors,
        "mitigating_factors": [],
        "critical_findings_count": 0,
        "recommended_actions_count": 1,
        "source": "fallback",
    }
    state["metadata"] = metadata
