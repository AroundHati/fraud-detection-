"""
Prompt templates for every agent in the FraudShield framework.

Each template is a multiline string that can be rendered with
``str.format()`` or a templating engine before being sent to the LLM.
Agents retrieve their prompts through this module rather than
embedding prompt text in business logic.
"""

from __future__ import annotations


class PromptTemplates:
    """Static collection of prompt templates keyed by agent role.

    All methods are ``@staticmethod`` — no instance state is required.
    """

    # ------------------------------------------------------------------
    # Risk Agent
    # ------------------------------------------------------------------

    @staticmethod
    def risk_agent_analysis() -> str:
        """Return the system + user prompt for risk assessment.

        Placeholders:
            ``{pipeline_results}`` — serialised pipeline output.
            ``{feature_summary}`` — aggregated feature data.
            ``{historical_context}`` — prior investigation notes (if any).
        """
        # TODO: Refine prompt wording once real LLM testing begins.
        return """You are a fraud risk analyst agent within the FraudShield system.

Your task is to analyse pipeline results and produce a structured risk assessment for each healthcare provider.

## Input Data
Pipeline Results:
{pipeline_results}

Feature Summary:
{feature_summary}

Historical Context:
{historical_context}

## Instructions
1. Review the fraud probability scores and confidence values.
2. Evaluate each fraud indicator against known thresholds.
3. Assign a risk level (Critical / High / Medium / Low) to each provider.
4. Flag providers that require immediate manual review.
5. Return your assessment as a JSON object matching the RiskAssessment schema.
"""

    # ------------------------------------------------------------------
    # Investigation Agent
    # ------------------------------------------------------------------

    @staticmethod
    def investigation_narrative() -> str:
        """Return the prompt for generating an investigation narrative.

        Placeholders:
            ``{provider_id}`` — the provider under investigation.
            ``{risk_assessment}`` — serialised risk assessment.
            ``{provider_data}`` — raw provider claim data.
            ``{prior_findings}`` — any previous investigation findings.
        """
        # TODO: Refine prompt wording once real LLM testing begins.
        return """You are an investigative analyst agent within the FraudShield system.

Your task is to generate a thorough, evidence-based investigation narrative for a healthcare provider flagged for potential fraud.

## Provider Under Investigation
Provider ID: {provider_id}

## Risk Assessment
{risk_assessment}

## Provider Data
{provider_data}

## Prior Findings
{prior_findings}

## Instructions
1. Synthesise all available evidence into a coherent narrative.
2. Identify specific fraud patterns (upcoding, unbundling, phantom billing, etc.).
3. Quantify the financial impact where data permits.
4. Cite specific claims, dates, and amounts as evidence.
5. Return your findings as a JSON object matching the InvestigationSummary schema.
"""

    # ------------------------------------------------------------------
    # Report Agent
    # ------------------------------------------------------------------

    @staticmethod
    def report_preparation() -> str:
        """Return the prompt for preparing report content.

        Placeholders:
            ``{investigation_summary}`` — serialised investigation results.
            ``{provider_findings}`` — serialised provider findings list.
            ``{recommendations}`` — serialised recommendation list.
            ``{report_metadata}`` — metadata for the report header/footer.
        """
        # TODO: Refine prompt wording once real LLM testing begins.
        return """You are a report preparation agent within the FraudShield system.

Your task is to structure investigation results into a professional report format suitable for PDF generation.

## Investigation Summary
{investigation_summary}

## Provider Findings
{provider_findings}

## Recommendations
{recommendations}

## Report Metadata
{report_metadata}

## Instructions
1. Organise findings into logical sections.
2. Ensure all numerical data is accurately represented.
3. Generate an executive summary paragraph.
4. Format recommendations with priority labels.
5. Return your output as a JSON object matching the ReportContent schema.
"""

    # ------------------------------------------------------------------
    # Supervisor Agent
    # ------------------------------------------------------------------

    @staticmethod
    def supervisor_routing() -> str:
        """Return the prompt for supervisor agent decision-making.

        Placeholders:
            ``{current_state}`` — serialised current AgentState.
            ``{available_agents}`` — list of registered agent names.
            ``{execution_history}`` — prior agent execution results.
        """
        # TODO: Refine prompt wording once real LLM testing begins.
        return """You are the supervisor agent within the FraudShield multi-agent system.

Your role is to orchestrate the workflow by determining which agent should execute next.

## Current State
{current_state}

## Available Agents
{available_agents}

## Execution History
{execution_history}

## Instructions
1. Review the current state and execution history.
2. Determine which agent must run next (or if the pipeline is complete).
3. Return a routing decision as JSON with the following structure:
   {{
     "next_agent": "<agent_name>",
     "reason": "<brief explanation>",
     "is_complete": false
   }}
4. Set ``is_complete`` to true when all required agents have finished.
"""
