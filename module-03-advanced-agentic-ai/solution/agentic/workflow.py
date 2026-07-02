"""Explicit LangGraph orchestration for UDA-Hub support tickets.

Lane A owns classification and routing. Resolver and escalation nodes are
injected so their tools and persistence can be implemented independently.

    START -> classifier -> resolver -> END
                    |          |
                    +----------+-> escalation -> END
"""

from collections.abc import Callable
from functools import partial
from typing import Any, Literal

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.store.base import BaseStore

from agentic.agents.classifier import (
    ClassifierRunnable,
    build_classifier,
    classify_ticket,
)
from agentic.state import (
    Route,
    SupportState,
    TicketCategory,
    TicketClassification,
)


CLASSIFICATION_CONFIDENCE_THRESHOLD = 0.75
RESOLUTION_CONFIDENCE_THRESHOLD = 0.70
HIGH_RISK_TAGS = frozenset(
    {
        "security",
        "fraud",
        "payment-dispute",
        "disputed-payment",
        "human-requested",
    }
)

WorkflowNode = Callable[[SupportState], dict[str, Any]]


def route_after_classification(
    state: SupportState,
) -> Literal["resolver", "escalation"]:
    """Route a validated classification using deterministic safety rules."""

    raw_classification = state.get("classification")
    if raw_classification is None or state.get("error"):
        return "escalation"

    try:
        classification = TicketClassification.model_validate(raw_classification)
    except (TypeError, ValueError):
        return "escalation"

    normalized_tags = {tag.strip().lower() for tag in classification.tags}
    if (
        classification.route == Route.ESCALATION
        or classification.category == TicketCategory.OTHER
        or classification.confidence < CLASSIFICATION_CONFIDENCE_THRESHOLD
        or bool(normalized_tags & HIGH_RISK_TAGS)
    ):
        return "escalation"

    return "resolver"


def route_after_resolution(
    state: SupportState,
) -> Literal["escalation", "__end__"]:
    """Finish only confident, successful resolutions that need no approval."""

    if state.get("error"):
        return "escalation"
    if state.get("action_required") and state.get("action_approved") is not True:
        return "escalation"
    if not state.get("resolution"):
        return "escalation"
    if state.get("resolution_confidence", 0.0) < RESOLUTION_CONFIDENCE_THRESHOLD:
        return "escalation"
    return END


def build_orchestrator(
    *,
    model: BaseChatModel | None = None,
    classifier: ClassifierRunnable | None = None,
    resolver_node: WorkflowNode | None = None,
    escalation_node: WorkflowNode | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
    store: BaseStore | None = None,
) -> CompiledStateGraph:
    """Build the UDA-Hub graph from explicit, replaceable components.

    Resolver and escalation behavior must be supplied by Lane B. Requiring
    these nodes prevents a graph that compiles but silently performs fake
    production work.
    """

    if resolver_node is None:
        raise ValueError("resolver_node is required until Lane B is implemented")
    if escalation_node is None:
        raise ValueError("escalation_node is required until Lane B is implemented")

    if classifier is None:
        selected_model = model or ChatOpenAI(model="gpt-4o-mini")
        classifier = build_classifier(selected_model)

    builder = StateGraph(SupportState)
    builder.add_node(
        "classifier",
        partial(classify_ticket, classifier=classifier),
    )
    builder.add_node("resolver", resolver_node)
    builder.add_node("escalation", escalation_node)

    builder.add_edge(START, "classifier")
    builder.add_conditional_edges(
        "classifier",
        route_after_classification,
        {"resolver": "resolver", "escalation": "escalation"},
    )
    builder.add_conditional_edges(
        "resolver",
        route_after_resolution,
        {"escalation": "escalation", END: END},
    )
    builder.add_edge("escalation", END)

    return builder.compile(
        checkpointer=checkpointer or InMemorySaver(),
        store=store,
    )


__all__ = [
    "build_orchestrator",
    "route_after_classification",
    "route_after_resolution",
]
