import unittest
import ci_fixer_policy as p

HEAD = "c" * 40


class CiFixerPolicyTests(unittest.TestCase):
    def test_main_fix_beats_product_blame(self):
        ctx = {"behind_main": True, "main_contains_plausible_fix": True, "product_regression": True}
        self.assertEqual(p.classify_failure(ctx), "STALE_PR_OR_FIXED_ON_MAIN")

    def test_unrelated_lane_is_fanout(self):
        self.assertEqual(p.classify_failure({"unrelated_lane_selected": True}), "WORKFLOW_SELECTION_OR_FANOUT")

    def test_runner_failure_classification(self):
        self.assertEqual(p.classify_failure({"runner_problem": True}), "RUNNER_TOOLCHAIN_OR_CONTAINER")

    def test_generated_drift_is_distinct(self):
        self.assertEqual(p.classify_failure({"generated_drift": True}), "GENERATED_ARTIFACT_DRIFT")

    def test_native_link_failure_is_distinct(self):
        self.assertEqual(p.classify_failure({"native_build_or_link_failure": True}), "BUILD_LINK_NATIVE_SDK")

    def test_unknown_when_evidence_is_insufficient(self):
        self.assertEqual(p.classify_failure({}), "UNKNOWN_NEEDS_DEEPER_EVIDENCE")

    def test_action_modes_do_not_mutate_inspect_request(self):
        self.assertEqual(p.action_mode("what is wrong with PR 5"), "INSPECT")
        self.assertEqual(p.action_mode("fix it"), "REPAIR")
        self.assertEqual(p.action_mode("fix CI on PR 461"), "REPAIR")
        self.assertEqual(p.action_mode("fix and merge PR 5"), "CLOSURE")

    def test_only_unexplained_failed_jobs_need_logs(self):
        jobs = [
            {"name": "ok", "conclusion": "success"},
            {"name": "known", "conclusion": "failure", "cause_explicit": True},
            {"name": "unknown", "conclusion": "failure", "cause_explicit": False},
        ]
        self.assertEqual([j["name"] for j in p.jobs_needing_logs(jobs)], ["unknown"])

    def test_transient_gets_at_most_one_targeted_rerun(self):
        self.assertTrue(p.should_rerun({"transient_evidence": True, "rerun_count": 0}))
        self.assertFalse(p.should_rerun({"transient_evidence": True, "rerun_count": 1}))

    def test_deterministic_signature_never_uses_flake_rerun(self):
        self.assertFalse(p.should_rerun({"transient_evidence": True, "rerun_count": 0, "deterministic_signature": True}))

    def test_inspect_mode_never_repairs(self):
        self.assertFalse(p.repair_allowed({"bounded_fix": True}, "INSPECT"))

    def test_bounded_repair_is_allowed_in_repair_mode(self):
        self.assertTrue(p.repair_allowed({"bounded_fix": True}, "REPAIR"))

    def test_owned_or_decision_bound_repairs_are_not_taken(self):
        self.assertFalse(p.repair_allowed({"bounded_fix": True, "owned_by_other_worker": True}, "REPAIR"))
        self.assertFalse(p.repair_allowed({"bounded_fix": True, "decision_required": True}, "REPAIR"))

    def test_old_head_never_counts_as_verified(self):
        self.assertFalse(p.exact_head_verified({"head_sha": HEAD, "verified_head_sha": "d" * 40, "required_checks_green": True}))

    def test_merge_requires_closure_mode_and_exact_head(self):
        ctx = {"head_sha": HEAD, "verified_head_sha": HEAD, "required_checks_green": True}
        self.assertFalse(p.merge_allowed(ctx, "REPAIR"))
        self.assertTrue(p.merge_allowed(ctx, "CLOSURE"))

    def test_head_move_after_verify_blocks_merge(self):
        ctx = {"head_sha": HEAD, "verified_head_sha": HEAD, "required_checks_green": True, "head_moved_after_verify": True}
        self.assertFalse(p.merge_allowed(ctx, "CLOSURE"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
