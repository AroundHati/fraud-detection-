"""
Supervisor agent for the FraudShield multi-agent system.

The supervisor is responsible for orchestration only — it routes
``AgentState`` through the agent pipeline sequentially, updates the
shared state, and returns the final result.  It contains no LLM code
and no ML logic.
"""

from __future__ import annotations

import logging
from typing import Optional

from ml.agents.base_agent import BaseAgent, AgentExecutionError
from ml.schemas.agent_state import AgentState

logger = logging.getLogger(__name__)


class SupervisorError(Exception):
    """Raised when the supervisor encounters an orchestration failure."""


class SupervisorAgent:
    """Orchestrates the sequential execution of agents.

    The supervisor maintains an ordered list of agents and drives
    ``AgentState`` through them one by one.  If an agent fails, the
    supervisor records the error and may optionally skip or retry
    depending on configuration.

    Attributes:
        agents: Ordered list of agents to execute.
        max_retries: Number of retries allowed per agent before skipping.
        enable_tracing: When ``True``, detailed execution traces are
            recorded in ``AgentState.execution_log``.
    """

    def __init__(
        self,
        agents: Optional[list[BaseAgent]] = None,
        max_retries: int = 2,
        enable_tracing: bool = True,
    ) -> None:
        """Initialise the supervisor with an ordered agent pipeline.

        Args:
            agents: Ordered list of ``BaseAgent`` instances.
            max_retries: Retry count per agent on failure.
            enable_tracing: Whether to record detailed execution traces.
        """
        self.agents: list[BaseAgent] = agents or []
        self.max_retries = max_retries
        self.enable_tracing = enable_tracing

        logger.info(
            "SupervisorAgent initialised — agents=%s max_retries=%d",
            [a.name for a in self.agents],
            self.max_retries,
        )

    # ------------------------------------------------------------------
    # Agent registration
    # ------------------------------------------------------------------

    def register_agent(self, agent: BaseAgent) -> None:
        """Add an agent to the end of the execution pipeline.

        Args:
            agent: The agent instance to register.
        """
        self.agents.append(agent)
        logger.info("Agent '%s' registered with supervisor.", agent.name)

    def unregister_agent(self, name: str) -> Optional[BaseAgent]:
        """Remove an agent by name from the pipeline.

        Args:
            name: The ``name`` attribute of the agent to remove.

        Returns:
            The removed agent, or ``None`` if not found.
        """
        for i, agent in enumerate(self.agents):
            if agent.name == name:
                removed = self.agents.pop(i)
                logger.info("Agent '%s' unregistered from supervisor.", name)
                return removed
        logger.warning("Agent '%s' not found — nothing removed.", name)
        return None

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------

    async def orchestrate(self, state: AgentState) -> AgentState:
        """Execute all agents sequentially, passing state through each.

        The supervisor iterates through the registered agent list and
        calls ``agent.run(state)`` for each one.  If an agent fails
        after exhausting retries, the error is recorded and execution
        continues with the next agent.

        Args:
            state: The initial shared state (e.g. populated by the API
                endpoint with pipeline results).

        Returns:
            The final shared state after all agents have executed.

        Raises:
            SupervisorError: If no agents are registered or if a
                critical agent fails irrecoverably.
        """
        if not self.agents:
            logger.error("No agents registered — nothing to orchestrate.")
            raise SupervisorError("No agents registered with the supervisor.")

        state.set_timestamp("supervisor_started")
        state.log_entry(
            agent_name="supervisor",
            status="started",
            message=f"Pipeline of {len(self.agents)} agent(s) beginning.",
        )

        logger.info(
            "Starting orchestration — pipeline=%s",
            [a.name for a in self.agents],
        )

        for agent in self.agents:
            success = await self._run_agent_with_retries(agent, state)

            if not success:
                logger.warning(
                    "Agent '%s' failed after %d attempt(s) — skipping.",
                    agent.name,
                    self.max_retries + 1,
                )

        state.set_timestamp("supervisor_completed")
        state.log_entry(
            agent_name="supervisor",
            status="completed",
            message=f"Pipeline finished. {len(state.errors)} error(s) recorded.",
        )

        logger.info(
            "Orchestration complete — errors=%d", len(state.errors)
        )
        return state

    async def _run_agent_with_retries(
        self,
        agent: BaseAgent,
        state: AgentState,
    ) -> bool:
        """Attempt to run an agent, retrying on failure.

        Args:
            agent: The agent to execute.
            state: The shared state.

        Returns:
            ``True`` if the agent completed successfully, ``False`` otherwise.
        """
        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 2):
            try:
                state = await agent.run(state)
                return True
            except AgentExecutionError as exc:
                last_error = exc
                logger.warning(
                    "Agent '%s' attempt %d/%d failed — %s",
                    agent.name,
                    attempt,
                    self.max_retries + 1,
                    exc,
                )
                state.log_entry(
                    agent_name=agent.name,
                    status="retried" if attempt <= self.max_retries else "failed",
                    message=f"Attempt {attempt}/{self.max_retries + 1}",
                    error=str(exc),
                )

        logger.error(
            "Agent '%s' exhausted all %d retry attempts.",
            agent.name,
            self.max_retries + 1,
        )
        return False
