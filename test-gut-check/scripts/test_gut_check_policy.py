import unittest
import gut_check_policy as p

HEAD = "a" * 40


def base(**kw):
    x = {
        "head_sha": HEAD,
        "verified_head_sha": HEAD,
        "lineage_understood": True,
        "acceptance_mapped": True,
        "test_inventory_complete": True,
        "false_green_challenged": True,
    }
    x.update(kw)
    return x


class GutCheckTests(unittest.TestCase):
    def test_many_tests_alone_do_not_define_sufficient(self):
        self.assertEqual(p.disposition(base(meaningful_gap=True, test_count=100)), "GAPS_FOUND")

    def test_false_green_is_a_gap(self):
        self.assertEqual(p.disposition(base(plausible_false_green=True)), "GAPS_FOUND")

    def test_external_blocker_blocks(self):
        self.assertEqual(p.disposition(base(external_blocker=True)), "BLOCKED")

    def test_missing_lineage_blocks_conclusion(self):
        self.assertEqual(p.disposition(base(lineage_understood=False)), "BLOCKED")

    def test_clean_mapped_coverage_is_sufficient(self):
        self.assertEqual(p.disposition(base()), "SUFFICIENT")

    def test_actionable_gap_requires_remediation(self):
        self.assertTrue(p.remediation_required(base(meaningful_gap=True)))

    def test_unrectified_gap_cannot_complete(self):
        self.assertFalse(p.completion_allowed(base(meaningful_gap=True, gaps_rectified=False)))

    def test_new_product_bug_requires_observed_prefix_failure(self):
        self.assertFalse(p.completion_allowed(base(new_test_exposes_product_defect=True, prefx_failure_observed=False)))

    def test_stale_head_cannot_complete(self):
        self.assertFalse(p.completion_allowed(base(verified_head_sha="b" * 40)))

    def test_rectified_exact_head_can_complete(self):
        self.assertTrue(p.completion_allowed(base(meaningful_gap=True, gaps_rectified=True)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
