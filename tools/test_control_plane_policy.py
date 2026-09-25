import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import control_plane_policy as p

A = "a" * 40
B = "b" * 40

def state(**kw):
    obj = {"head_sha": A, "checks_head_sha": A, "required_checks_green": True, "mergeable": True, "acceptance_complete": True, "ordinary_review_complete": True, "merge_evidence_complete": True}
    obj.update(kw)
    return obj

class ControlPlanePolicyTests(unittest.TestCase):
    def test_old_head_evidence_is_stale(self):
        self.assertFalse(p.gate_current(state(head_sha=B, adversarial_review={"head_sha": A, "disposition": "VERIFIED"}), "adversarial_review"))

    def test_stale_gate_uses_delta_until_delta_reopens(self):
        obj = state(head_sha=B, adversarial_review={"head_sha": A, "disposition": "VERIFIED"})
        self.assertEqual(p.review_requirement(obj, required=True, evidence_key="adversarial_review"), "DELTA")
        self.assertEqual(p.review_requirement(obj, required=True, evidence_key="adversarial_review", delta_reopens=True), "FULL")

    def test_incomplete_merge_evidence_fails_closed(self):
        self.assertFalse(p.merge_eligible(state(merge_evidence_complete=False)))

    def test_green_checks_on_old_head_do_not_merge(self):
        self.assertFalse(p.merge_eligible(state(head_sha=B)))

    def test_relevant_main_fix_blocks_merge_until_incorporated(self):
        self.assertFalse(p.merge_eligible(state(behind_main=3, main_contains_relevant_fix=True)))

    def test_required_stale_review_blocks_merge(self):
        self.assertFalse(p.merge_eligible(state(adversarial_review_required=True, adversarial_review={"head_sha": B, "disposition": "VERIFIED"})))

    def test_issue_worker_hands_off_instead_of_merging(self):
        result = p.evaluate(state(handoff_ready=True), p.authority_for("issue"))
        self.assertEqual(result["owned_actions"], ["HANDOFF"])
        self.assertFalse(result["terminal_for_workflow"])

    def test_issue_worker_is_terminal_when_only_merge_remains(self):
        result = p.evaluate(state(), p.authority_for("issue"))
        self.assertEqual(result["unowned_actions"], ["MERGE"])
        self.assertTrue(result["terminal_for_workflow"])

    def test_pr_auto_owns_merge(self):
        result = p.evaluate(state(), p.authority_for("pr-auto"))
        self.assertEqual(result["owned_actions"], ["MERGE"])

    def test_red_ci_never_coexists_with_merge_action(self):
        result = p.evaluate(state(ci_red=True), p.authority_for("pr-auto"))
        self.assertIn("DIAGNOSE_CI", result["actions"])
        self.assertNotIn("MERGE", result["actions"])

    def test_known_implementation_defect_never_coexists_with_merge_action(self):
        result = p.evaluate(state(implementation_defect=True), p.authority_for("pr-auto"))
        self.assertIn("FIX_IMPLEMENTATION", result["actions"])
        self.assertNotIn("MERGE", result["actions"])

    def test_merge_requires_reconciliation(self):
        result = p.evaluate(state(merged=True, merge_reachable_from_main=False, reconciliation_evidence_complete=True, linked_issue_state_correct=True, stale_labels_or_duplicate_work=False), p.authority_for("issue-fixer"))
        self.assertEqual(result["owned_actions"], ["RECONCILE_ISSUE"])

    def test_shared_fix_propagation_is_pr_auto_owned(self):
        obj = state(merged=True, merge_reachable_from_main=True, reconciliation_evidence_complete=True, linked_issue_state_correct=True, stale_labels_or_duplicate_work=False, shared_fix_landed=True, affected_sibling_prs=[581, 584], propagation_complete=False)
        issue_result = p.evaluate(obj, p.authority_for("issue-fixer"))
        auto_result = p.evaluate(obj, p.authority_for("pr-auto"))
        self.assertIn("PROPAGATE_SHARED_FIX", issue_result["unowned_actions"])
        self.assertIn("PROPAGATE_SHARED_FIX", auto_result["owned_actions"])

    def test_incomplete_reconciliation_evidence_fails_closed(self):
        self.assertFalse(p.post_merge_reconciled(state(merged=True, merge_reachable_from_main=True)))

if __name__ == "__main__":
    unittest.main(verbosity=2)
