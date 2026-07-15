"""
Centralized configuration module for the FraudShield multi-agent system.

Provides a single source of truth for all configurable constants
used across agents, LLM integrations, and service orchestration.
"""

from pathlib import Path


# ---------------------------------------------------------------------------
# LLM Configuration
# ---------------------------------------------------------------------------

LLM_PROVIDER: str = "openai"
"""Identifier for the LLM provider backend (e.g. 'openai', 'anthropic', 'ollama')."""

LLM_MODEL: str = "gpt-4o"
"""Model identifier used for all LLM completions."""

TEMPERATURE: float = 0.3
"""Sampling temperature for LLM responses. Lower values are more deterministic."""

MAX_TOKENS: int = 4096
"""Maximum number of tokens in a single LLM completion."""

LLM_REQUEST_TIMEOUT: int = 60
"""Timeout in seconds for a single LLM API call."""

LLM_MAX_RETRIES: int = 3
"""Number of retry attempts for transient LLM API failures."""

# ---------------------------------------------------------------------------
# Report Configuration
# ---------------------------------------------------------------------------

REPORT_OUTPUT_DIR: Path = Path("storage/reports")
"""Directory where generated PDF reports are persisted."""

# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------

LOG_LEVEL: str = "INFO"
"""Root logging level for the entire agent framework."""

LOG_FORMAT: str = "%(asctime)s | %(name)-28s | %(levelname)-8s | %(message)s"
"""Default log line format."""

# ---------------------------------------------------------------------------
# Pipeline Configuration
# ---------------------------------------------------------------------------

PIPELINE_DB_PATH: Path = Path("storage/fraudshield.db")
"""Path to the SQLite investigation database."""

PIPELINE_MODEL_DIR: Path = Path("ml/models")
"""Directory containing serialized ML model artifacts."""

# ---------------------------------------------------------------------------
# Agent Orchestration Configuration
# ---------------------------------------------------------------------------

AGENT_EXECUTION_TIMEOUT: int = 120
"""Maximum seconds a single agent may run before being terminated."""

MAX_AGENT_RETRIES: int = 2
"""Number of times a failed agent step may be retried by the supervisor."""

ENABLE_TRACING: bool = True
"""When True, the supervisor records detailed execution traces."""

# ---------------------------------------------------------------------------
# API Configuration
# ---------------------------------------------------------------------------

API_HOST: str = "0.0.0.0"
"""Bind address for the FastAPI server."""

API_PORT: int = 8000
"""Port for the FastAPI server."""

CORS_ORIGINS: list[str] = ["http://localhost:3000"]
"""Allowed CORS origins for the API."""
