"""Read-only safety guard — blocks any mutation path."""

from __future__ import annotations

from enum import Enum
from typing import Any


class ReadOnlyViolation(Exception):
    """Raised when auditor attempts a forbidden mutation."""

    def __init__(self, action: str, detail: str = "") -> None:
        self.action = action
        self.detail = detail
        super().__init__(f"READ_ONLY_VIOLATION: {action}" + (f" — {detail}" if detail else ""))


class BlockedAction(str, Enum):
    WRITE = "write"
    UPDATE = "update"
    DELETE = "delete"
    ARCHIVE = "archive"
    SUPERSEDE = "supersede"
    CHANGE_WEIGHT = "change_weight"
    PROMOTE = "promote"
    MUTATE = "mutate"


class ReadOnlyGuard:
    """Runtime assertion that auditor performs zero mutations."""

    READ_ONLY_ASSERTION = True

    def __init__(self) -> None:
        self._blocked_actions: list[dict[str, str]] = []
        self.mutations_performed: int = 0

    def assert_read_only(self, action: BlockedAction, detail: str = "") -> None:
        entry = {"action": action.value, "detail": detail}
        self._blocked_actions.append(entry)
        raise ReadOnlyViolation(action.value, detail)

    def record_blocked_attempt(self, action: BlockedAction, detail: str = "") -> dict[str, str]:
        """Record a blocked action without raising (for advisory reports)."""
        entry = {"action": action.value, "detail": detail, "blocked": "true"}
        self._blocked_actions.append(entry)
        return entry

    @property
    def blocked_actions(self) -> list[dict[str, str]]:
        return list(self._blocked_actions)

    def verify_zero_mutations(self) -> bool:
        return self.mutations_performed == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "read_only_assertion": self.READ_ONLY_ASSERTION,
            "mutations_performed": self.mutations_performed,
            "blocked_actions": self.blocked_actions,
        }
