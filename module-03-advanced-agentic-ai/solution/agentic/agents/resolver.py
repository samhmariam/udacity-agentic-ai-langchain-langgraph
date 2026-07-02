"""Grounded ticket-resolution agent and graph node."""

from __future__ import annotations

from typing import Any, Literal, Protocol

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import BaseTool
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, Field, model_validator

from agentic.state import SupportState, TicketClassification, TicketStatus
from agentic.tools.agent_tools import build_resolver_tools
from agentic.tools.database import CoreRepository, ExternalRepository
from agentic.tools.knowledge import KnowledgeRetriever


RESOLVER_PROMPT = """You are UDA-Hub's customer-support resolver.

Resolve only supported, low-risk requests. Use tools to inspect customer facts
and retrieve approved knowledge. Policy claims must be grounded in retrieved
articles; list the article IDs in sources. Never invent account, reservation,
payment, venue, or policy data.

You may propose cancellation of an owned reservation, but you cannot approve or
execute it. Set action to cancel_reservation and provide its reservation ID.
Refunds, disputed payments, security incidents, unavailable facts, and requests
outside the tools must be returned with confidence below 0.70 so a human can
handle them. Keep the customer response concise and actionable.
"""


class ResolutionDecision(BaseModel):
    response: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    sources: list[str] = Field(default_factory=list)
    action: Literal["none", "cancel_reservation"] = "none"
    reservation_id: str | None = None
    action_reason: str | None = None

    @model_validator(mode="after")
    def validate_action(self) -> "ResolutionDecision":
        if self.action == "cancel_reservation" and not self.reservation_id:
            raise ValueError("reservation_id is required for cancellation")
        return self


class ResolverRunnable(Protocol):
    def invoke(self, input: dict[str, Any]) -> dict[str, Any]: ...


def build_resolver(
    model: BaseChatModel,
    tools: list[BaseTool],
) -> CompiledStateGraph:
    return create_agent(
        model=model,
        tools=tools,
        system_prompt=RESOLVER_PROMPT,
        response_format=ResolutionDecision,
        name="ticket_resolver",
    )


def _latest_customer_text(state: SupportState) -> str:
    for message in reversed(state.get("messages", [])):
        if isinstance(message, HumanMessage) and message.text.strip():
            return message.text.strip()
    raise ValueError("Ticket contains no customer message")


def resolve_ticket(
    state: SupportState,
    *,
    model: BaseChatModel | None = None,
    resolver: ResolverRunnable | None = None,
    core_repository: CoreRepository,
    external_repository: ExternalRepository,
    knowledge_retriever: KnowledgeRetriever,
) -> dict[str, Any]:
    """Resolve a ticket, execute pre-approved actions, and persist the outcome."""

    try:
        classification = TicketClassification.model_validate(state["classification"])
        account_id = state.get("account_id") or "cultpass"
        if resolver is None:
            if model is None:
                raise ValueError("model is required when resolver is not supplied")
            resolver = build_resolver(
                model,
                build_resolver_tools(
                    account_id=account_id,
                    external_user_id=state.get("external_user_id"),
                    core_repository=core_repository,
                    external_repository=external_repository,
                    knowledge_retriever=knowledge_retriever,
                ),
            )

        request = {
            "ticket": _latest_customer_text(state),
            "ticket_id": state.get("ticket_id"),
            "account_id": account_id,
            "external_user_id": state.get("external_user_id"),
            "channel": state.get("channel"),
            "classification": classification.model_dump(mode="json"),
        }
        result = resolver.invoke(
            {"messages": [HumanMessage(content=f"Resolve this ticket:\n{request!r}")]}
        )
        decision = ResolutionDecision.model_validate(result["structured_response"])

        action_required = decision.action != "none"
        action_approved = state.get("action_approved") if action_required else None
        action_result = None
        if decision.action == "cancel_reservation" and action_approved is True:
            external_user_id = state.get("external_user_id")
            if not external_user_id:
                raise ValueError("Cannot cancel without an external_user_id")
            action_result = external_repository.cancel_reservation(
                reservation_id=decision.reservation_id or "",
                external_user_id=external_user_id,
                approved=True,
            )

        response = decision.response
        if action_result:
            response = f"{response}\n\nAction result: {action_result}"

        if state.get("ticket_id") and (
            not action_required or action_approved is True
        ):
            core_repository.save_outcome(
                ticket_id=state["ticket_id"],
                content=response,
                status=TicketStatus.RESOLVED.value,
                issue_type=classification.category.value,
                tags=classification.tags,
            )

        return {
            "messages": [AIMessage(content=response)],
            "resolution": response,
            "resolution_confidence": decision.confidence,
            "sources": decision.sources,
            "proposed_action": decision.action,
            "proposed_action_id": decision.reservation_id,
            "action_required": action_required,
            "action_result": action_result,
            "status": (
                TicketStatus.AWAITING_APPROVAL.value
                if action_required and action_approved is not True
                else TicketStatus.RESOLVED.value
            ),
            "error": None,
        }
    except Exception as exc:
        return {
            "resolution_confidence": 0.0,
            "status": TicketStatus.FAILED.value,
            "error": f"Resolver failed: {type(exc).__name__}: {exc}",
        }
