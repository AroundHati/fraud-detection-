"""
Message schemas for inter-agent communication in the FraudShield system.

Defines the structured messages that agents exchange via the supervisor,
including role identifiers, message types, and the message envelope.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    """Enumerates the roles an agent can assume in the system."""

    SUPERVISOR = "supervisor"
    RISK = "risk"
    INVESTIGATION = "investigation"
    REPORT = "report"
    SYSTEM = "system"


class MessageType(str, Enum):
    """Classification of messages exchanged between agents."""

    COMMAND = "command"
    """Instruction from the supervisor to execute a task."""

    RESPONSE = "response"
    """Result returned by an agent after execution."""

    QUERY = "query"
    """Information request from one agent to another."""

    ERROR = "error"
    """Error notification propagated through the pipeline."""

    HEARTBEAT = "heartbeat"
    """Periodic liveness signal from an agent."""


class AgentMessage(BaseModel):
    """Envelope for all inter-agent communication.

    Every message carries a sender, recipient, type, and an arbitrary
    payload.  The ``conversation_id`` field allows messages to be
    grouped into logical request/response chains.

    Attributes:
        message_id: Globally unique identifier for this message.
        conversation_id: Groups messages belonging to the same exchange.
        sender: Role of the originating agent.
        recipient: Role of the intended recipient agent.
        message_type: Classification of the message.
        payload: Arbitrary data carried by the message.
        timestamp: When the message was created.
        in_reply_to: Optional ID of the message being replied to.
        metadata: Arbitrary metadata for extensibility.
    """

    message_id: str = Field(
        ...,
        description="Globally unique message identifier.",
    )
    conversation_id: str = Field(
        ...,
        description="Groups messages belonging to the same exchange.",
    )
    sender: AgentRole = Field(
        ...,
        description="Role of the agent that sent this message.",
    )
    recipient: AgentRole = Field(
        ...,
        description="Role of the intended recipient agent.",
    )
    message_type: MessageType = Field(
        ...,
        description="Classification of the message.",
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary data carried by the message.",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the message was created.",
    )
    in_reply_to: Optional[str] = Field(
        default=None,
        description="ID of the message this message replies to.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary metadata for extensibility.",
    )
