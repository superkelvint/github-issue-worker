import unittest
import reflection_policy as p


class ReflectionTests(unittest.TestCase):
    def test_repeated_instruction_is_recurring(self):
        self.assertEqual(p.evidence_strength({"repeat_count": 2}), "RECURRING")

    def test_severe_oneoff_is_not_dismissed(self):
        self.assertEqual(p.evidence_strength({"repeat_count": 1, "high_severity": True}), "HIGH_SEVERITY_ONE_OFF")

    def test_tooling_root_cause_beats_skill_creation(self):
        self.assertEqual(p.recommended_fix({"repository_tooling_cause": True, "distinct_missing_workflow": True, "repeat_count": 5}), "REPOSITORY_TOOLING")

    def test_existing_skill_is_preferred_over_new_skill(self):
        self.assertEqual(p.recommended_fix({"existing_skill_should_own": True, "distinct_missing_workflow": True, "repeat_count": 3}), "SKILL_CHANGE")

    def test_new_skill_needs_repeated_distinct_workflow(self):
        self.assertEqual(p.recommended_fix({"distinct_missing_workflow": True, "repeat_count": 1}), "NO_CHANGE")

    def test_repeated_polling_with_future_trigger_becomes_automation(self):
        self.assertEqual(p.recommended_fix({"clear_future_trigger": True, "repeated_polling": True}), "AUTOMATION")

    def test_isolated_annoyance_defaults_no_change(self):
        self.assertEqual(p.recommended_fix({}), "NO_CHANGE")

    def test_shortcut_that_skips_required_tests_is_rejected(self):
        self.assertFalse(p.shortcut_safe({"skips_required_tests": True}))

    def test_merge_before_exact_head_is_rejected(self):
        self.assertFalse(p.shortcut_safe({"merge_before_exact_head": True}))

    def test_skill_change_requires_safe_false_green_profile(self):
        item = {"existing_skill_should_own": True, "repeat_count": 3}
        self.assertTrue(p.skill_change_warranted(item))
        item["stale_cache_risk"] = True
        self.assertFalse(p.skill_change_warranted(item))


if __name__ == "__main__":
    unittest.main(verbosity=2)
