"""Database repositories for UDA-Hub and connected customer systems."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, joinedload, sessionmaker

from data.models import cultpass, udahub


SOLUTION_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CORE_DB = SOLUTION_ROOT / "data" / "core" / "udahub.db"
DEFAULT_EXTERNAL_DB = SOLUTION_ROOT / "data" / "external" / "cultpass.db"


def _session_factory(path: str | Path) -> sessionmaker[Session]:
    database_path = Path(path)
    if not database_path.is_file():
        raise FileNotFoundError(f"Database does not exist: {database_path}")
    engine = create_engine(f"sqlite:///{database_path}", echo=False)
    return sessionmaker(bind=engine, expire_on_commit=False)


class CoreRepository:
    """Read and persist UDA-Hub ticket state."""

    def __init__(self, db_path: str | Path = DEFAULT_CORE_DB) -> None:
        self.db_path = Path(db_path)
        self._sessions = _session_factory(self.db_path)

    def close(self) -> None:
        """Release pooled SQLite connections."""

        self._sessions.kw["bind"].dispose()

    def get_ticket_context(self, ticket_id: str) -> dict[str, Any]:
        with self._sessions() as session:
            result = session.execute(
                select(udahub.Ticket)
                .where(udahub.Ticket.ticket_id == ticket_id)
                .options(
                    joinedload(udahub.Ticket.user),
                    joinedload(udahub.Ticket.ticket_metadata),
                    joinedload(udahub.Ticket.messages),
                )
            )
            ticket = result.unique().scalar_one_or_none()
            if ticket is None:
                raise LookupError(f"Ticket not found: {ticket_id}")

            metadata = ticket.ticket_metadata
            return {
                "ticket_id": ticket.ticket_id,
                "account_id": ticket.account_id,
                "channel": ticket.channel,
                "user": {
                    "user_id": ticket.user.user_id,
                    "external_user_id": ticket.user.external_user_id,
                    "name": ticket.user.user_name,
                },
                "status": metadata.status if metadata else None,
                "issue_type": metadata.main_issue_type if metadata else None,
                "tags": metadata.tags if metadata else None,
                "messages": [
                    {
                        "role": message.role.value,
                        "content": message.content,
                        "created_at": message.created_at.isoformat()
                        if message.created_at
                        else None,
                    }
                    for message in sorted(
                        ticket.messages,
                        key=lambda item: item.created_at,
                    )
                ],
            }

    def save_outcome(
        self,
        *,
        ticket_id: str,
        content: str,
        status: str,
        issue_type: str | None = None,
        tags: list[str] | None = None,
    ) -> None:
        """Atomically append an AI response and update ticket metadata."""

        with self._sessions.begin() as session:
            ticket = session.get(udahub.Ticket, ticket_id)
            if ticket is None:
                raise LookupError(f"Ticket not found: {ticket_id}")

            metadata = session.get(udahub.TicketMetadata, ticket_id)
            if metadata is None:
                metadata = udahub.TicketMetadata(
                    ticket_id=ticket_id,
                    status=status,
                    main_issue_type=issue_type,
                    tags=", ".join(tags or []),
                )
                session.add(metadata)
            else:
                metadata.status = status
                if issue_type is not None:
                    metadata.main_issue_type = issue_type
                if tags is not None:
                    metadata.tags = ", ".join(tags)

            session.add(
                udahub.TicketMessage(
                    message_id=str(uuid.uuid4()),
                    ticket_id=ticket_id,
                    role=udahub.RoleEnum.ai,
                    content=content,
                )
            )


class ExternalRepository:
    """Read and safely mutate the connected CultPass database."""

    def __init__(self, db_path: str | Path = DEFAULT_EXTERNAL_DB) -> None:
        self.db_path = Path(db_path)
        self._sessions = _session_factory(self.db_path)

    def close(self) -> None:
        """Release pooled SQLite connections."""

        self._sessions.kw["bind"].dispose()

    def get_customer_context(self, external_user_id: str) -> dict[str, Any]:
        with self._sessions() as session:
            result = session.execute(
                select(cultpass.User)
                .where(cultpass.User.user_id == external_user_id)
                .options(
                    joinedload(cultpass.User.subscription),
                    joinedload(cultpass.User.reservations).joinedload(
                        cultpass.Reservation.experience
                    ),
                )
            )
            user = result.unique().scalar_one_or_none()
            if user is None:
                raise LookupError(f"CultPass user not found: {external_user_id}")

            subscription = user.subscription
            return {
                "user_id": user.user_id,
                "name": user.full_name,
                "is_blocked": user.is_blocked,
                "subscription": {
                    "status": subscription.status,
                    "tier": subscription.tier,
                    "monthly_quota": subscription.monthly_quota,
                }
                if subscription
                else None,
                "reservations": [
                    {
                        "reservation_id": reservation.reservation_id,
                        "status": reservation.status,
                        "experience_id": reservation.experience_id,
                        "experience": reservation.experience.title,
                        "when": reservation.experience.when.isoformat(),
                        "location": reservation.experience.location,
                    }
                    for reservation in user.reservations
                ],
            }

    def propose_reservation_cancellation(
        self,
        *,
        reservation_id: str,
        external_user_id: str,
    ) -> dict[str, Any]:
        """Validate a cancellation without changing database state."""

        with self._sessions() as session:
            reservation = session.scalar(
                select(cultpass.Reservation).where(
                    cultpass.Reservation.reservation_id == reservation_id,
                    cultpass.Reservation.user_id == external_user_id,
                )
            )
            if reservation is None:
                raise LookupError("Reservation was not found for this customer")
            return {
                "reservation_id": reservation.reservation_id,
                "current_status": reservation.status,
                "eligible": reservation.status == "reserved",
                "requires_human_approval": True,
            }

    def cancel_reservation(
        self,
        *,
        reservation_id: str,
        external_user_id: str,
        approved: bool,
    ) -> dict[str, Any]:
        """Cancel an owned reservation only after explicit external approval."""

        if approved is not True:
            raise PermissionError("Reservation cancellation requires human approval")

        with self._sessions.begin() as session:
            reservation = session.scalar(
                select(cultpass.Reservation).where(
                    cultpass.Reservation.reservation_id == reservation_id,
                    cultpass.Reservation.user_id == external_user_id,
                )
            )
            if reservation is None:
                raise LookupError("Reservation was not found for this customer")
            if reservation.status == "cancelled":
                return {
                    "reservation_id": reservation_id,
                    "status": "cancelled",
                    "changed": False,
                }
            if reservation.status != "reserved":
                raise ValueError(
                    f"Reservation in status {reservation.status!r} cannot be cancelled"
                )

            reservation.status = "cancelled"
            return {
                "reservation_id": reservation_id,
                "status": "cancelled",
                "changed": True,
            }
