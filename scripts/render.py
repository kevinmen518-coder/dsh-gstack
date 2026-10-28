#!/usr/bin/env python3
"""Render garrytan/gstack skills for DeepSeek Harness.

The upstream repository ships Claude Code skills. This script keeps each
skill's Markdown and supporting resources, rewrites host-specific paths and
tool names, and writes a DSH-compatible skill tree plus a bundle manifest.

Usage:
    python scripts/render.py --source .build/gstack-main --output .
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.S)
NAME_LINE = re.compile(r"(?m)^name:[ \t]*(.+?)[ \t]*$")
DESC_LINE = re.compile(r"(?m)^description:[ \t]*(.*?)(?=^[A-Za-z_][A-Za-z0-9_-]*:|\Z)", re.S)

# All upstream skill directory names are collected at runtime. These are used
# only for rewriting slash-command references such as `/review` to the actual
# DSH skill name `/gstack-review`.
def parse_frontmatter(text: str) -> tuple[dict[str, str], str, str]:
    match = FRONTMATTER.match(text)
    if not match:
        raise ValueError("SKILL.md has no YAML frontmatter")
    raw = match.group(1)
    body = text[match.end() :]

    name_match = NAME_LINE.search(raw)
    if not name_match:
        raise ValueError("SKILL.md frontmatter has no name")
    upstream_name = name_match.group(1).strip().strip("'\"")

    desc_match = DESC_LINE.search(raw)
    description = ""
    if desc_match:
        description = desc_match.group(1).strip()
        if description.startswith(("|", ">")):
            lines = description.splitlines()[1:]
            description = " ".join(line.strip() for line in lines if line.strip())
        description = description.strip()
        if len(description) >= 2 and description[0] == description[-1] and description[0] in "\"'":
            description = description[1:-1].strip()
    if not description:
        description = f"gstack skill {upstream_name}."
    description = re.sub(r"\s*\(gstack\)\s*$", "", description).strip()

    return {"name": upstream_name, "description": description}, raw, body


def rewrite_body(body: str, upstream_name: str, command_map: dict[str, str]) -> str:
    body = body.replace("~/.claude/skills/gstack", "~/.dsh/gstack")
    body = body.replace(".claude/skills/gstack", ".dsh/gstack")
    body = body.replace("~/.claude/skills", "~/.dsh/skills")

    # Resources copied with this skill resolve against the skill directory
    # reported by DSH as resourceBase. References to gstack's shared bin/,
    # scripts/, and lib/ stay outside and require the optional checkout.
    if upstream_name != "gstack":
        prefix = f"~/.dsh/gstack/{upstream_name}/"
        body = body.replace(prefix, "")

    replacements = [
        ("Claude Code's Agent tool", "the subagent tool"),
        ("Agent tool", "subagent tool"),
        ("AskUserQuestion", "ask_user_question"),
        ("use the Bash tool", "use the pwsh tool"),
        ("the Bash tool", "the pwsh tool"),
        ("Bash tool", "pwsh tool"),
        ("use the Write tool", "use the write tool"),
        ("the Write tool", "the write tool"),
        ("use the Edit tool", "use the edit tool"),
        ("the Edit tool", "the edit tool"),
        ("use the Grep tool", "use the grep tool"),
        ("the Grep tool", "the grep tool"),
        ("use the Glob tool", "use the glob tool"),
        ("the Glob tool", "the glob tool"),
        ("the Read tool", "the read tool"),
        ("the Skill tool", "the skill tool"),
        ("Claude Code", "DeepSeek Harness"),
    ]
    for old, new in replacements:
        body = body.replace(old, new)

    # Rewrite slash-command mentions for skills that exist in the bundle.
    # Longest names first so /plan-eng-review wins over /plan and URLs are
    # protected by the preceding character check.
    alternatives = "|".join(re.escape(name) for name in sorted(command_map, key=len, reverse=True))
    slash = re.compile(rf"(?<![\w./-])/({alternatives})(?![\w-])")
    body = slash.sub(lambda m: f"/{command_map[m.group(1)]}", body)
    return body


def install_notes(upstream_name: str, dsh_name: str, version: str) -> str:
    return f"""> **DSH install notes** - upstream gstack skill `{upstream_name}` (gstack v{version}),
> bundled as `{dsh_name}` by the `dsh-gstack` plugin. Upstream slash-command mentions
> are rewritten to their `gstack-*` DSH skill names. Host tool names were mapped to
> DSH equivalents: `ask_user_question`, `pwsh`, `subagent`, and `skill`.
>
> The methodology, review frameworks, checklists, and Markdown resources are included.
> Resource paths inside this skill resolve against the skill directory reported by
> DSH as `resourceBase`. gstack's optional shared binaries and browser automation
> are not bundled, so commands that require Bun, Git Bash, Chromium, or native
> build tools must use their documented degraded path or be configured separately
> from the upstream repository.
"""


def render(source: Path, output: Path) -> int:
    version = (source / "VERSION").read_text(encoding="utf-8").strip()
    candidates: list[tuple[str, Path, Path]] = []

    for directory in sorted(source.iterdir(), key=lambda p: p.name):
        skill_file = directory / "SKILL.md"
        if directory.is_dir() and skill_file.is_file():
            candidates.append((directory.name, skill_file, directory))

    root_skill = source / "SKILL.md"
    if root_skill.is_file():
        candidates.append(("gstack", root_skill, None))

    if not candidates:
        raise RuntimeError(f"no gstack skills found in {source}")

    parsed: list[tuple[str, str, Path, Path | None, dict[str, str], str]] = []
    dsh_names: set[str] = set()
    command_map: dict[str, str] = {}
    for directory_name, skill_file, resource_dir in candidates:
        text = skill_file.read_text(encoding="utf-8")
        frontmatter, _raw, body = parse_frontmatter(text)
        if directory_name == "gstack":
            dsh_name = "gstack"
        elif directory_name.startswith("gstack-"):
            dsh_name = directory_name
        else:
            dsh_name = f"gstack-{directory_name}"
        if dsh_name in dsh_names:
            raise ValueError(f"duplicate rendered skill name: {dsh_name}")
        dsh_names.add(dsh_name)
        command_map[directory_name] = dsh_name
        parsed.append((dsh_name, directory_name, skill_file, resource_dir, frontmatter, body))

    skills_dir = output / "skills"
    if skills_dir.exists():
        shutil.rmtree(skills_dir)
    skills_dir.mkdir(parents=True)

    for dsh_name, upstream_name, skill_file, resource_dir, frontmatter, body in parsed:
        target_dir = skills_dir / dsh_name
        if resource_dir is None:
            target_dir.mkdir(parents=True)
        else:
            shutil.copytree(resource_dir, target_dir, ignore=shutil.ignore_patterns(".DS_Store", "Thumbs.db"))

        description = json.dumps(frontmatter["description"], ensure_ascii=False)
        if upstream_name == "gstack":
            source_url = "https://github.com/garrytan/gstack/blob/main/SKILL.md"
        else:
            source_url = f"https://github.com/garrytan/gstack/tree/main/{upstream_name}"
        new_frontmatter = (
            "---\n"
            f"name: {dsh_name}\n"
            f"description: {description}\n"
            "metadata:\n"
            f"  source: {source_url}\n"
            f"  upstream-name: {upstream_name}\n"
            f"  upstream-version: {version}\n"
            "---\n"
        )
        rewritten = rewrite_body(body, upstream_name, command_map)
        notes = install_notes(upstream_name, dsh_name, version)
        (target_dir / "SKILL.md").write_text(
            new_frontmatter + "\n" + notes + "\n" + rewritten.lstrip("\r\n"),
            encoding="utf-8",
            newline="\n",
        )

    return len(parsed)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    count = render(args.source.resolve(), args.output.resolve())
    print(f"rendered {count} skills")


if __name__ == "__main__":
    main()
