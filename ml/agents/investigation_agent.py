"""
Investigation agent for the FraudShield multi-agent system.

The Investigation Agent generates evidence-based investigation narratives
for flagged providers.  It uses ``RepositoryTool`` for data retrieval
and ``LLMClient`` for narrative generation.

This module contains ONLY the agent skeleton — no actual investigation
logic is implemented yet.
"""

from __future__ import annotations

import logging

from ml.agents.base_agent import BaseAgent
from ml.schemas.agent_state import AgentState

logger = logging.getLogger(__name__)


class InvestigationAgentError(Exception):
    """Raised when the Investigation Agent encounters a processing failure."""


class InvestigationAgent(BaseAgent):
    """Agent that generates investigation narratives for flagged providers.

    Attributes:
        name: ``"investigation"``
        description: Brief description of the agent's responsibility.
    """

    name: str = "investigation"
    description: str = (
        "Generates evidence-based investigation narratives for flagged providers."
    )

    async def execute(self, state: AgentState) -> AgentState:
        """Execute the investigation workflow.

        Steps (not yet implemented):
            1. Validate that ``state.risk_assessment`` is present.
            2. Identify providers requiring investigation (high/critical risk).
            3. For each flagged provider:
               a. Retrieve claim data via ``RepositoryTool``.
               b. Construct an investigation prompt.
               c. Generate a narrative via ``LLMClient``.
               d. Parse and validate the response.
            4. Build ``InvestigationSummary`` with all findings.
            5. Populate ``state.investigation_summary``, ``state.provider_findings``,
               and ``state.recommendations``.
            6. Return the updated state.

        Args:
            state: The shared agent state with risk assessment data.

        Returns:
            The updated agent state with investigation data populated.

        Raises:
            InvestigationAgentError: If the investigation cannot be completed.
        """
        # TODO: Implement investigation logic.
        #       1. Validate state.risk_assessment.
        #       2. Iterate over flagged providers.
        #       3. Use RepositoryTool to fetch provider data.
        #       4. Use LLMClient to generate narratives.
        #       5. Build InvestigationSummary and attach to state.
        logger.info(
            "[%s] execute() called — risk_assessment present=%s",
            self.name,
            state.risk_assessment is not None,
        )

        if state.risk_assessment is None:
            raise InvestigationAgentError(
                "Cannot generate investigation — state.risk_assessment is None."
            )

        # TODO: Replace pass with actual implementation.
        pass
