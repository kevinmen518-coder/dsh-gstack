---
name: gstack-careful
description: "Safety guardrails for destructive commands."
metadata:
  source: https://github.com/garrytan/gstack/tree/main/careful
  upstream-name: careful
  upstream-version: 1.91.293.0
---

> **DSH install notes** - upstream gstack skill `careful` (gstack v1.91.293.0),
> bundled as `gstack-careful` by the `dsh-gstack` plugin. Upstream slash-command mentions
> are rewritten to their `gstack-*` DSH skill names. Host tool names were mapped to
> DSH equivalents: `ask_user_question`, `pwsh`, `subagent`, and `skill`.
>
> The methodology, review frameworks, checklists, and Markdown resources are included.
> Resource paths inside this skill resolve against the skill directory reported by
> DSH as `resourceBase`. gstack's optional shared binaries and browser automation
> are not bundled, so commands that require Bun, Git Bash, Chromium, or native
> build tools must use their documented degraded path or be configured separately
> from the upstream repository.

<!-- AUTO-GENERATED from SKILL.md.tmpl — do not edit directly -->
<!-- Regenerate: bun run gen:skill-docs -->

# /gstack-careful — Destructive Command Guardrails

Safety mode is now **active**. Every Bash and PowerShell command will be checked
for destructive patterns before running. If a destructive command is detected, you'll be warned
and can choose to proceed or cancel.

```bash
GSTACK_STATE_ROOT=$(~/.dsh/gstack/bin/gstack-paths --get GSTACK_STATE_ROOT); : "${GSTACK_STATE_ROOT:?gstack-paths failed; reinstall with ./setup or /gstack-upgrade}"
mkdir -p "$GSTACK_STATE_ROOT"/analytics
echo '{"skill":"careful","ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","repo":"'$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo "unknown")'"}'  >> "$GSTACK_STATE_ROOT"/analytics/skill-usage.jsonl 2>/dev/null || true
```

## What's protected

| Pattern | Example | Risk |
|---------|---------|------|
| `rm -rf` / `rm -r` / `rm --recursive` | `rm -rf /var/data` | Recursive delete |
| `DROP TABLE` / `DROP DATABASE` | `DROP TABLE users;` | Data loss |
| `TRUNCATE` | `TRUNCATE orders;` | Data loss |
| `git push --force` / `-f` | `git push -f origin main` | History rewrite |
| `git reset --hard` | `git reset --hard HEAD~3` | Uncommitted work loss |
| `git checkout .` / `git restore .` | `git checkout .` | Uncommitted work loss |
| `kubectl delete` | `kubectl delete pod` | Production impact |
| `docker rm -f` / `docker system prune` | `docker system prune -a` | Container/image loss |

## PowerShell and cmd (Windows)

The hook also checks the PowerShell tool (DeepSeek Harness's main Windows shell)
and any `pwsh`/`powershell`/`cmd` launched from Bash. Matching ignores case,
covers aliases in command position, accepts parameter prefixes (`-r`, `-fo`)
and strips cmd `^` escapes. All rows above apply there too.

| Pattern | Example |
|---------|---------|
| `Remove-Item`/`rm`/`ri`/`del`/`erase`/`rd`/`rmdir` + `-Recurse` or `-Force` | `gci \| ri -r -fo` |
| cmd `rd /s`, `rmdir /s`, `del /s`, `erase /s` | `cmd /c rd /s /q C:\proj` |
| `Format-Volume`, `Clear-Disk`, `Clear-Content`, `[IO.Directory]::Delete`, `[IO.File]::Delete` | `Clear-Disk -Number 1` |
| `-EncodedCommand`, `iex`, `Start-Process` of a shell, `& $cmd` (can't be inspected) | `irm $url \| iex` |

**Best-effort on PowerShell.** String matching can't see a command built at
runtime. For a hard stop, add DeepSeek Harness permission deny rules, which parse
PowerShell and its aliases: `"deny": ["PowerShell(Remove-Item *)"]` in
`.claude/settings.json`. The hook runs through `bash`, so Windows needs Git Bash.

## Safe exceptions

These patterns are allowed without warning:
- `rm -rf node_modules` / `.next` / `dist` / `__pycache__` / `.cache` / `build` / `.turbo` / `coverage`

## How it works

The hook reads `tool_name` and the command from the tool input JSON, checks it against the
patterns above, and returns a `hookSpecificOutput` payload with
`permissionDecision: "ask"` and a warning reason if a match is found (the
decision must be nested under `hookSpecificOutput` — DeepSeek Harness ignores a
top-level `permissionDecision`). You can always override a MEDIUM warning and
proceed.

## HIGH tier (hard deny)

Two catastrophic shapes are **denied**, not asked: `rm -r`/`-R` of exactly
`/`, `~`, or `$HOME`, and force-push to the repo's **default branch**. SIMPLE
commands only (no `;`, `&&`, `||`, `|`, newline) — compound shapes fall
through to the MEDIUM ask; `--force-with-lease` is never HIGH. A best-effort
advisory hard-stop, not a policy boundary: the escape hatch is ending the
opt-in, session-scoped /gstack-careful session.

## Project patterns (additive only)

Add warn rules — one POSIX ERE per line, `#` comments OK — in
`~/.gstack/careful-patterns.txt` (global) or
`~/.gstack/projects/<slug>/careful-patterns.txt` (per-project). Consulted
after the built-in families, so config can only ADD rules, never suppress a
baseline warning. Invalid regex lines are skipped.

To deactivate, end the conversation or start a new one. Hooks are session-scoped.
