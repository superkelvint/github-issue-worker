import unittest
import followup_policy as p

HEAD1 = "a" * 40
HEAD2 = "b" * 40


def issue(**kw):
    obj = {
        "open": True,
        "status_labels": [p.NEEDS],
        "open_pr_count": 1,
        "followup_specific": True,
        "pr_needs_cto_review": False,
    }
    obj.update(kw)
    return obj


def work(**kw):
    obj = {
        "claimed": True,
        "pr_open": True,
        "head_sha": HEAD1,
        "tested_head": HEAD1,
        "verification_complete": True,
        "verification_passed": True,
        "head_writable": True,
    }
    obj.update(kw)
    return obj


class FollowupPolicyTests(unittest.TestCase):
    def test_requires_exactly_one_existing_open_pr(self):
        self.assertFalse(p.eligible(issue(open_pr_count=0)))
        self.assertFalse(p.eligible(issue(open_pr_count=2)))

    def test_already_in_progress_is_not_eligible(self):
        self.assertFalse(p.eligible(issue(status_labels=[p.IN_PROGRESS])))

    def test_pr_already_handed_to_cto_is_not_eligible(self):
        self.assertFalse(p.eligible(issue(pr_needs_cto_review=True)))

    def test_queue_contains_only_clean_followups(self):
        self.assertEqual(len(p.queue([issue(), issue(open_pr_count=0), issue(pr_needs_cto_review=True)])), 1)

    def test_claim_transition_is_exact(self):
        self.assertTrue(p.claim_transition_valid(issue(), issue(status_labels=[p.IN_PROGRESS])))
        self.assertFalse(p.claim_transition_valid(issue(), issue(status_labels=[p.NEEDS, p.IN_PROGRESS])))

    def test_unclaimed_eligible_issue_requests_claim(self):
        self.assertEqual(p.classify(issue(), work(claimed=False)), "CLAIM")

    def test_invalid_followup_releases_claim(self):
        self.assertEqual(p.classify(issue(), work(invalid_followup=True)), "RELEASE")

    def test_environment_recovery_is_attempted_before_blocking(self):
        self.assertEqual(p.classify(issue(), work(environment_failure=True, environment_recovery_available=True)), "REMEDIATE_ENV")

    def test_head_change_restarts_verification(self):
        self.assertEqual(p.classify(issue(), work(head_sha=HEAD2)), "RESTART_HEAD_CHANGED")

    def test_unwritable_existing_branch_blocks_code_followup(self):
        self.assertEqual(p.classify(issue(), work(code_change_required=True, head_writable=False)), "BLOCKED")

    def test_green_exact_head_can_hand_back(self):
        self.assertTrue(p.handoff_allowed(work()))
        self.assertEqual(p.classify(issue(), work()), "HANDOFF")

    def test_failed_required_verification_never_hands_off(self):
        obj = work(verification_passed=False, required_check_failing=True)
        self.assertFalse(p.handoff_allowed(obj))
        self.assertEqual(p.classify(issue(), obj), "BLOCKED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
