# dsh-gstack

[![DeepSeek Harness plugin](https://img.shields.io/badge/DeepSeek%20Harness-plugin-4f46e5)](#install)

Use [garrytan/gstack](https://github.com/garrytan/gstack) skills inside
[DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness).

This repository is a DSH bundle. Installing it registers the bundled skill
tree with DSH; it does not require a build step or a separate manual edit to
`cordis.patch.yml`.

Current upstream: **gstack 1.91.293.0**. Bundled skills: **62**.

## Install

```bash
dsh plugin --profile web add -w github:kevinmen518-coder/dsh-gstack
```

Replace `web` with the profile you use, such as `desktop`. `-w` is harmless on
current pnpm and is required on pnpm versions that still apply the workspace
root check. Restart the profile after installation so DSH composes the new
bundle and scans its skills.

Confirm that the bundle and skill provider were loaded:

```bash
dsh --profile web --dump-config
```

Look for `dsh-gstack` in `dsh.profile.bundles` and `dsh-gstack-skills` in the
composed config. The skill catalog should then list `gstack` and the
`gstack-*` skills.

### Troubleshooting

**`ERR_PNPM_ADDING_TO_ROOT`** — a DSH profile is itself a pnpm workspace (it
declares `packages: ['.', 'plugins/*']` in `pnpm-workspace.yaml`), so pnpm
refuses an `add` that targets the workspace root. Either keep `-w` on the CLI,
or add this to the profile's `pnpm-workspace.yaml` so GUI installs work too:

```yaml
ignoreWorkspaceRootCheck: true
```

**`'git' is not recognized`** — a `github:` spec is resolved through
`git ls-remote`, so git must be on `PATH`. If it is not, install from a tarball
URL instead, which needs no git:

```bash
dsh plugin --profile desktop add -w \
  https://codeload.github.com/kevinmen518-coder/dsh-gstack/tar.gz/refs/heads/main
```

**Skills installed but never listed** — the skill provider needs `dshHome` and
`agentsHome`; both are mandatory in the `dsh-skill-filesystem` schema and have
no defaults. This bundle sets them explicitly in `cordis.patch.yml`.

## What is included

All upstream skills are included as Markdown with their supporting resources
from each skill directory. Names are prefixed with `gstack-` to avoid collisions
with generic skills such as `review`, `qa`, `ship`, and `spec`. The repository
root skill is exposed as `gstack`.

Examples:

| Upstream command | DSH skill |
| --- | --- |
| `/office-hours` | `gstack-office-hours` |
| `/plan-ceo-review` | `gstack-plan-ceo-review` |
| `/plan-eng-review` | `gstack-plan-eng-review` |
| `/review` | `gstack-review` |
| `/qa` | `gstack-qa` |
| `/ship` | `gstack-ship` |

The renderer maps Claude Code host concepts to DSH equivalents:

- `AskUserQuestion` becomes `ask_user_question`;
- `Bash` becomes `pwsh`;
- `Task` / `Agent` become `subagent` / `subagent_fork`;
- `Skill` becomes `skill`;
- gstack checkout paths become `~/.dsh/gstack`.

## Capability boundaries

The planning, review, specification, investigation, retrospective, design
critique, and documentation workflows are Markdown-driven and usable directly.

The following upstream features depend on software that is not shipped in this
package:

| Feature | External requirement |
| --- | --- |
| `browse`, `qa`, browser-backed design review | gstack browser build |
| `make-pdf`, `diagram`, design binaries | gstack native build |
| `ship`, `land-and-deploy` git steps | Git for Windows or equivalent |
| gstack helper preamble | Bun and a gstack checkout |
| `cso` dynamic scanning | native compiler/toolchain |
| iOS skills | macOS and a real device |
| `codex`, GBrain sync | their respective CLIs |

When a helper is unavailable, use the skill's documented degraded path rather
than pretending the missing tool ran. To use the full upstream toolchain,
install gstack separately, for example at `~/.dsh/gstack`, and follow its
Windows prerequisites.

## Update

Re-render from a newer upstream checkout:

```bash
python scripts/render.py --source .build/gstack-main --output .
python -m unittest discover -s tests -v
```

Then bump `version` in `package.json` to the new upstream version.

## Development

```bash
python scripts/render.py --source .build/gstack-main --output .
python -m unittest discover -s tests -v
```

The renderer is intentionally stdlib-only so it also works with the Python that
ships with DSH Desktop.

## Attribution and license

The skills are derived from [garrytan/gstack](https://github.com/garrytan/gstack),
Copyright Garry Tan and contributors, licensed under MIT. This is an independent
community adaptation and is not affiliated with or endorsed by Garry Tan or
DeepSeek. See `LICENSE` and `NOTICE.md`.
