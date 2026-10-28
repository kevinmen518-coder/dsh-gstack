from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)


class PackageTests(unittest.TestCase):
    def test_manifest_declares_bundle(self) -> None:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(package["dsh"]["bundle"]["patch"], "./cordis.patch.yml")
        self.assertIn("skills", package["files"])
        self.assertIn("cordis.patch.yml", package["files"])

    def test_bundle_patch_is_portable(self) -> None:
        patch = (ROOT / "cordis.patch.yml").read_text(encoding="utf-8")
        self.assertIn("providerName: dsh-gstack", patch)
        self.assertIn("includeDefaultRoots: false", patch)
        self.assertIn("new URL('skills/', baseUrl)", patch)
        self.assertNotIn("C:/Users/", patch)
        self.assertNotIn("C:\\Users\\", patch)

    def test_expected_skill_count(self) -> None:
        skill_files = sorted(SKILLS.glob("*/SKILL.md"))
        self.assertGreaterEqual(len(skill_files), 62)

    def test_no_double_gstack_prefix(self) -> None:
        names = [path.parent.name for path in SKILLS.glob("*/SKILL.md")]
        self.assertNotIn("gstack-gstack-upgrade", names)
        self.assertIn("gstack-upgrade", names)

    def test_bundled_resource_paths_are_relative(self) -> None:
        text = (SKILLS / "gstack-office-hours" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("sections/preamble.md", text)
        self.assertNotIn("~/.dsh/gstack/office-hours/", text)

    def test_names_are_unique_and_valid(self) -> None:
        names: list[str] = []
        for skill_file in sorted(SKILLS.glob("*/SKILL.md")):
            text = skill_file.read_text(encoding="utf-8")
            match = FRONTMATTER.match(text)
            self.assertIsNotNone(match, f"missing frontmatter: {skill_file}")
            assert match is not None
            name_match = re.search(r"(?m)^name:\s*(\S+)\s*$", match.group(1))
            description_match = re.search(r"(?m)^description:\s*(.+)$", match.group(1))
            self.assertIsNotNone(name_match, f"missing name: {skill_file}")
            self.assertIsNotNone(description_match, f"missing description: {skill_file}")
            name = name_match.group(1)
            self.assertRegex(name, r"^[a-z0-9][a-z0-9-]*$")
            self.assertEqual(skill_file.parent.name, name)
            names.append(name)
        self.assertEqual(len(names), len(set(names)))

    def test_router_skill_exists(self) -> None:
        self.assertTrue((SKILLS / "gstack" / "SKILL.md").is_file())
        self.assertTrue((SKILLS / "gstack-office-hours" / "SKILL.md").is_file())
        self.assertTrue((SKILLS / "gstack-plan-ceo-review" / "SKILL.md").is_file())

    def test_no_host_specific_paths_or_tool_names(self) -> None:
        forbidden = [
            "C:/Users/sxmen",
            "C:\\Users\\sxmen",
            "~/.claude/skills",
            "AskUserQuestion",
        ]
        for skill_file in SKILLS.glob("*/SKILL.md"):
            text = skill_file.read_text(encoding="utf-8")
            for value in forbidden:
                self.assertNotIn(value, text, f"{value} leaked into {skill_file}")

    def test_every_skill_has_install_notes_and_version(self) -> None:
        for skill_file in SKILLS.glob("*/SKILL.md"):
            text = skill_file.read_text(encoding="utf-8")
            self.assertIn("DSH install notes", text, str(skill_file))
            self.assertIn("upstream-version:", text, str(skill_file))

    def test_upstream_resources_are_copied(self) -> None:
        autoplan = SKILLS / "gstack-autoplan" / "sections" / "manifest.json"
        self.assertTrue(autoplan.is_file(), "autoplan resource directory was not copied")

    def test_slash_commands_use_dsh_names(self) -> None:
        text = (SKILLS / "gstack" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("/gstack-ship", text)
        self.assertNotRegex(text, r"(?<![\w./-])/office-hours(?![\w-])")


if __name__ == "__main__":
    unittest.main()
