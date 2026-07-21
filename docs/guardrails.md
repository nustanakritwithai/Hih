# Guardrails reference

All guardrails live in `hooks/pretool.sh` and `hooks/prewrite.sh`. Each has a
stable ID so blocked output is greppable in transcripts.

| ID  | Hook        | What it blocks                                        | Why                                                       |
| --- | ----------- | ----------------------------------------------------- | --------------------------------------------------------- |
| R01 | pretool     | `rm -rf /`, `rm -rf ~`, `rm -rf .`                    | Catastrophic, irreversible, no plausible legitimate use.  |
| R02 | pretool     | `git push --force` to a protected branch              | Rewrites shared history; loses other contributors' work.  |
| R03 | pretool     | `git reset --hard`                                    | Silent loss of uncommitted work; require explicit go.     |
| R04 | pretool     | `sudo`                                                | Escapes the sandbox; almost never needed for code work.   |
| R05 | pretool/pre | writes to `.env`, `*.pem`, `id_rsa`, `credentials.*`  | Avoids accidental secret commits.                         |
| R06 | pretool     | `chmod 777`                                           | World-writable is almost never the right answer.          |
| R07 | pretool     | `curl ... \| sh` (and `bash`/`zsh`)                   | Untrusted remote execution.                               |
| R08 | pretool     | `git commit --no-verify`                              | Bypasses pre-commit hooks; fix the root cause instead.    |
| R09 | pretool     | `--no-gpg-sign`                                       | Bypasses signing policy.                                  |
| R10 | pretool     | `git branch -D` on a protected branch                 | Hard branch delete on `main`/`master` is almost never OK. |

## Toggling

In `harness.toml`:

```toml
[guardrails]
R03_reset_hard = false   # disable the reset-hard guard
```

The script reads booleans on its own; setting `false` short-circuits the
matcher. (Note: the current shell implementation hard-enforces all rules. The
toggle is honoured by the upcoming Go implementation. In the meantime, comment
out the relevant block in `pretool.sh` to disable a rule locally.)

## Adding a new rule

1. Pick the next free ID (e.g. `R11`).
2. Add a regex matcher and a `block` call in `hooks/pretool.sh`.
3. Add a row to this table.
4. Add a test in `tests/run.sh` covering both pass and block paths.
5. Document it in `harness.toml` under `[guardrails]`.

## Override

You cannot override a guardrail with `--no-verify` or env vars. To override,
edit `hooks/pretool.sh` — and that edit is reviewed in the next PR.
