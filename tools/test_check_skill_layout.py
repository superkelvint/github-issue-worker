from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import check_skill_layout as layout


class AgentMetadataValidationTests(unittest.TestCase):
    def write_file(self, name: str, content: str) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_accepts_required_interface_fields(self):
        path = self.write_file(
            "openai.yaml",
            'interface:\n'
            '  display_name: "Coverage Risk Reducer"\n'
            '  short_description: "Reduce high-risk coverage gaps"\n',
        )
        self.assertEqual(layout.validate_agent_metadata(path), [])

    def test_rejects_missing_short_description(self):
        path = self.write_file(
            "openai.yaml",
            'interface:\n'
            '  display_name: "Coverage Risk Reducer"\n',
        )
        self.assertEqual(
            layout.validate_agent_metadata(path),
            [f"missing interface.short_description: {path.as_posix()}"],
        )


class SkillFrontmatterValidationTests(unittest.TestCase):
    def write_skill(self, description: str) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "SKILL.md"
        path.write_text(
            f"---\nname: issue\ndescription: {description}\n---\n\nBody.\n",
            encoding="utf-8",
        )
        return path

    def test_accepts_valid_description(self):
        self.assertEqual(
            layout.validate_skill_frontmatter(
                self.write_skill("Claim an issue using the codex/issue-NUMBER branch.")
            ),
            [],
        )

    def test_rejects_angle_brackets_in_description(self):
        path = self.write_skill("Claim codex/issue-<number>.")
        self.assertEqual(
            layout.validate_skill_frontmatter(path),
            [f"skill description contains forbidden angle brackets: {path.as_posix()}"],
        )


class MarketplaceValidationTests(unittest.TestCase):
    def valid_marketplace(self):
        return {
            "plugins": [
                {
                    "name": layout.PLUGIN_NAME,
                    "source": {
                        "source": "local",
                        "path": layout.EXPECTED_MARKETPLACE_PATH,
                    },
                    "policy": {
                        "installation": "AVAILABLE",
                        "authentication": "ON_INSTALL",
                    },
                    "category": "Productivity",
                }
            ]
        }

    def test_accepts_canonical_plugin_subdirectory(self):
        self.assertEqual(layout.validate_marketplace_data(self.valid_marketplace()), [])

    def test_rejects_marketplace_root_as_plugin_path(self):
        data = self.valid_marketplace()
        data["plugins"][0]["source"]["path"] = "./"
        self.assertIn(
            "marketplace plugin source.path must be "
            f"{layout.EXPECTED_MARKETPLACE_PATH!r}",
            layout.validate_marketplace_data(data),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
