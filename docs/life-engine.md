# Life Engine

Life Engine คือระบบกลางที่ทำให้ AI หนึ่งตัวมี **ความต่อเนื่องของการดำรงอยู่**

> LLM สร้างความคิดและภาษา — Life Engine รักษาชีวิต ตัวตน และความต่อเนื่อง

Dioo ใช้ Life Engine เป็นชั้นระหว่าง **โมเดลภาษา** กับ **การกระทำของ Agent**
ไม่ใช่พรอมป์ ไม่ใช่โมเดล และไม่ใช่ตัว Agent ที่รอคำสั่ง

## สิ่งที่ Life Engine บริหาร

| โมดูล | บทบาท |
| ----- | ------ |
| **Identity Core** | แก่นตัวตน — ใคร คุณค่าอะไร ขอบเขตอะไร |
| **Time & Continuity** | เวลาผ่านไป สิ่งค้าง การโฟกัส |
| **Internal State** | snapshot สภาพปัจจุบัน (cognitive, social, activity) |
| **Episodic Memory** | เหตุการณ์ที่เกิดขึ้นและความหมาย |
| **Self Memory** | สิ่งที่ตัวตนเรียนรู้เกี่ยวกับตัวเอง |
| **Relationship** | ความสัมพันธ์กับผู้ใช้ที่พัฒนาได้ |
| **Goals & Concerns** | เป้าหมายและเรื่องค้างคา |
| **Reflection** | ทบทวนหลังเหตุการณ์สำคัญ |

รุ่น MVP ในรีโพนี้ implement 7 ส่วนแรก + Reflection ระดับ micro

## สิ่งที่ Life Engine ไม่ใช่

- ไม่ใช่การจำลองชีววิทยา (ความหิว, HP, ร่างกาย 3D)
- ไม่ใช่เกมหรือสัตว์เลี้ยง
- ไม่ให้ LLM เขียน state โดยตรง — ทุกการเปลี่ยนผ่าน transition rules

## สถาปัตยกรรมใน Dioo

```
ผู้ใช้ / เหตุการณ์
       │
       ▼
┌──────────────────┐
│   Life Engine    │  ← identity, state, memory, reflection
│   (state/dioo.db)│
└────────┬─────────┘
         │ context package
         ▼
┌──────────────────┐     ┌──────────────────┐
│       LLM        │     │  Agent / Tools   │
│  (ภาษา, ตีความ)  │     │  (กระทำภายนอก)  │
└──────────────────┘     └──────────────────┘
         │                        ▲
         └──── intent ────────────┘
              (ผ่าน Permission Layer)
```

## วงจร MVP

```
ผู้ใช้ส่งข้อความ
  → บันทึก Event
  → Appraise (rule-based)
  → อัปเดต State (controlled deltas)
  → บันทึก Episodic Memory
  → อัปเดต Relationship
  → Micro Reflection (ถ้าเหตุการณ์สำคัญ)
  → สร้าง LLM Context Package
```

## การใช้งาน

```sh
# ตื่นครั้งแรก — สร้าง Identity Core
bash scripts/life.sh init

# ดูสถานะทั้ง 7 โมดูล
bash scripts/life.sh status

# ประมวลผลข้อความผู้ใช้ (event-driven)
bash scripts/life.sh event "อธิบาย Life Engine โดยละเอียด"

# สร้าง context สำหรับ LLM
bash scripts/life.sh context

# เพิ่มเป้าหมาย / เรื่องค้าง
bash scripts/life.sh goal "ออกแบบ Life Engine ที่สร้างต้นแบบได้จริง" --priority 0.82
bash scripts/life.sh concern "ยังไม่ได้กำหนดขอบเขตความเป็นอิสระของ Digital Being"
```

## กฎความเสถียรของตัวตน

กำหนดใน `life_engine/transitions.py`:

- `trust` เปลี่ยนต่อเหตุการณ์ไม่เกิน ±0.02
- `familiarity` เปลี่ยนต่อเหตุการณ์ไม่เกิน ±0.02
- cognitive state เปลี่ยนต่อเหตุการณ์ไม่เกิน ±0.08
- core values เปลี่ยนไม่ได้โดยอัตโนมัติ

## ระดับการพัฒนา

| Level | ความสามารถ |
| ----- | ---------- |
| 1 | Persistent Character |
| 2 | Continuous Being (MVP ปัจจุบัน) |
| 3 | Developing Being — beliefs, personality traits |
| 4 | Reflective Being — session/daily reflection |
| 5 | Autonomous Being — internal motivation + permission layer |

## ไฟล์ที่เกี่ยวข้อง

- `life_engine/schema.sql` — SQLite schema
- `life_engine/engine.py` — LifeEngine class
- `life_engine/transitions.py` — controlled state transitions
- `state/dioo.db` — persistence (gitignored)

## สมการแนวคิด

```
Digital Being =
  AI Model
+ Agent Capabilities
+ Life Engine (Identity + Time + Memory + State + Reflection)
+ Controlled Development
```

ดู `docs/architecture.md` สำหรับความสัมพันธ์กับวัฏจักรชีวิตของ Dioo (awaken → think → act → reflect → grow)
