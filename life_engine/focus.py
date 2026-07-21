"""Structured focus — not a static string."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

UTC = timezone.utc


def make_focus(
    focus: str,
    strength: float,
    reason: str,
    progress: float = 0.0,
    review_hours: int = 24,
) -> dict[str, Any]:
    now = datetime.now(UTC).replace(microsecond=0)
    review = now + timedelta(hours=review_hours)
    return {
        "focus": focus,
        "strength": round(min(1.0, max(0.0, strength)), 2),
        "started_at": now.isoformat().replace("+00:00", "Z"),
        "reason": reason,
        "progress": round(min(1.0, max(0.0, progress)), 2),
        "review_at": review.isoformat().replace("+00:00", "Z"),
    }


def focus_needs_review(focus_detail: dict[str, Any] | None) -> bool:
    if not focus_detail or "review_at" not in focus_detail:
        return False
    try:
        review = datetime.fromisoformat(focus_detail["review_at"].replace("Z", "+00:00"))
        return datetime.now(UTC) >= review
    except (ValueError, TypeError):
        return False


def advance_focus_progress(focus_detail: dict[str, Any], delta: float) -> dict[str, Any]:
    out = dict(focus_detail)
    out["progress"] = round(min(1.0, float(out.get("progress", 0)) + delta), 2)
    return out
