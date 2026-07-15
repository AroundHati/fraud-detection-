"""
Shared data schemas for the FraudShield multi-agent system.

Contains Pydantic models and dataclasses that define the shape of
data flowing between agents, services, and API endpoints.
"""

from ml.schemas.agent_state import AgentState
from ml.schemas.investigation import InvestigationSummary, ProviderFinding, Recommendation
from ml.schemas.messages import AgentMessage, AgentRole, MessageType
from ml.schemas.report import ReportContent, ReportMetadata
from ml.schemas.risk import (
    FraudIndicator,
    InvestigationPriority,
    ProviderRisk,
    RiskAssessment,
    RiskLevel,
)

__all__ = [
    "AgentState",
    "AgentMessage",
    "AgentRole",
    "FraudIndicator",
    "InvestigationPriority",
    "MessageType",
    "InvestigationSummary",
    "ProviderFinding",
    "ProviderRisk",
    "Recommendation",
    "ReportContent",
    "ReportMetadata",
    "RiskAssessment",
    "RiskLevel",
]
