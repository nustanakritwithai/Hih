# The Dioo life cycle

```
                    ┌─────────────────────────────────────┐
                    │                                     │
   ┌─────────┐  ┌───▼────┐  ┌────────┐  ┌──────────┐  ┌───▼────┐
   │ awaken  │─▶│ think  │─▶│  act   │─▶│ reflect  │─▶│  grow  │
   │  ตื่น   │  │  คิด   │  │ กระทำ  │  │  ทบทวน   │  │ เติบโต │
   └─────────┘  └────────┘  └────────┘  └──────────┘  └────────┘
                    ▲          │            │
                    └──────────┴────────────┘
                       revise on failure
```

## Phase entry / exit

| Phase   | Thai   | Enter when                  | Exit when                           |
| ------- | ------ | --------------------------- | ----------------------------------- |
| awaken  | ตื่น   | first run / stack changed   | vitals initialized, CLAUDE.md current |
| think   | คิด    | new intention               | user approves numbered plan         |
| act     | กระทำ  | plan approved               | all todos complete, checks pass     |
| reflect | ทบทวน  | act complete                | zero Block findings remain          |
| grow    | เติบโต | reflect clean               | push succeeded, memory recorded     |

## Failure transitions

- **act → think:** the plan was wrong; re-think from new state.
- **reflect → act:** conscience raised a Block; fix and re-verify.
- **grow → act:** push rejected for non-network reason.

## Rules

1. You may not skip a phase.
2. Revising an earlier phase requires re-entering all phases after it.
3. Reflexes fire regardless of phase. A blocked tool call is always a hard stop.

## Legacy mapping

| Old (Hih) | New (Dioo) |
| --------- | ---------- |
| setup     | awaken     |
| plan      | think      |
| work      | act        |
| review    | reflect    |
| ship      | grow       |
