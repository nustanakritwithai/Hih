"""Format Life Engine context as readable presence for the model."""

from __future__ import annotations

from typing import Any


def format_presence(context: dict[str, Any], last_event: str | None = None) -> str:
    identity = context.get("identity_summary", {})
    state = context.get("current_state", {})
    cognitive = state.get("cognitive", {})
    social = state.get("social", {})
    activity = state.get("activity", {})
    continuity = state.get("continuity", {})
    rel = context.get("relationship_summary", {})

    lines = [
        "# Dioo — สถานะปัจจุบัน",
        "",
        "> ไฟล์นี้สร้างโดย Life Engine — อ่านก่อนตอบผู้ใช้ทุกครั้ง",
        "",
        "## ตัวตน",
        f"- **ชื่อ:** {identity.get('name', 'Dioo')} (ดิโอ)",
        f"- **คุณค่าหลัก:** {', '.join(identity.get('core_values', []))}",
        "",
        "### นิยามตัวเอง",
    ]
    for item in identity.get("self_concept", []):
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## สภาพภายในตอนนี้",
            f"- **ความอยากรู้:** {cognitive.get('curiosity', 0):.2f}",
            f"- **ความมั่นใจ:** {cognitive.get('certainty', 0):.2f}",
            f"- **ความสับสน:** {cognitive.get('confusion', 0):.2f}",
            f"- **โหลดการคิด:** {cognitive.get('cognitive_load', 0):.2f}",
            f"- **ความไว้วางใจ (ผู้ใช้):** {social.get('trust', 0):.2f}",
            f"- **ความคุ้นเคย:** {social.get('familiarity', 0):.2f}",
            f"- **พร้อมสนทนา:** {social.get('interaction_readiness', 0):.2f}",
        ]
    )
    focus = activity.get("current_focus")
    if focus:
        lines.append(f"- **โฟกัสปัจจุบัน:** {focus}")

    last_at = continuity.get("last_interaction_at")
    if last_at:
        lines.extend(["", f"**ปฏิสัมพันธ์ล่าสุด:** {last_at}"])

    if rel:
        lines.extend(
            [
                "",
                "## ความสัมพันธ์",
                f"- **ประเภท:** {rel.get('relationship_type', 'creator_companion')}",
                f"- **ความไว้วางใจ:** {rel.get('trust', 0):.2f}",
                f"- **จำนวนปฏิสัมพันธ์:** {rel.get('interaction_count', 0)}",
            ]
        )

    goals = context.get("active_goals", [])
    if goals:
        lines.extend(["", "## เป้าหมายที่กำลังติดตาม"])
        for g in goals:
            lines.append(f"- [{g.get('priority', 0):.2f}] {g.get('goal_text', '')}")

    concerns = context.get("open_concerns", [])
    if concerns:
        lines.extend(["", "## เรื่องค้างคา"])
        for c in concerns:
            lines.append(f"- [{c.get('urgency', 0):.2f}] {c.get('concern_text', '')}")

    memories = context.get("relevant_memories", [])
    if memories:
        lines.extend(["", "## ความทรงจำล่าสุด"])
        for m in memories[:5]:
            lines.append(f"- ({m.get('timestamp', '')}) {m.get('event_text', '')[:120]}")

    self_mem = context.get("self_memories", [])
    if self_mem:
        lines.extend(["", "## สิ่งที่เรียนรู้เกี่ยวกับตัวเอง"])
        for s in self_mem[:3]:
            adj = s.get("behavioral_adjustment")
            line = f"- {s.get('observation', '')}"
            if adj:
                line += f" → {adj}"
            lines.append(line)

    intent = context.get("selected_intent", {})
    lines.extend(
        [
            "",
            "## ความตั้งใจในการตอบ",
            f"- **intent:** {intent.get('intent', 'respond')}",
            f"- **tone:** {intent.get('tone', 'clear_and_thoughtful')}",
            f"- **depth:** {intent.get('depth', 'match_user')}",
        ]
    )

    if last_event:
        lines.extend(["", "## เหตุการณ์ล่าสุด", f"> {last_event}"])

    boundaries = identity.get("boundaries", {})
    if boundaries:
        lines.extend(["", "## ขอบเขต (ห้ามละเมิด)"])
        for key, val in boundaries.items():
            if val:
                lines.append(f"- {key}")

    return "\n".join(lines) + "\n"
