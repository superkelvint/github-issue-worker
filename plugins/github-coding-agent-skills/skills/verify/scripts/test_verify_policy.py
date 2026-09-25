import unittest
import verify_policy as p

HEAD1 = "1" * 40
HEAD2 = "2" * 40


def base(**kw):
    pr = {
        "open": True,
        "draft": True,
        "head_sha": HEAD1,
        "tested_head": HEAD1,
        "local_verification_passed": True,
        "required_checks": ["success"],
        "head_writable": True,
        "repair_in_scope": True,
        "prepush_verification_passed": True,
    }
    pr.update(kw)
    return pr


class VerifyPolicyTests(unittest.TestCase):
    def test_only_github_drafts_enter_queue(self):
        prs = [base(), base(draft=False), base(open=False)]
        self.assertEqual(len(p.queue(prs)), 1)

    def test_green_exact_head_draft_is_ready(self):
        self.assertEqual(p.classify(base()), "READY")

    def test_old_head_evidence_restarts(self):
        self.assertEqual(p.classify(base(head_sha=HEAD2)), "RESTART_HEAD_CHANGED")

    def test_pending_required_check_keeps_draft(self):
        self.assertEqual(p.classify(base(required_checks=["pending"])), "DRAFT_BLOCKED")

    def test_environment_recovery_precedes_failure_classification(self):
        self.assertEqual(p.classify(base(environment_failure=True, environment_recovery_available=True)), "REMEDIATE_ENV")

    def test_pr_scoped_failure_can_be_repaired(self):
        self.assertEqual(p.classify(base(verification_failed=True)), "REPAIR")

    def test_unwritable_branch_cannot_be_auto_repaired(self):
        self.assertEqual(p.classify(base(verification_failed=True, head_writable=False)), "DRAFT_FAILED")

    def test_contract_change_required_is_not_safe_repair(self):
        self.assertFalse(p.repair_allowed(base(contract_change_required=True)))

    def test_concurrent_head_change_blocks_push_and_ready(self):
        pr = base(concurrent_change=True)
        self.assertFalse(p.repair_allowed(pr))
        self.assertFalse(p.ready_allowed(pr))

    def test_failed_required_check_blocks_ready(self):
        self.assertFalse(p.ready_allowed(base(required_checks=["failure"])))

    def test_unresolved_local_failure_blocks_ready(self):
        self.assertFalse(p.ready_allowed(base(unresolved_verification_failure=True)))

    def test_no_required_checks_can_pass_when_not_applicable(self):
        self.assertEqual(p.required_checks_state(base(required_checks=[])), "PASS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
