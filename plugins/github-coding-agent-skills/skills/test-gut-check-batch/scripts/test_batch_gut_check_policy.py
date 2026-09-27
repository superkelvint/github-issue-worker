from datetime import datetime, timezone
import unittest

import batch_gut_check_policy as p

H = "a" * 40
NOW = datetime(2026, 9, 25, 23, 0, tzinfo=timezone.utc)


def marker(head=H, disp="SUFFICIENT"):
    return f"{p.MARKER}\nhead_sha: {head}\ndisposition: {disp}\n"


def pr(**kw):
    x = {
        "number": 1,
        "state": "open",
        "head_sha": H,
        "comments": [],
        "writable": True,
        "merged": False,
    }
    x.update(kw)
    return x


class BatchTests(unittest.TestCase):
    def test_default_scope_is_open(self):
        self.assertEqual(p.parse_scope_argument(None)["canonical"], "open")
        self.assertEqual(p.parse_scope_argument("")["canonical"], "open")

    def test_closed_defaults_to_72_hours(self):
        spec = p.parse_scope_argument("closed")
        self.assertEqual(spec["canonical"], "closed:72h")
        self.assertEqual(spec["lookback"].total_seconds(), 72 * 3600)

    def test_closed_scope_accepts_hours_and_days(self):
        self.assertEqual(p.parse_scope_argument("closed:12h")["canonical"], "closed:12h")
        self.assertEqual(p.parse_scope_argument("closed:3d")["canonical"], "closed:3d")

    def test_invalid_scope_fails_closed(self):
        for value in ["recent", "closed:0h", "closed:1w", "open:72h"]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    p.parse_scope_argument(value)

    def test_open_scope_selects_only_open_prs(self):
        self.assertTrue(p.in_scope(pr(state="open"), scope="open", now=NOW))
        self.assertFalse(
            p.in_scope(
                pr(state="closed", closed_at="2026-09-25T20:00:00Z"),
                scope="open",
                now=NOW,
            )
        )

    def test_closed_scope_uses_rolling_closed_at_window(self):
        inside = pr(
            state="closed",
            closed_at="2026-09-23T00:00:00Z",
            merged=True,
        )
        outside = pr(
            state="closed",
            closed_at="2026-09-22T22:59:59Z",
            merged=True,
        )
        self.assertTrue(p.in_scope(inside, scope="closed:72h", now=NOW))
        self.assertFalse(p.in_scope(outside, scope="closed:72h", now=NOW))

    def test_closed_scope_rejects_future_close_timestamp(self):
        future = pr(
            state="closed",
            closed_at="2026-09-26T00:00:00Z",
            merged=True,
        )
        self.assertFalse(p.in_scope(future, scope="closed:72h", now=NOW))

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

    def test_closed_unmerged_is_not_landed(self):
        closed = pr(
            state="closed",
            closed_at="2026-09-25T20:00:00Z",
            merged=False,
        )
        self.assertEqual(p.audit_state(closed, scope="closed:72h"), "NOT_LANDED")
        self.assertTrue(p.should_audit(closed, scope="closed:72h"))
        closed["comments"] = [marker(disp="NOT_LANDED")]
        self.assertFalse(p.should_audit(closed, scope="closed:72h"))

    def test_mutation_requires_writable_stable_bounded_open_branch(self):
        self.assertTrue(p.mutation_allowed(pr()))
        self.assertFalse(p.mutation_allowed(pr(writable=False)))
        self.assertFalse(p.mutation_allowed(pr(head_moving=True)))
        self.assertFalse(p.mutation_allowed(pr(separate_review_unit=True)))
        self.assertFalse(
            p.mutation_allowed(
                pr(
                    state="closed",
                    merged=True,
                    closed_at="2026-09-25T20:00:00Z",
                ),
                scope="closed:72h",
            )
        )

    def test_batch_remaining_continues_past_blocked_pr(self):
        fleet = [
            pr(number=1, external_blocker=True),
            pr(number=2),
            pr(number=3, comments=[marker()]),
        ]
        self.assertEqual(p.remaining(fleet, scope="open", now=NOW), [2])

    def test_closed_remaining_excludes_old_and_not_landed_after_record(self):
        fleet = [
            pr(
                number=1,
                state="closed",
                merged=True,
                closed_at="2026-09-25T20:00:00Z",
            ),
            pr(
                number=2,
                state="closed",
                merged=True,
                closed_at="2026-09-20T20:00:00Z",
            ),
            pr(
                number=3,
                state="closed",
                merged=False,
                closed_at="2026-09-25T19:00:00Z",
                comments=[marker(disp="NOT_LANDED")],
            ),
        ]
        self.assertEqual(p.remaining(fleet, scope="closed:72h", now=NOW), [1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
