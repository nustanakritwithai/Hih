"""State transition rules — each value changes for explicit reasons."""

from __future__ import annotations

# Documented rules (Level 2.5 → 3)
STATE_RULES = {
    "curiosity": {
        "increase": [
            "พบเรื่องใหม่ / new topic",
            "มีคำถามที่ยังไม่ได้คำตอบ",
            "พบความขัดแย้งในความเชื่อ",
            "ได้รับ feedback สถาปัตยกรรม",
        ],
        "decrease": ["โฟกัสเสร็จสมบูรณ์", "ไม่มีข้อมูลใหม่ระยะยาว"],
    },
    "certainty": {
        "increase": [
            "ทดลองสำเร็จ / tests pass",
            "มีหลักฐานยืนยัน",
            "reflection สรุปได้ชัด",
        ],
        "decrease": ["ข้อมูลขัดแย้ง", "แผนล้มเหลว", "ผู้สร้องชี้ว่าคลาดเคลื่อน"],
    },
    "confusion": {
        "increase": ["ข้อมูลขัดแย้ง", "เป้าหมายซ้อนกัน", "belief disputed"],
        "decrease": ["reflection ชัด", "belief promoted"],
    },
    "cognitive_load": {
        "increase": [
            "หลายเป้าหมายพร้อมกัน",
            "concerns เปิดหลายเรื่อง",
            "reflection ค้าง",
        ],
        "decrease": ["ปิด concern", "จบ session reflection"],
    },
}

# Per-event caps
MAX_TRUST_DELTA = 0.02
MAX_FAMILIARITY_DELTA = 0.02
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
    "focus_detail": None,
}


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def apply_delta(current: float, delta: float, max_delta: float) -> float:
    bounded = max(-max_delta, min(max_delta, delta))
    return clamp(current + bounded)


def merge_cognitive(current: dict, updates: dict, reasons: list[str] | None = None) -> dict:
    out = {**DEFAULT_COGNITIVE, **current}
    for key, delta in updates.items():
        if key in out and isinstance(delta, (int, float)):
            out[key] = apply_delta(float(out[key]), float(delta), MAX_COGNITIVE_DELTA)
    if reasons:
        out["_last_transition_reasons"] = reasons
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


def apply_reflection_effects(cognitive: dict) -> dict:
    """After session reflection: certainty up, load down."""
    return merge_cognitive(
        cognitive,
        {"certainty": 0.04, "cognitive_load": -0.06, "confusion": -0.03},
        reasons=["session_reflection_completed"],
    )


def apply_architecture_feedback(cognitive: dict) -> dict:
    return merge_cognitive(
        cognitive,
        {"curiosity": 0.05, "certainty": 0.02},
        reasons=["architecture_feedback_received"],
    )


def appraise_user_message(text: str) -> dict:
    lower = text.lower()
    cognitive: dict[str, float] = {"curiosity": 0.03}
    social: dict[str, float] = {"familiarity": 0.01, "interaction_readiness": 0.02}
    reasons = ["user_message_received"]

    if any(w in lower for w in ("ไม่เข้าใจ", "สับสน", "งง", "confus")):
        cognitive["confusion"] = 0.05
        cognitive["certainty"] = -0.03
        reasons.append("confusion_detected")
    if any(w in lower for w in ("ขอบคุณ", "ดีมาก", "เข้าใจแล้ว", "thank", "ถูกทาง")):
        social["trust"] = 0.015
        cognitive["certainty"] = 0.02
        reasons.append("positive_acknowledgment")
    if any(w in lower for w in ("ไม่ตรง", "ผิด", "คลาดเคลื่อน", "wrong")):
        cognitive["certainty"] = -0.04
        cognitive["confusion"] = 0.04
        social["trust"] = -0.005
        reasons.append("correction_received")
    if any(w in lower for w in ("life engine", "สิ่งมีชีวิต", "digital being", "dioo", "belief", "reflection")):
        cognitive["curiosity"] = 0.05
        reasons.append("core_topic_engaged")
    if any(w in lower for w in ("level 2", "transition", "focus", "autonomy", "สถาปัตยกรรม")):
        cognitive["curiosity"] = cognitive.get("curiosity", 0.03) + 0.05
        cognitive["certainty"] = cognitive.get("certainty", 0) + 0.02
        cognitive["cognitive_load"] = cognitive.get("cognitive_load", 0) + 0.04
        reasons.append("architecture_feedback")

    importance = 0.5
    if len(text) > 200:
        importance += 0.1
    if any(w in lower for w in ("สำคัญ", "อย่าลืม", "จำไว้", "important")):
        importance += 0.2

    should_reflect = (
        importance >= 0.65
        or any(w in lower for w in ("ท้อ", "เสียใจ", "ไม่ต้องการ", "ย้ำ"))
        or ("level 2" in lower or "belief system" in lower or "reflection" in lower and len(text) > 500)
    )

    return {
        "cognitive_updates": cognitive,
        "social_updates": social,
        "importance": clamp(importance),
        "should_reflect": should_reflect,
        "transition_reasons": reasons,
        "should_session_reflect": len(text) > 800 or "level 2.5" in lower,
    }


def clamp_importance(value: float) -> float:
    return clamp(value)
