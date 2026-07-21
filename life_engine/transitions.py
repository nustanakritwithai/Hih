"""Controlled state transitions — LLM cannot write state directly."""

from __future__ import annotations

# Per-event caps (stability rules from Life Engine spec)
MAX_TRUST_DELTA = 0.02
MAX_FAMILIARITY_DELTA = 0.02
MAX_TRAIT_DELTA_PER_DAY = 0.005
MAX_COGNITIVE_DELTA = 0.08

DEFAULT_COGNITIVE = {
    "curiosity": 0.7,
    "certainty": 0.5,
    "confusion": 0.1,
    "cognitive_load": 0.2,
}

DEFAULT_SOCIAL = {
    "trust": 0.5,
    "familiarity": 0.3,
    "interaction_readiness": 0.7,
}

DEFAULT_ACTIVITY = {
    "current_focus": None,
    "focus_strength": 0.0,
    "interruption_tolerance": 0.6,
}


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def apply_delta(current: float, delta: float, max_delta: float) -> float:
    bounded = max(-max_delta, min(max_delta, delta))
    return clamp(current + bounded)


def merge_cognitive(current: dict, updates: dict) -> dict:
    out = {**DEFAULT_COGNITIVE, **current}
    for key, delta in updates.items():
        if key in out and isinstance(delta, (int, float)):
            out[key] = apply_delta(float(out[key]), float(delta), MAX_COGNITIVE_DELTA)
    return out


def merge_social(current: dict, updates: dict) -> dict:
    out = {**DEFAULT_SOCIAL, **current}
    if "trust" in updates:
        out["trust"] = apply_delta(float(out["trust"]), float(updates["trust"]), MAX_TRUST_DELTA)
    if "familiarity" in updates:
        out["familiarity"] = apply_delta(
            float(out["familiarity"]), float(updates["familiarity"]), MAX_FAMILIARITY_DELTA
        )
    if "interaction_readiness" in updates:
        out["interaction_readiness"] = apply_delta(
            float(out["interaction_readiness"]),
            float(updates["interaction_readiness"]),
            MAX_COGNITIVE_DELTA,
        )
    return out


def appraise_user_message(text: str) -> dict:
    """Rule-based appraisal for MVP. LLM can propose richer appraisal later."""
    lower = text.lower()
    cognitive: dict[str, float] = {"curiosity": 0.03}
    social: dict[str, float] = {"familiarity": 0.01, "interaction_readiness": 0.02}

    if any(w in lower for w in ("ไม่เข้าใจ", "สับสน", "งง", "confus")):
        cognitive["confusion"] = 0.05
        cognitive["certainty"] = -0.03
    if any(w in lower for w in ("ขอบคุณ", "ดีมาก", "เข้าใจแล้ว", "thank")):
        social["trust"] = 0.015
        cognitive["certainty"] = 0.02
    if any(w in lower for w in ("ไม่ตรง", "ผิด", "คลาดเคลื่อน", "wrong")):
        cognitive["certainty"] = -0.04
        cognitive["confusion"] = 0.04
        social["trust"] = -0.005
    if any(w in lower for w in ("life engine", "สิ่งมีชีวิต", "digital being", "dioo")):
        cognitive["curiosity"] = 0.05

    importance = 0.5
    if len(text) > 200:
        importance += 0.1
    if any(w in lower for w in ("สำคัญ", "อย่าลืม", "จำไว้", "important")):
        importance += 0.2

    return {
        "cognitive_updates": cognitive,
        "social_updates": social,
        "importance": clamp(importance),
        "should_reflect": importance >= 0.65 or any(
            w in lower for w in ("ท้อ", "เสียใจ", "ไม่ต้องการ", "ย้ำ")
        ),
    }
