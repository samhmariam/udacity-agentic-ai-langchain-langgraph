"""API-key-free tests for Lane A classification and routing."""

import unittest

from langchain_core.messages import AIMessage, HumanMessage
from pydantic import ValidationError

from agentic.agents.classifier import classify_ticket
from agentic.state import (
    Route,
    TicketCategory,
    TicketClassification,
    TicketStatus,
    Urgency,
)
from agentic.workflow import (
    build_orchestrator,
    route_after_classification,
    route_after_resolution,
)


def make_classification(
    *,
    category: TicketCategory = TicketCategory.ACCOUNT_ACCESS,
    confidence: float = 0.9,
    route: Route = Route.RESOLVER,
    tags: list[str] | None = None,
) -> TicketClassification:
    return TicketClassification(
        category=category,
        urgency=Urgency.MEDIUM,
        confidence=confidence,
        tags=tags or ["login"],
        route=route,
        rationale="The request clearly matches the selected category.",
    )


class FakeClassifier:
    def __init__(self, response):
        self.response = response
        self.inputs = []

    def invoke(self, input):
        self.inputs.append(input)
        return self.response


class TestTicketClassification(unittest.TestCase):
    def test_accepts_valid_structured_classification(self):
        classification = make_classification(confidence=1.0)

        self.assertEqual(classification.category, TicketCategory.ACCOUNT_ACCESS)
        self.assertEqual(classification.confidence, 1.0)

    def test_rejects_confidence_outside_zero_to_one(self):
        for confidence in (-0.01, 1.01):
            with self.subTest(confidence=confidence):
                with self.assertRaises(ValidationError):
                    make_classification(confidence=confidence)

    def test_all_categories_are_valid(self):
        for category in TicketCategory:
            with self.subTest(category=category):
                self.assertEqual(
                    make_classification(category=category).category,
                    category,
                )


class TestClassifierNode(unittest.TestCase):
    def test_copies_validated_structured_response_into_state(self):
        expected = make_classification()
        classifier = FakeClassifier({"structured_response": expected.model_dump()})

        update = classify_ticket(
            {
                "messages": [HumanMessage(content="I cannot log in")],
                "channel": "chat",
            },
            classifier=classifier,
        )

        self.assertEqual(TicketClassification.model_validate(update["classification"]), expected)
        self.assertEqual(update["status"], TicketStatus.IN_PROGRESS.value)
        self.assertIsNone(update["error"])
        request_text = classifier.inputs[0]["messages"][0].content
        self.assertIn("I cannot log in", request_text)
        self.assertIn("'channel': 'chat'", request_text)

    def test_missing_customer_text_becomes_valid_escalation(self):
        classifier = FakeClassifier({"structured_response": make_classification()})

        update = classify_ticket({"messages": []}, classifier=classifier)

        classification = TicketClassification.model_validate(update["classification"])
        self.assertEqual(classification.route, Route.ESCALATION)
        self.assertEqual(classification.confidence, 0.0)
        self.assertEqual(update["status"], TicketStatus.FAILED.value)
        self.assertIn("no non-empty customer message", update["error"])
        self.assertEqual(classifier.inputs, [])

    def test_malformed_classifier_output_becomes_valid_escalation(self):
        classifier = FakeClassifier(
            {
                "structured_response": {
                    "category": "not-a-category",
                    "confidence": 3,
                }
            }
        )

        update = classify_ticket(
            {"messages": [HumanMessage(content="Help")]},
            classifier=classifier,
        )

        classification = TicketClassification.model_validate(update["classification"])
        self.assertEqual(classification.route, Route.ESCALATION)
        self.assertEqual(classification.category, TicketCategory.OTHER)
        self.assertIn("invalid response", update["error"])


class TestRouting(unittest.TestCase):
    def test_confidence_boundary(self):
        expected = {
            0.74: "escalation",
            0.75: "resolver",
            1.0: "resolver",
        }
        for confidence, route in expected.items():
            with self.subTest(confidence=confidence):
                state = {
                    "classification": make_classification(
                        confidence=confidence
                    ).model_dump(mode="json")
                }
                self.assertEqual(route_after_classification(state), route)

    def test_classifier_selected_escalation_wins(self):
        state = {
            "classification": make_classification(
                confidence=1.0,
                route=Route.ESCALATION,
            ).model_dump(mode="json")
        }
        self.assertEqual(route_after_classification(state), "escalation")

    def test_other_category_is_always_escalated(self):
        state = {
            "classification": make_classification(
                category=TicketCategory.OTHER,
                confidence=1.0,
            ).model_dump(mode="json")
        }
        self.assertEqual(route_after_classification(state), "escalation")

    def test_high_risk_tag_is_always_escalated(self):
        state = {
            "classification": make_classification(
                confidence=1.0,
                tags=["payment-dispute"],
            ).model_dump(mode="json")
        }
        self.assertEqual(route_after_classification(state), "escalation")

    def test_supported_categories_reach_resolver(self):
        supported = set(TicketCategory) - {TicketCategory.OTHER}
        for category in supported:
            with self.subTest(category=category):
                state = {
                    "classification": make_classification(
                        category=category,
                        confidence=0.9,
                        tags=[category.value],
                    ).model_dump(mode="json")
                }
                self.assertEqual(route_after_classification(state), "resolver")

    def test_resolution_routes_cover_success_failure_and_action(self):
        cases = [
            ({"resolution": "Done", "resolution_confidence": 0.70}, "__end__"),
            ({"resolution": "Unsure", "resolution_confidence": 0.69}, "escalation"),
            ({"resolution_confidence": 1.0}, "escalation"),
            ({"resolution": "Done", "resolution_confidence": 1.0, "error": "db"}, "escalation"),
            (
                {
                    "resolution": "Ready",
                    "resolution_confidence": 1.0,
                    "action_required": True,
                    "action_approved": False,
                },
                "escalation",
            ),
            (
                {
                    "resolution": "Executed",
                    "resolution_confidence": 1.0,
                    "action_required": True,
                    "action_approved": True,
                },
                "__end__",
            ),
        ]
        for state, expected in cases:
            with self.subTest(state=state):
                self.assertEqual(route_after_resolution(state), expected)


class TestWorkflow(unittest.TestCase):
    @staticmethod
    def resolver_node(state):
        return {
            "messages": [AIMessage(content="Resolved")],
            "resolution": "Resolved",
            "resolution_confidence": 0.95,
            "status": TicketStatus.RESOLVED.value,
        }

    @staticmethod
    def escalation_node(state):
        return {
            "messages": [AIMessage(content="Escalated")],
            "escalation_reason": state.get("error") or "Specialist review required",
            "status": TicketStatus.ESCALATED.value,
        }

    def test_requires_lane_b_nodes(self):
        classifier = FakeClassifier({"structured_response": make_classification()})
        with self.assertRaisesRegex(ValueError, "resolver_node"):
            build_orchestrator(classifier=classifier)
        with self.assertRaisesRegex(ValueError, "escalation_node"):
            build_orchestrator(
                classifier=classifier,
                resolver_node=self.resolver_node,
            )

    def test_graph_resolves_supported_ticket(self):
        classifier = FakeClassifier({"structured_response": make_classification()})
        graph = build_orchestrator(
            classifier=classifier,
            resolver_node=self.resolver_node,
            escalation_node=self.escalation_node,
        )

        result = graph.invoke(
            {"messages": [HumanMessage(content="I cannot log in")]},
            {"configurable": {"thread_id": "resolve-1"}},
        )

        self.assertEqual(result["status"], TicketStatus.RESOLVED.value)
        self.assertEqual(result["resolution"], "Resolved")

    def test_graph_escalates_low_confidence_ticket(self):
        classifier = FakeClassifier(
            {"structured_response": make_classification(confidence=0.74)}
        )
        graph = build_orchestrator(
            classifier=classifier,
            resolver_node=self.resolver_node,
            escalation_node=self.escalation_node,
        )

        result = graph.invoke(
            {"messages": [HumanMessage(content="Something is wrong")]},
            {"configurable": {"thread_id": "escalate-1"}},
        )

        self.assertEqual(result["status"], TicketStatus.ESCALATED.value)
        self.assertNotIn("resolution", result)

    def test_checkpoint_restores_messages_for_same_thread(self):
        classifier = FakeClassifier({"structured_response": make_classification()})
        graph = build_orchestrator(
            classifier=classifier,
            resolver_node=self.resolver_node,
            escalation_node=self.escalation_node,
        )
        config = {"configurable": {"thread_id": "conversation-1"}}

        graph.invoke({"messages": [HumanMessage(content="First")]}, config)
        result = graph.invoke({"messages": [HumanMessage(content="Second")]}, config)

        contents = [message.content for message in result["messages"]]
        self.assertEqual(contents, ["First", "Resolved", "Second", "Resolved"])


if __name__ == "__main__":
    unittest.main()
