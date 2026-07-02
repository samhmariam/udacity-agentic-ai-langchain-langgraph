"""Offline integration tests for Lane B tools and specialist nodes."""

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from langchain_core.embeddings import Embeddings
from langchain_core.messages import HumanMessage
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from agentic.agents.escalation import escalate_ticket
from agentic.agents.resolver import resolve_ticket
from agentic.state import Route, TicketCategory, TicketClassification, Urgency
from agentic.tools.agent_tools import build_resolver_tools
from agentic.tools.database import CoreRepository, ExternalRepository
from agentic.tools.knowledge import SemanticKnowledgeBase
from data.models import cultpass, udahub


class FakeEmbeddings(Embeddings):
    @staticmethod
    def _embed(text: str) -> list[float]:
        normalized = text.lower()
        return [
            float(normalized.count("login") + 1),
            float(normalized.count("event") + 1),
            float(normalized.count("subscription") + 1),
        ]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


class FakeRetriever:
    def search(self, account_id: str, query: str, limit: int = 3):
        return [
            {
                "article_id": "article-login",
                "account_id": account_id,
                "title": "Login help",
                "content": "Use password reset.",
                "score": 1.0,
            }
        ][:limit]


class FakeAgent:
    def __init__(self, structured_response):
        self.structured_response = structured_response

    def invoke(self, input):
        return {"structured_response": self.structured_response}


class LaneBTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.core_path = root / "core.db"
        self.external_path = root / "external.db"
        self._seed_core()
        self._seed_external()
        self.core = CoreRepository(self.core_path)
        self.external = ExternalRepository(self.external_path)

    def tearDown(self):
        self.core.close()
        self.external.close()
        self.temp_dir.cleanup()

    def _seed_core(self):
        engine = create_engine(f"sqlite:///{self.core_path}")
        udahub.Base.metadata.create_all(engine)
        sessions = sessionmaker(bind=engine)
        with sessions.begin() as session:
            session.add_all(
                [
                    udahub.Account(account_id="cultpass", account_name="CultPass"),
                    udahub.Account(account_id="other", account_name="Other"),
                    udahub.User(
                        user_id="core-user-1",
                        account_id="cultpass",
                        external_user_id="user-1",
                        user_name="Sam",
                    ),
                    udahub.Ticket(
                        ticket_id="ticket-1",
                        account_id="cultpass",
                        user_id="core-user-1",
                        channel="chat",
                    ),
                    udahub.TicketMetadata(
                        ticket_id="ticket-1",
                        status="open",
                        tags="login",
                    ),
                    udahub.TicketMessage(
                        message_id="message-1",
                        ticket_id="ticket-1",
                        role=udahub.RoleEnum.user,
                        content="I cannot log in",
                    ),
                    udahub.Knowledge(
                        article_id="article-login",
                        account_id="cultpass",
                        title="Login help",
                        content="Use password reset.",
                        tags="login,password",
                    ),
                    udahub.Knowledge(
                        article_id="article-other",
                        account_id="other",
                        title="Other tenant article",
                        content="This must not leak.",
                        tags="private",
                    ),
                ]
            )
        engine.dispose()

    def _seed_external(self):
        engine = create_engine(f"sqlite:///{self.external_path}")
        cultpass.Base.metadata.create_all(engine)
        sessions = sessionmaker(bind=engine)
        with sessions.begin() as session:
            session.add_all(
                [
                    cultpass.User(
                        user_id="user-1",
                        full_name="Sam",
                        email="sam@example.com",
                    ),
                    cultpass.User(
                        user_id="user-2",
                        full_name="Alex",
                        email="alex@example.com",
                    ),
                    cultpass.Subscription(
                        subscription_id="subscription-1",
                        user_id="user-1",
                        status="active",
                        tier="basic",
                        monthly_quota=4,
                    ),
                    cultpass.Experience(
                        experience_id="experience-1",
                        title="Museum visit",
                        description="A museum visit",
                        location="London",
                        when=datetime(2026, 8, 1, 10, 0),
                        slots_available=5,
                        is_premium=False,
                    ),
                    cultpass.Reservation(
                        reservation_id="reservation-1",
                        user_id="user-1",
                        experience_id="experience-1",
                        status="reserved",
                    ),
                ]
            )
        engine.dispose()

    @staticmethod
    def classification():
        return TicketClassification(
            category=TicketCategory.ACCOUNT_ACCESS,
            urgency=Urgency.MEDIUM,
            confidence=0.95,
            tags=["login"],
            route=Route.RESOLVER,
            rationale="Login issue",
        ).model_dump(mode="json")


class TestRepositories(LaneBTestCase):
    def test_reads_ticket_and_customer_context(self):
        ticket = self.core.get_ticket_context("ticket-1")
        customer = self.external.get_customer_context("user-1")

        self.assertEqual(ticket["user"]["external_user_id"], "user-1")
        self.assertEqual(ticket["messages"][0]["content"], "I cannot log in")
        self.assertEqual(customer["subscription"]["status"], "active")
        self.assertEqual(customer["reservations"][0]["reservation_id"], "reservation-1")

    def test_save_outcome_is_atomic_and_updates_metadata(self):
        self.core.save_outcome(
            ticket_id="ticket-1",
            content="Use password reset.",
            status="resolved",
            issue_type="account_access",
            tags=["login", "password"],
        )

        ticket = self.core.get_ticket_context("ticket-1")
        self.assertEqual(ticket["status"], "resolved")
        self.assertEqual(ticket["issue_type"], "account_access")
        self.assertEqual(ticket["messages"][-1]["role"], "ai")

    def test_cancellation_requires_approval_and_is_idempotent(self):
        proposal = self.external.propose_reservation_cancellation(
            reservation_id="reservation-1",
            external_user_id="user-1",
        )
        self.assertTrue(proposal["eligible"])

        with self.assertRaises(PermissionError):
            self.external.cancel_reservation(
                reservation_id="reservation-1",
                external_user_id="user-1",
                approved=False,
            )

        first = self.external.cancel_reservation(
            reservation_id="reservation-1",
            external_user_id="user-1",
            approved=True,
        )
        second = self.external.cancel_reservation(
            reservation_id="reservation-1",
            external_user_id="user-1",
            approved=True,
        )
        self.assertTrue(first["changed"])
        self.assertFalse(second["changed"])

    def test_cannot_access_another_customers_reservation(self):
        with self.assertRaises(LookupError):
            self.external.propose_reservation_cancellation(
                reservation_id="reservation-1",
                external_user_id="user-2",
            )


class TestKnowledgeAndTools(LaneBTestCase):
    def test_semantic_search_is_account_scoped(self):
        knowledge = SemanticKnowledgeBase(
            self.core_path,
            embeddings=FakeEmbeddings(),
        )

        results = knowledge.search("cultpass", "login problem", limit=3)

        self.assertEqual([item["article_id"] for item in results], ["article-login"])

    def test_bound_ticket_tool_rejects_cross_tenant_ticket(self):
        tools = build_resolver_tools(
            account_id="other",
            external_user_id="user-1",
            core_repository=self.core,
            external_repository=self.external,
            knowledge_retriever=FakeRetriever(),
        )
        ticket_tool = next(tool for tool in tools if tool.name == "get_ticket_context")

        with self.assertRaises(PermissionError):
            ticket_tool.invoke({"ticket_id": "ticket-1"})


class TestSpecialistNodes(LaneBTestCase):
    def test_resolver_persists_grounded_resolution(self):
        resolver = FakeAgent(
            {
                "response": "Use the password-reset option.",
                "confidence": 0.92,
                "sources": ["article-login"],
                "action": "none",
            }
        )
        state = {
            "messages": [HumanMessage(content="I cannot log in")],
            "ticket_id": "ticket-1",
            "account_id": "cultpass",
            "external_user_id": "user-1",
            "classification": self.classification(),
        }

        update = resolve_ticket(
            state,
            resolver=resolver,
            core_repository=self.core,
            external_repository=self.external,
            knowledge_retriever=FakeRetriever(),
        )

        self.assertEqual(update["status"], "resolved")
        self.assertEqual(update["sources"], ["article-login"])
        self.assertEqual(self.core.get_ticket_context("ticket-1")["status"], "resolved")

    def test_unapproved_action_does_not_mutate_external_database(self):
        resolver = FakeAgent(
            {
                "response": "The cancellation is ready for approval.",
                "confidence": 0.9,
                "sources": ["article-login"],
                "action": "cancel_reservation",
                "reservation_id": "reservation-1",
                "action_reason": "Customer requested cancellation",
            }
        )
        state = {
            "messages": [HumanMessage(content="Cancel my reservation")],
            "ticket_id": "ticket-1",
            "account_id": "cultpass",
            "external_user_id": "user-1",
            "classification": self.classification(),
        }

        update = resolve_ticket(
            state,
            resolver=resolver,
            core_repository=self.core,
            external_repository=self.external,
            knowledge_retriever=FakeRetriever(),
        )

        self.assertEqual(update["status"], "awaiting_approval")
        self.assertTrue(update["action_required"])
        customer = self.external.get_customer_context("user-1")
        self.assertEqual(customer["reservations"][0]["status"], "reserved")

    def test_approved_action_executes_and_persists(self):
        resolver = FakeAgent(
            {
                "response": "Your reservation has been cancelled.",
                "confidence": 0.95,
                "sources": [],
                "action": "cancel_reservation",
                "reservation_id": "reservation-1",
            }
        )
        state = {
            "messages": [HumanMessage(content="Cancel my reservation")],
            "ticket_id": "ticket-1",
            "account_id": "cultpass",
            "external_user_id": "user-1",
            "classification": self.classification(),
            "action_approved": True,
        }

        update = resolve_ticket(
            state,
            resolver=resolver,
            core_repository=self.core,
            external_repository=self.external,
            knowledge_retriever=FakeRetriever(),
        )

        self.assertEqual(update["status"], "resolved")
        self.assertTrue(update["action_result"]["changed"])
        customer = self.external.get_customer_context("user-1")
        self.assertEqual(customer["reservations"][0]["status"], "cancelled")

    def test_escalation_agent_persists_handoff(self):
        agent = FakeAgent(
            {
                "customer_message": "A specialist will review this request.",
                "internal_summary": "Login issue could not be resolved.",
                "reason": "Low confidence",
                "recommended_action": "Verify the account manually.",
            }
        )
        state = {
            "messages": [HumanMessage(content="I cannot log in")],
            "ticket_id": "ticket-1",
            "account_id": "cultpass",
            "classification": self.classification(),
            "resolution_confidence": 0.4,
        }

        update = escalate_ticket(
            state,
            escalation_agent=agent,
            core_repository=self.core,
        )

        self.assertEqual(update["status"], "escalated")
        self.assertEqual(self.core.get_ticket_context("ticket-1")["status"], "escalated")


if __name__ == "__main__":
    unittest.main()
