from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class DeadlineState:
    state: str
    days: int | None = None


def deadline_state(due_date: date | None, today: date) -> DeadlineState:
    if due_date is None:
        return DeadlineState("none")
    days_remaining = (due_date - today).days
    if days_remaining == 0:
        return DeadlineState("due_today", 0)
    if days_remaining < 0:
        return DeadlineState("overdue", -days_remaining)
    return DeadlineState("upcoming", days_remaining)
