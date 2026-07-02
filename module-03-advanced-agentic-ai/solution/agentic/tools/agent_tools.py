"""LangChain tools bound to the current account and customer."""

from langchain_core.tools import BaseTool, tool

from agentic.tools.database import CoreRepository, ExternalRepository
from agentic.tools.knowledge import KnowledgeRetriever


def build_resolver_tools(
    *,
    account_id: str,
    external_user_id: str | None,
    core_repository: CoreRepository,
    external_repository: ExternalRepository,
    knowledge_retriever: KnowledgeRetriever,
) -> list[BaseTool]:
    """Create account-scoped tools that cannot cross the current tenant boundary."""

    @tool
    def search_knowledge(query: str, limit: int = 3) -> list[dict]:
        """Search approved support articles relevant to the customer's question."""

        return knowledge_retriever.search(account_id, query, limit)

    @tool
    def get_customer_context() -> dict:
        """Get the current customer's profile, subscription, and reservations."""

        if not external_user_id:
            raise ValueError("The ticket does not identify an external customer")
        return external_repository.get_customer_context(external_user_id)

    @tool
    def get_ticket_context(ticket_id: str) -> dict:
        """Get UDA-Hub metadata and message history for the current ticket."""

        context = core_repository.get_ticket_context(ticket_id)
        if context["account_id"] != account_id:
            raise PermissionError("Ticket belongs to a different account")
        if (
            external_user_id
            and context["user"]["external_user_id"] != external_user_id
        ):
            raise PermissionError("Ticket belongs to a different customer")
        return context

    @tool
    def propose_reservation_cancellation(reservation_id: str) -> dict:
        """Validate cancellation eligibility without changing the reservation."""

        if not external_user_id:
            raise ValueError("The ticket does not identify an external customer")
        return external_repository.propose_reservation_cancellation(
            reservation_id=reservation_id,
            external_user_id=external_user_id,
        )

    return [
        search_knowledge,
        get_customer_context,
        get_ticket_context,
        propose_reservation_cancellation,
    ]
