from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import check_skill_layout as layout


class AgentMetadataValidationTests(unittest.TestCase):
    def write_metadata(self, content: str) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "openai.yaml"
        path.write_text(content, encoding="utf-8")
        return path

    def test_accepts_required_interface_fields(self):
        path = self.write_metadata(
            'interface:\n'
            '  display_name: "Coverage Risk Reducer"\n'
            '  short_description: "Reduce high-risk coverage gaps"\n'
        )
        self.assertEqual(layout.validate_agent_metadata(path), [])

    def test_rejects_missing_short_description(self):
        path = self.write_metadata(
            'interface:\n'
            '  display_name: "Coverage Risk Reducer"\n'
        )
        self.assertEqual(
            layout.validate_agent_metadata(path),
            [f"missing interface.short_description: {path.as_posix()}"],
        )

    def test_rejects_missing_display_name(self):
        path = self.write_metadata(
            'interface:\n'
            '  short_description: "Reduce high-risk coverage gaps"\n'
        )
        self.assertEqual(
            layout.validate_agent_metadata(path),
            [f"missing interface.display_name: {path.as_posix()}"],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
