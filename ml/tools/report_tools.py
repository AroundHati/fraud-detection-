"""
Report tools for the FraudShield agent framework.

Wraps the existing ``report_generator`` service behind a tool interface
that agents can invoke without importing service internals directly.

This module contains ONLY the tool skeleton — no actual logic is
implemented yet.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ReportToolError(Exception):
    """Raised when a report tool operation fails."""


class ReportTool:
    """Agent-facing wrapper around the report generation service.

    Provides a simplified interface for agents to prepare report data
    and trigger PDF generation.

    Attributes:
        name: Tool identifier for logging and diagnostics.
    """

    name: str = "report_tool"

    def __init__(self) -> None:
        """Initialise the report tool.

        TODO: Accept and store configuration such as output directory
        and template paths.
        """
        # TODO: Load report configuration from ml.config.
        logger.info("ReportTool initialised.")

    async def prepare_report_data(
        self,
        investigation_summary: dict[str, Any],
        provider_findings: list[dict[str, Any]],
        recommendations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Prepare structured data for PDF report generation.

        Args:
            investigation_summary: Serialised investigation summary.
            provider_findings: List of serialised provider findings.
            recommendations: List of serialised recommendations.

        Returns:
            A dictionary structured for the ``generate_report`` function.

        Raises:
            ReportToolError: If data preparation fails.
        """
        logger.info("ReportTool.prepare_report_data() called.")

        # TODO: Implement report data preparation.
        #       1. Validate all inputs.
        #       2. Assemble the report data dictionary.
        #       3. Return the structured data.
        raise ReportToolError(
            "prepare_report_data() is not yet implemented."
        )

    async def generate_pdf(
        self,
        report_data: dict[str, Any],
        output_path: Optional[str] = None,
    ) -> str:
        """Trigger PDF generation from prepared report data.

        Args:
            report_data: The structured report data from ``prepare_report_data``.
            output_path: Optional override for the output file path.

        Returns:
            The filesystem path where the PDF was written.

        Raises:
            ReportToolError: If PDF generation fails.
        """
        logger.info("ReportTool.generate_pdf() called.")

        # TODO: Implement PDF generation trigger.
        #       1. Import and call report_generator.generate_report().
        #       2. Write the PDF bytes to the output path.
        #       3. Return the output path.
        raise ReportToolError(
            "generate_pdf() is not yet implemented."
        )
