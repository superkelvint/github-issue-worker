import unittest
import batch_gut_check_policy as p

H = "a" * 40


def marker(head=H, disp="SUFFICIENT"):
    return f"{p.MARKER}\nhead_sha: {head}\ndisposition: {disp}\n"


def pr(**kw):
    x = {"number": 1, "head_sha": H, "comments": [], "writable": True}
    x.update(kw)
    return x


class BatchTests(unittest.TestCase):
    def test_current_sufficient_marker_skips_reaudit(self):
        self.assertFalse(p.should_audit(pr(comments=[marker()])))

    def test_stale_marker_never_skips_new_head(self):
        self.assertTrue(p.should_audit(pr(head_sha="b" * 40, comments=[marker()])))

    def test_gaps_remain_are_rechecked(self):
        self.assertTrue(p.should_audit(pr(comments=[marker(disp="GAPS_REMAIN")])))

    def test_explicit_fresh_pass_reaudits_current_marker(self):
        self.assertTrue(p.should_audit(pr(comments=[marker()]), fresh=True))

    def test_moving_head_is_active(self):
        self.assertEqual(p.audit_state(pr(head_moving=True)), "ACTIVE")

    def test_external_blocker_is_blocked(self):
        self.assertEqual(p.audit_state(pr(external_blocker=True)), "BLOCKED")

    def test_docs_only_can_be_na(self):
        self.assertEqual(p.audit_state(pr(runtime_tests_not_applicable=True)), "N/A")

    def test_unrecorded_na_needs_one_audit_record(self):
        self.assertTrue(p.should_audit(pr(runtime_tests_not_applicable=True)))

    def test_mutation_requires_writable_stable_bounded_branch(self):
        self.assertTrue(p.mutation_allowed(pr()))
        self.assertFalse(p.mutation_allowed(pr(writable=False)))
        self.assertFalse(p.mutation_allowed(pr(head_moving=True)))
        self.assertFalse(p.mutation_allowed(pr(separate_review_unit=True)))

    def test_batch_remaining_continues_past_blocked_pr(self):
        fleet = [
            pr(number=1, external_blocker=True),
            pr(number=2),
            pr(number=3, comments=[marker()]),
        ]
        self.assertEqual(p.remaining(fleet), [2])


if __name__ == "__main__":
    unittest.main(verbosity=2)
