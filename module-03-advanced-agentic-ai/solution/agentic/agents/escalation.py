"""Human-escalation agent and persistence node."""

from __future__ import annotations

from typing import Any, Protocol

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, Field

from agentic.state import SupportState, TicketClassification, TicketStatus
from agentic.tools.database import CoreRepository


ESCALATION_PROMPT = """You prepare safe customer-support escalations.

Write a calm customer-facing message explaining that specialist review is
needed. Also create a concise internal summary containing the issue, urgency,
classification, attempts made, errors, proposed actions, and the recommended
next step. Do not claim that an action, refund, or fix occurred when it did not.
"""


class EscalationDecision(BaseModel):
    customer_message: str = Field(min_length=1)
    internal_summary: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    recommended_action: str = Field(min_length=1)


class EscalationRunnable(Protocol):
    def invoke(self, input: dict[str, Any]) -> dict[str, Any]: ...


def build_escalation_agent(model: BaseChatModel) -> CompiledStateGraph:
    return create_agent(
        model=model,
        tools=[],
        system_prompt=ESCALATION_PROMPT,
        response_format=EscalationDecision,
        name="ticket_escalation",
    )


def escalate_ticket(
    state: SupportState,
    *,
    escalation_agent: EscalationRunnable,
    core_repository: CoreRepository,
) -> dict[str, Any]:
    """Create and persist a human-readable specialist handoff."""

    raw_classification = state.get("classification")
    classification = None
    if raw_classification:
        try:
            classification = TicketClassification.model_validate(raw_classification)
        except ValueError:
            classification = None

    context = {
        "ticket_id": state.get("ticket_id"),
        "account_id": state.get("account_id"),
        "external_user_id": state.get("external_user_id"),
        "classification": classification.model_dump(mode="json")
        if classification
        else None,
        "resolver_response": state.get("resolution"),
        "resolver_confidence": state.get("resolution_confidence"),
        "proposed_action": state.get("proposed_action"),
        "error": state.get("error"),
    }

    try:
        result = escalation_agent.invoke(
            {
                "messages": [
                    HumanMessage(content=f"Prepare an escalation:\n{context!r}")
                ]
            }
        )
        decision = EscalationDecision.model_validate(result["structured_response"])

        if state.get("ticket_id"):
            core_repository.save_outcome(
                ticket_id=state["ticket_id"],
                content=decision.customer_message,
                status=TicketStatus.ESCALATED.value,
                issue_type=classification.category.value if classification else None,
                tags=classification.tags if classification else None,
            )

        return {
            "messages": [AIMessage(content=decision.customer_message)],
            "escalation_reason": decision.reason,
            "internal_summary": decision.internal_summary,
            "recommended_action": decision.recommended_action,
            "status": TicketStatus.ESCALATED.value,
            "error": state.get("error"),
        }
    except Exception as exc:
        fallback = (
            "I’m unable to complete this request automatically. "
            "A support specialist needs to review it."
        )
        return {
            "messages": [AIMessage(content=fallback)],
            "escalation_reason": f"Escalation failed: {type(exc).__name__}: {exc}",
            "internal_summary": repr(context),
            "recommended_action": "Review the ticket and contact the customer.",
            "status": TicketStatus.FAILED.value,
            "error": f"Escalation failed: {type(exc).__name__}: {exc}",
        }
