"""Load evolution.toml configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:
    tomllib = None  # type: ignore


DEFAULT_PATH = Path("evolution.toml")


def load_config(path: Path | None = None) -> dict[str, Any]:
    p = path or DEFAULT_PATH
    if not p.exists():
        return {
            "evolution": {"enabled": True, "phase": "E1", "level": "E2_SANDBOX_EXPERIMENT"},
            "features": {},
            "budget": {},
            "thresholds": {},
        }
    if tomllib is None:
        raise RuntimeError("tomllib required")
    data = tomllib.loads(p.read_text(encoding="utf-8"))
    return data


def feature_enabled(config: dict, name: str) -> bool:
    return bool(config.get("features", {}).get(name, False))
