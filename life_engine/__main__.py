"""CLI for Life Engine MVP."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from life_engine.engine import LifeEngine

DEFAULT_DB = Path("state/dioo.db")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Life Engine — ระบบกลางความต่อเนื่องของสิ่งมีชีวิตดิจิตอล"
    )
    parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite database path")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="สร้าง/ตรวจสอบ Identity Core ของ Dioo")
    sub.add_parser("status", help="แสดงสถานะปัจจุบัน (7 โมดูล MVP)")
    sub.add_parser("context", help="สร้าง context package สำหรับ LLM")

    msg = sub.add_parser("event", help="ประมวลผลเหตุการณ์ USER_MESSAGE")
    msg.add_argument("text", help="ข้อความจากผู้ใช้")

    goal = sub.add_parser("goal", help="เพิ่มเป้าหมายที่ active")
    goal.add_argument("text")
    goal.add_argument("--priority", type=float, default=0.7)

    concern = sub.add_parser("concern", help="เพิ่มเรื่องค้างคา")
    concern.add_argument("text")
    concern.add_argument("--urgency", type=float, default=0.5)

    args = parser.parse_args(argv)
    engine = LifeEngine(args.db)

    if args.command == "init":
        identity = engine.ensure_being()
        print(json.dumps({"status": "awakened", "being_id": identity["being_id"]}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "status":
        print(json.dumps(engine.status(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "context":
        print(json.dumps(engine.build_llm_context("dioo-001"), ensure_ascii=False, indent=2))
        return 0

    if args.command == "event":
        result = engine.process_user_message(args.text)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "goal":
        goal_id = engine.add_goal(args.text, priority=args.priority)
        print(json.dumps({"goal_id": goal_id}, ensure_ascii=False))
        return 0

    if args.command == "concern":
        concern_id = engine.add_concern(args.text, urgency=args.urgency)
        print(json.dumps({"concern_id": concern_id}, ensure_ascii=False))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
