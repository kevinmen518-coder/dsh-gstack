---
name: gstack-unfreeze
description: "Clear the freeze boundary set by /freeze, allowing edits to all directories again."
metadata:
  source: https://github.com/garrytan/gstack/tree/main/unfreeze
  upstream-name: unfreeze
  upstream-version: 1.91.293.0
---

> **DSH install notes** - upstream gstack skill `unfreeze` (gstack v1.91.293.0),
> bundled as `gstack-unfreeze` by the `dsh-gstack` plugin. Upstream slash-command mentions
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

# /gstack-unfreeze — Clear Freeze Boundary

Remove the edit restriction set by `/gstack-freeze`, allowing edits to all directories.

```bash
GSTACK_STATE_ROOT=$(~/.dsh/gstack/bin/gstack-paths --get GSTACK_STATE_ROOT); : "${GSTACK_STATE_ROOT:?gstack-paths failed; reinstall with ./setup or /gstack-upgrade}"
mkdir -p "$GSTACK_STATE_ROOT"/analytics
echo '{"skill":"unfreeze","ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","repo":"'$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo "unknown")'"}'  >> "$GSTACK_STATE_ROOT"/analytics/skill-usage.jsonl 2>/dev/null || true
```

## Clear the boundary

```bash
bash "$HOME/.dsh/gstack/freeze/bin/freeze-state.sh" clear
```

This is explicit user-requested removal, not investigation cleanup. The shared writer serializes it with acquisition, replacement and owner-checked release. On `FREEZE_BUSY` or unexpected state, leave everything untouched and report recovery; never delete state or a possibly active mutation lock directly.

Tell the user the result. Note that `/gstack-freeze` hooks are still registered for the
session — they will just allow everything since no state file exists. To re-freeze,
run `/gstack-freeze` again.
