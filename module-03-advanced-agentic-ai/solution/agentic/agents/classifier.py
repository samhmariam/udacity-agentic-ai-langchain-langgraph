"""Ticket-classification agent and its LangGraph node adapter."""

from typing import Any, Protocol

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.graph.state import CompiledStateGraph

from agentic.state import (
    Route,
    SupportState,
    TicketCategory,
    TicketClassification,
    TicketStatus,
    Urgency,
)


CLASSIFIER_PROMPT = """You are UDA-Hub's ticket classifier.

Classify the latest customer request using only the supplied ticket text and
metadata. Do not answer or resolve the request.

Categories:
- account_access: login, password, blocked account, or authentication issues
- subscription: plan, quota, pause, cancellation, or membership questions
- reservation: booking, cancellation, availability, or QR-code issues
- billing_refund: charges, billing, payment, or refund questions
- event_information: venue, schedule, entry, or experience details
- accessibility: accommodation or accessibility needs
- other: unsupported or unclear requests

Routing rules:
- Route clear, supported, low-risk requests to resolver.
- Route security incidents, suspected fraud, disputed payments, threats,
  requests for a human, unsupported requests, and ambiguous requests to
  escalation.
- Use confidence below 0.75 whenever important context is missing or the
  classification is materially ambiguous.
- Treat user-supplied urgency as a signal, not as unquestioned truth.
- Keep tags short, lowercase, and operationally useful.
"""


class ClassifierRunnable(Protocol):
    """Minimal interface needed by the classifier graph node."""

    def invoke(self, input: dict[str, Any]) -> dict[str, Any]: ...


def build_classifier(model: BaseChatModel) -> CompiledStateGraph:
    """Build the structured-output ticket classifier."""

    return create_agent(
        model=model,
        tools=[],
        system_prompt=CLASSIFIER_PROMPT,
        response_format=TicketClassification,
        name="ticket_classifier",
    )


def _latest_customer_text(state: SupportState) -> str | None:
    for message in reversed(state.get("messages", [])):
        if isinstance(message, HumanMessage):
            text = message.text.strip()
            if text:
                return text
    return None


def _fallback_classification(reason: str) -> TicketClassification:
    return TicketClassification(
        category=TicketCategory.OTHER,
        urgency=Urgency.HIGH,
        confidence=0.0,
        tags=["classification-failed"],
        route=Route.ESCALATION,
        rationale=reason,
    )


def classify_ticket(
    state: SupportState,
    *,
    classifier: ClassifierRunnable,
) -> dict[str, Any]:
    """Classify the latest customer message and return a validated state update."""

    ticket_text = _latest_customer_text(state)
    if ticket_text is None:
        reason = "Ticket contains no non-empty customer message."
        return {
            "classification": _fallback_classification(reason).model_dump(mode="json"),
            "status": TicketStatus.FAILED.value,
            "error": reason,
        }

    metadata = {
        "ticket_id": state.get("ticket_id"),
        "account_id": state.get("account_id"),
        "external_user_id": state.get("external_user_id"),
        "channel": state.get("channel"),
        "supplied_urgency": state.get("supplied_urgency"),
        **state.get("ticket_metadata", {}),
    }
    request = (
        f"Ticket text:\n{ticket_text}\n\n"
        f"Ticket metadata:\n{metadata!r}"
    )

    try:
        result = classifier.invoke({"messages": [HumanMessage(content=request)]})
        classification = TicketClassification.model_validate(
            result["structured_response"]
        )
    except (KeyError, TypeError, ValueError) as exc:
        reason = f"Classifier returned an invalid response: {exc}"
        return {
            "classification": _fallback_classification(reason).model_dump(mode="json"),
            "status": TicketStatus.FAILED.value,
            "error": reason,
        }
    except Exception as exc:  # The model/provider boundary can raise many error types.
        reason = f"Classifier failed: {type(exc).__name__}: {exc}"
        return {
            "classification": _fallback_classification(reason).model_dump(mode="json"),
            "status": TicketStatus.FAILED.value,
            "error": reason,
        }

    return {
        "classification": classification.model_dump(mode="json"),
        "status": TicketStatus.IN_PROGRESS.value,
        "error": None,
    }
