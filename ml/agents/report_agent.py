"""
Report agent for the FraudShield multi-agent system.

The Report Agent assembles investigation results into a structured
report format suitable for PDF generation.  It uses ``ReportTool``
for report data preparation.

This module contains ONLY the agent skeleton — no actual report
generation logic is implemented yet.
"""

from __future__ import annotations

import logging

from ml.agents.base_agent import BaseAgent
from ml.schemas.agent_state import AgentState

logger = logging.getLogger(__name__)


class ReportAgentError(Exception):
    """Raised when the Report Agent encounters a processing failure."""


class ReportAgent(BaseAgent):
    """Agent that assembles investigation results into report content.

    Attributes:
        name: ``"report"``
        description: Brief description of the agent's responsibility.
    """

    name: str = "report"
    description: str = (
        "Assembles investigation results into structured report content."
    )

    async def execute(self, state: AgentState) -> AgentState:
        """Execute the report preparation workflow.

        Steps (not yet implemented):
            1. Validate that ``state.investigation_summary`` is present.
            2. Prepare report metadata (ID, timestamps, author).
            3. Use ``ReportTool`` to structure sections.
            4. Populate ``state.report_metadata`` and ``state.report``.
            5. Return the updated state.

        Note:
            This agent does NOT generate PDFs.  PDF generation is
            handled by the downstream ``report_generator`` service.

        Args:
            state: The shared agent state with investigation data.

        Returns:
            The updated agent state with report content populated.

        Raises:
            ReportAgentError: If the report cannot be assembled.
        """
        # TODO: Implement report assembly logic.
        #       1. Validate state.investigation_summary.
        #       2. Build ReportMetadata.
        #       3. Use ReportTool to assemble sections.
        #       4. Build ReportContent and attach to state.
        logger.info(
            "[%s] execute() called — investigation_summary present=%s",
            self.name,
            state.investigation_summary is not None,
        )

        if state.investigation_summary is None:
            raise ReportAgentError(
                "Cannot prepare report — state.investigation_summary is None."
            )

        # TODO: Replace pass with actual implementation.
        pass
