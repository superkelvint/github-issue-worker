import unittest
from pathlib import Path

from coverage_risk import inventory


class CoverageRiskTests(unittest.TestCase):
    def test_inventory_excludes_generated_and_test_files_and_orders_pressure(self):
        payload = {
            "data": [{
                "files": [
                    {"filename": "/repo/src/critical.rs", "summary": {
                        "lines": {"count": 100, "covered": 50, "percent": 50.0},
                        "functions": {"count": 10, "covered": 4, "percent": 40.0},
                        "regions": {"count": 120, "covered": 55, "percent": 45.8333},
                    }},
                    {"filename": "/repo/src/small.rs", "summary": {
                        "lines": {"count": 10, "covered": 9, "percent": 90.0},
                        "functions": {"count": 2, "covered": 2, "percent": 100.0},
                        "regions": {"count": 12, "covered": 11, "percent": 91.6667},
                    }},
                    {"filename": "/repo/generated/rpc.rs", "summary": {
                        "lines": {"count": 500, "covered": 0, "percent": 0.0},
                    }},
                    {"filename": "/repo/tests/integration.rs", "summary": {
                        "lines": {"count": 500, "covered": 0, "percent": 0.0},
                    }},
                ]
            }]
        }

        rows = inventory(payload, Path("/repo"), include_tests=False)
        self.assertEqual([r["path"] for r in rows], ["src/critical.rs", "src/small.rs"])
        self.assertEqual(rows[0]["uncovered_lines"], 50)
        self.assertEqual(rows[0]["uncovered_functions"], 6)

    def test_missing_percent_is_derived(self):
        payload = {"data": [{"files": [{
            "filename": "/repo/src/lib.rs",
            "summary": {
                "lines": {"count": 4, "covered": 3},
                "functions": {"count": 0, "covered": 0},
                "regions": {"count": 2, "covered": 1},
            },
        }]}]}
        row = inventory(payload, Path("/repo"), include_tests=False)[0]
        self.assertEqual(row["lines"]["percent"], 75.0)
        self.assertEqual(row["functions"]["percent"], 100.0)
        self.assertEqual(row["regions"]["percent"], 50.0)


if __name__ == "__main__":
    unittest.main()
