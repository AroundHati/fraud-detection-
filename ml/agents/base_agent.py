"""
Abstract base class for all agents in the FraudShield system.

Every agent must subclass ``BaseAgent`` and implement the ``execute``
method.  The base class provides standardised logging, error handling,
and lifecycle hooks so that concrete agents focus solely on their
domain logic.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Optional

from ml.schemas.agent_state import AgentState

logger = logging.getLogger(__name__)


class AgentExecutionError(Exception):
    """Raised when an agent fails during execution."""


class BaseAgent(ABC):
    """Abstract base class defining the contract for every agent.

    Attributes:
        name: Short, unique identifier for this agent (e.g. ``"risk"``).
        description: One-line human-readable description of the agent's role.
    """

    name: str
    """Unique agent identifier used in logs and routing."""

    description: str
    """Human-readable description of the agent's responsibility."""

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------

    def on_start(self, state: AgentState) -> None:
        """Called before ``execute`` — suitable for one-time setup.

        Override in subclasses to perform pre-execution checks such as
        validating that required fields are present in *state*.

        Args:
            state: The shared agent state.
        """
        logger.info("[%s] Agent execution starting.", self.name)

    def on_complete(self, state: AgentState) -> None:
        """Called after ``execute`` returns successfully.

        Override in subclasses to perform cleanup or post-processing.

        Args:
            state: The shared agent state after execution.
        """
        logger.info("[%s] Agent execution completed.", self.name)

    def on_error(self, state: AgentState, error: Exception) -> None:
        """Called when ``execute`` raises an exception.

        Override in subclasses to perform error-specific recovery.

        Args:
            state: The shared agent state at the time of failure.
            error: The exception that was raised.
        """
        logger.error("[%s] Agent execution failed — %s", self.name, error)

    # ------------------------------------------------------------------
    # Core interface
    # ------------------------------------------------------------------

    @abstractmethod
    async def execute(self, state: AgentState) -> AgentState:
        """Execute the agent's core logic.

        Implementations must read from and write to *state* rather than
        returning new data structures.  The method must be idempotent
        — calling it twice with the same state should produce the same
        result.

        Args:
            state: The shared agent state (mutated in-place and returned).

        Returns:
            The updated agent state.

        Raises:
            AgentExecutionError: If the agent cannot complete its task.
        """
        ...

    # ------------------------------------------------------------------
    # Orchestrator helpers (called by the supervisor)
    # ------------------------------------------------------------------

    async def run(self, state: AgentState) -> AgentState:
        """Execute the agent with full lifecycle management.

        This method is the entry point used by the supervisor.  It wraps
        ``execute`` with timing, logging, and error handling.

        Args:
            state: The shared agent state.

        Returns:
            The updated agent state.

        Raises:
            AgentExecutionError: If the agent fails and the error is not
                recoverable.
        """
        start_time = time.monotonic()

        self.on_start(state)
        state.set_timestamp(f"{self.name}_started")
        state.log_entry(agent_name=self.name, status="started")

        try:
            updated_state = await self.execute(state)
            duration = time.monotonic() - start_time

            state.set_timestamp(f"{self.name}_completed")
            state.log_entry(
                agent_name=self.name,
                status="completed",
                duration_seconds=round(duration, 3),
            )
            self.on_complete(updated_state)
            return updated_state

        except Exception as exc:
            duration = time.monotonic() - start_time

            state.record_error(agent_name=self.name, error=str(exc))
            state.log_entry(
                agent_name=self.name,
                status="failed",
                duration_seconds=round(duration, 3),
                error=str(exc),
            )
            self.on_error(state, exc)
            raise AgentExecutionError(
                f"Agent '{self.name}' failed: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name!r})>"
