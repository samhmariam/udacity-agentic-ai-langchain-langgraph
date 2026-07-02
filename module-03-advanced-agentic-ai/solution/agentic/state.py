"""Shared state and structured outputs for the UDA-Hub workflow."""

from enum import StrEnum
from typing import Any

from langgraph.graph import MessagesState
from pydantic import BaseModel, Field
from typing_extensions import NotRequired


class TicketCategory(StrEnum):
    """Supported customer-support issue categories."""

    ACCOUNT_ACCESS = "account_access"
    SUBSCRIPTION = "subscription"
    RESERVATION = "reservation"
    BILLING_REFUND = "billing_refund"
    EVENT_INFORMATION = "event_information"
    ACCESSIBILITY = "accessibility"
    OTHER = "other"


class Urgency(StrEnum):
    """Operational urgency assigned during ticket classification."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Route(StrEnum):
    """Next specialist selected by the classifier."""

    RESOLVER = "resolver"
    ESCALATION = "escalation"


class TicketStatus(StrEnum):
    """Lifecycle status of a ticket while the workflow is running."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    AWAITING_APPROVAL = "awaiting_approval"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    FAILED = "failed"


class TicketClassification(BaseModel):
    """Validated decision returned by the classifier agent."""

    category: TicketCategory
    urgency: Urgency
    confidence: float = Field(ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    route: Route
    rationale: str = Field(min_length=1)


class SupportState(MessagesState):
    """State shared by all nodes in the UDA-Hub support graph."""

    ticket_id: NotRequired[str]
    account_id: NotRequired[str]
    external_user_id: NotRequired[str]
    channel: NotRequired[str]
    supplied_urgency: NotRequired[str]
    ticket_metadata: NotRequired[dict[str, Any]]

    # Store structured output as JSON primitives so checkpoints remain portable.
    # Nodes validate this dictionary with TicketClassification before using it.
    classification: NotRequired[dict[str, Any]]
    resolution: NotRequired[str]
    resolution_confidence: NotRequired[float]
    sources: NotRequired[list[str]]
    escalation_reason: NotRequired[str]
    internal_summary: NotRequired[str]
    recommended_action: NotRequired[str]

    action_required: NotRequired[bool]
    action_approved: NotRequired[bool | None]
    proposed_action: NotRequired[str]
    proposed_action_id: NotRequired[str | None]
    action_result: NotRequired[dict[str, Any] | None]
    status: NotRequired[str]
    error: NotRequired[str | None]
