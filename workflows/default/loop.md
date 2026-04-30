# The default Hih loop

```
                    ┌─────────────────────────────────────┐
                    │                                     │
   ┌────────┐  ┌────▼───┐  ┌────────┐  ┌──────────┐  ┌────┴───┐
   │ setup  │─▶│  plan  │─▶│  work  │─▶│  review  │─▶│  ship  │
   └────────┘  └────────┘  └────────┘  └──────────┘  └────────┘
                    ▲          │            │
                    └──────────┴────────────┘
                       revise on red
```

## Stage entry / exit

| Stage  | Enter when                        | Exit when                              |
| ------ | --------------------------------- | -------------------------------------- |
| setup  | first run / stack changed         | `CLAUDE.md` reflects current stack     |
| plan   | new task assigned                 | user approves the numbered plan        |
| work   | plan approved                     | all todos complete, all checks pass    |
| review | work complete                     | zero `Block` findings remain           |
| ship   | review clean                      | push succeeded                         |

## Failure transitions

- **work → plan:** the plan was wrong; re-plan from new state.
- **review → work:** a reviewer raised a `Block`; fix and re-verify.
- **ship → work:** push rejected for reason other than network.

## Rules

1. You may not skip a stage.
2. You may revise an earlier stage at any time, but you must re-enter the
   stages between it and the current one (re-planning means re-working and
   re-reviewing).
3. Hooks fire regardless of stage. A blocked tool call is always a hard stop.
