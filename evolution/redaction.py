"""Secret redaction for trajectories and logs."""

from __future__ import annotations

import re
from typing import Any

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|password|token|bearer)\s*[:=]\s*\S+"),
    re.compile(r"-----BEGIN [A-Z ]+-----"),
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    re.compile(r"ghp_[a-zA-Z0-9]{20,}"),
]


def redact_text(text: str) -> str:
    out = text
    for pat in SECRET_PATTERNS:
        out = pat.sub("[REDACTED]", out)
    return out


def redact_obj(obj: Any) -> Any:
    if isinstance(obj, str):
        return redact_text(obj)
    if isinstance(obj, dict):
        return {k: redact_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_obj(x) for x in obj]
    return obj
