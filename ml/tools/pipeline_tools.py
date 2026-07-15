"""
Pipeline tools for the FraudShield agent framework.

Wraps the existing ``Pipeline`` service behind a tool interface that
agents can invoke without importing service internals directly.  This
abstraction ensures that agents never instantiate ``FeatureBuilder``,
``Predictor``, ``RiskScorer``, or ``ExplainabilityEngine`` — they
call ``PipelineTool`` which delegates to the ``Pipeline`` service.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class PipelineToolError(Exception):
    """Raised when a pipeline tool operation fails."""


class PipelineTool:
    """Agent-facing wrapper around the ML pipeline service.

    Provides a simplified interface for agents to execute the fraud
    detection pipeline and retrieve per-provider predictions.  The
    ``Pipeline`` service is loaded lazily on first use so that
    importing ``PipelineTool`` alone does not trigger model loading.

    Attributes:
        name: Tool identifier for logging and diagnostics.
    """

    name: str = "pipeline_tool"

    def __init__(self) -> None:
        """Initialise the pipeline tool.

        The underlying ``Pipeline`` service is instantiated lazily on
        the first call to ``run_pipeline`` so that model weights are
        loaded only when actually needed.
        """
        self._pipeline: Any = None
        logger.info("PipelineTool initialised.")

    # ------------------------------------------------------------------
    # Lazy pipeline access
    # ------------------------------------------------------------------

    def _get_pipeline(self) -> Any:
        """Return the ``Pipeline`` service, loading it on first access.

        Returns:
            An initialised ``Pipeline`` instance.

        Raises:
            PipelineToolError: If the ``Pipeline`` class cannot be
                imported or instantiated.
        """
        if self._pipeline is not None:
            return self._pipeline

        try:
            from ml.services.pipeline import Pipeline

            self._pipeline = Pipeline()
            logger.info("Pipeline service loaded via PipelineTool.")
        except ImportError as exc:
            raise PipelineToolError(
                f"Could not import Pipeline service: {exc}"
            ) from exc
        except Exception as exc:
            raise PipelineToolError(
                f"Could not instantiate Pipeline: {exc}"
            ) from exc

        return self._pipeline

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run_pipeline(
        self,
        data: pd.DataFrame,
        *,
        group_by: Optional[str] = "provider_id",
    ) -> Dict[str, Any]:
        """Execute the fraud detection pipeline on the provided data.

        Delegates to ``Pipeline.run()`` and returns the serialised
        ``PipelineResult`` as a plain dictionary.

        Args:
            data: Raw claims DataFrame.  Must contain the columns
                required by ``FeatureBuilder``.
            group_by: Column to group claims by.  Defaults to
                ``"provider_id"``.

        Returns:
            A dictionary with keys ``success``, ``data`` (containing
            ``results``, ``total_providers``, ``summary``), or
            ``error`` on failure.

        Raises:
            PipelineToolError: If the pipeline execution fails or
                returns an unsuccessful result.
        """
        logger.info(
            "PipelineTool.run_pipeline() — rows=%d cols=%d group_by=%s",
            len(data),
            len(data.columns),
            group_by,
        )

        pipeline = self._get_pipeline()

        try:
            result = pipeline.run(data, group_by=group_by)
        except Exception as exc:
            raise PipelineToolError(f"Pipeline execution failed: {exc}") from exc

        if not result.success:
            raise PipelineToolError(
                f"Pipeline returned error: {result.error or 'unknown error'}"
            )

        serialised: Dict[str, Any] = {
            "success": result.success,
            "data": {
                "results": result.results,
                "total_providers": result.total_providers,
                "summary": result.summary,
            },
        }

        logger.info(
            "PipelineTool.run_pipeline() complete — %d providers scored.",
            result.total_providers,
        )
        return serialised

    async def get_provider_predictions(
        self,
        pipeline_data: Dict[str, Any],
        provider_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve predictions for a specific provider from pipeline output.

        Args:
            pipeline_data: The ``"data"`` portion of a pipeline result
                dictionary (as returned by ``run_pipeline``).
            provider_id: The provider identifier to query.

        Returns:
            The provider's prediction dictionary, or ``None`` if no
            matching provider is found.
        """
        results: List[Dict[str, Any]] = pipeline_data.get("results", [])

        for record in results:
            if record.get("provider_id") == provider_id:
                logger.info(
                    "PipelineTool — found prediction for provider %s",
                    provider_id,
                )
                return record

        logger.warning(
            "PipelineTool — provider %s not found in %d results.",
            provider_id,
            len(results),
        )
        return None

    def get_all_results(
        self,
        pipeline_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Extract the list of per-provider results from pipeline output.

        Args:
            pipeline_data: The ``"data"`` portion of a pipeline result
                dictionary.

        Returns:
            The list of per-provider result dictionaries.  Empty list
            if no results are present.
        """
        return pipeline_data.get("results", [])
