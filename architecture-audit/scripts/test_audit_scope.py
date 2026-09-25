#!/usr/bin/env python3
import unittest

from audit_scope import ALL_MODULES, select


class AuditScopeTests(unittest.TestCase):
    def test_python_routes_client_and_cross_cutting(self):
        result = select("python client")
        self.assertIn("14-client-python.md", result["audit_files"])
        self.assertIn("03-searchkernel-protocol.md", result["audit_files"])
        self.assertIn("18-cross-cutting-gates.md", result["audit_files"])
        self.assertIn("area:python", result["area_labels"])

    def test_ir_adapter_routes_both_semantic_and_engine_boundaries(self):
        result = select("IR adapter lowering")
        self.assertIn("09-searchkernel-ir-adapter.md", result["audit_files"])
        self.assertIn("05-searchkernel-ir.md", result["audit_files"])
        self.assertIn("11-searchkernel-vespa-engine.md", result["audit_files"])

    def test_searchkerneld_includes_dispatch_boundary(self):
        result = select("searchkerneld")
        self.assertIn("13-searchkerneld.md", result["audit_files"])
        self.assertIn("08-searchkernel-dispatch.md", result["audit_files"])
        self.assertIn("area:searchkerneld", result["area_labels"])

    def test_unknown_scope_fails_open_to_live_inventory_not_fake_specificity(self):
        result = select("ruby client")
        self.assertEqual(
            result["audit_files"],
            ["00-audit-method.md", "18-cross-cutting-gates.md", "19-audit-record-and-freeze.md"],
        )
        self.assertIsNotNone(result["warning"])

    def test_repository_wide_routes_every_current_module(self):
        result = select("repository-wide")
        self.assertEqual(result["audit_files"], ALL_MODULES)
        self.assertEqual(len(result["audit_files"]), 20)


if __name__ == "__main__":
    unittest.main()
