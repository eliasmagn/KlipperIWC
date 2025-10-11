"""Service helpers orchestrating status history persistence."""

from __future__ import annotations

from datetime import datetime

from klipperiwc.db.session import session_scope
from klipperiwc.models import PrinterStatus
from klipperiwc.repositories.status_history import (
    create_status_history,
    delete_older_than,
)

__all__ = ["record_status_snapshot", "purge_history_before"]


def record_status_snapshot(status: PrinterStatus, recorded_at: datetime | None = None) -> int:
    """Persist an incoming status update and return the new record id."""

    with session_scope() as session:
        entry = create_status_history(session, status, recorded_at)
        entry_id = entry.id
    return entry_id


def purge_history_before(before: datetime) -> int:
    """Remove history entries captured before ``before``."""

    with session_scope() as session:
        deleted = delete_older_than(session, before)
    return deleted
