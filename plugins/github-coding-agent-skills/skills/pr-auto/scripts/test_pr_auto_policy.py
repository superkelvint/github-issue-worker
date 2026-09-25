#!/usr/bin/env python3
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import pr_auto_policy as p

HEAD_A = "a" * 40
HEAD_B = "b" * 40


def base_pr(**overrides):
    pr = {
        "number": 100,
        "head_sha": HEAD_A,
        "draft": False,
        "conflicted": False,
        "mergeable": True,
        "ci": "green",
        "required_checks_complete": True,
        "issue_acceptance_complete": True,
        "ordinary_review_complete": True,
        "ready_for_review": True,
        "change_domains": ["docs"],
        "changed_file_count": 1,
        "changed_lines": 10,
        "behind_main": 0,
    }
    pr.update(overrides)
    return pr


class BlastRadiusTests(unittest.TestCase):
    def test_trivial_docs_are_low_risk(self):
        self.assertEqual(p.blast_radius(base_pr()), "LOW")

    def test_semantic_boundary_is_high_risk(self):
        self.assertEqual(p.blast_radius(base_pr(change_domains=["portable-semantics"])), "HIGH")

    def test_large_cross_cutting_change_is_high_even_without_named_domain(self):
        pr = base_pr(change_domains=["client-core", "transport", "packaging"], changed_file_count=12)
        self.assertEqual(p.blast_radius(pr), "HIGH")


class ReviewTrackingTests(unittest.TestCase):
    def test_parse_review_marker(self):
        text = f"""note
<!-- pr-auto:adversarial-review -->
PR-AUTO ADVERSARIAL REVIEW
head_sha: {HEAD_A}
disposition: NO_BLOCKER_FOUND
scope: persistence
reviewed_at: 2026-09-25T12:00:00Z
"""
        rec = p.parse_review_comment(text)
        self.assertIsNotNone(rec)
        self.assertEqual(rec.head_sha, HEAD_A)
        self.assertEqual(rec.disposition, "NO_BLOCKER_FOUND")

    def test_parse_architecture_audit_marker(self):
        text = f"""note
<!-- pr-auto:architecture-audit -->
PR-AUTO ARCHITECTURE AUDIT
head_sha: {HEAD_A}
disposition: VERIFIED
scope: canonical ingress closure
reviewed_at: 2026-09-25T12:05:00Z
"""
        rec = p.parse_architecture_audit_comment(text)
        self.assertIsNotNone(rec)
        self.assertEqual(rec.head_sha, HEAD_A)
        self.assertEqual(rec.disposition, "VERIFIED")

    def test_bad_marker_is_ignored(self):
        self.assertIsNone(p.parse_review_comment(
            "<!-- pr-auto:adversarial-review -->\nhead_sha: nope\ndisposition: VERIFIED"
        ))

    def test_current_high_risk_review_is_reused(self):
        pr = base_pr(
            change_domains=["persistence"],
            adversarial_review={"head_sha": HEAD_A, "disposition": "NO_BLOCKER_FOUND"},
        )
        self.assertEqual(p.adversarial_review_requirement(pr), "CURRENT")

    def test_high_risk_without_review_requires_full(self):
        self.assertEqual(
            p.adversarial_review_requirement(base_pr(change_domains=["native-boundary"])),
            "FULL",
        )

    def test_low_risk_change_does_not_force_adversarial_review(self):
        self.assertEqual(p.adversarial_review_requirement(base_pr()), "NONE")

    def test_explicit_user_request_forces_review_even_on_same_head(self):
        pr = base_pr(
            user_requested_adversarial=True,
            adversarial_review={"head_sha": HEAD_A, "disposition": "VERIFIED"},
        )
        self.assertEqual(p.adversarial_review_requirement(pr), "FULL")

    def test_stale_review_with_tiny_delta_uses_delta_review(self):
        pr = base_pr(
            head_sha=HEAD_B,
            change_domains=["persistence"],
            adversarial_review={"head_sha": HEAD_A, "disposition": "NO_BLOCKER_FOUND"},
            delta_domains=["tests-only"],
            delta_file_count=1,
            delta_changed_lines=8,
        )
        self.assertEqual(p.adversarial_review_requirement(pr), "DELTA")

    def test_stale_review_with_semantic_delta_requires_full_review_again(self):
        pr = base_pr(
            head_sha=HEAD_B,
            change_domains=["persistence"],
            adversarial_review={"head_sha": HEAD_A, "disposition": "NO_BLOCKER_FOUND"},
            delta_domains=["portable-semantics"],
            delta_file_count=2,
            delta_changed_lines=35,
        )
        self.assertEqual(p.adversarial_review_requirement(pr), "FULL")


class ArchitectureAuditTests(unittest.TestCase):
    def test_docs_do_not_require_architecture_audit(self):
        self.assertEqual(p.architecture_audit_requirement(base_pr()), "NONE")

    def test_transport_change_requires_full_architecture_audit(self):
        self.assertEqual(
            p.architecture_audit_requirement(base_pr(change_domains=["transport"])),
            "FULL",
        )

    def test_current_exact_head_architecture_audit_is_reused(self):
        pr = base_pr(
            change_domains=["transport"],
            architecture_audit={"head_sha": HEAD_A, "disposition": "NO_BLOCKER_FOUND"},
        )
        self.assertEqual(p.architecture_audit_requirement(pr), "CURRENT")

    def test_stale_architecture_audit_with_tiny_delta_uses_delta(self):
        pr = base_pr(
            head_sha=HEAD_B,
            change_domains=["transport"],
            architecture_audit={"head_sha": HEAD_A, "disposition": "VERIFIED"},
            delta_domains=["tests-only"],
            delta_file_count=1,
            delta_changed_lines=4,
        )
        self.assertEqual(p.architecture_audit_requirement(pr), "DELTA")

    def test_stale_architecture_audit_with_architectural_delta_requires_full(self):
        pr = base_pr(
            head_sha=HEAD_B,
            change_domains=["transport"],
            architecture_audit={"head_sha": HEAD_A, "disposition": "VERIFIED"},
            delta_domains=["client-parity"],
            delta_file_count=1,
            delta_changed_lines=4,
        )
        self.assertEqual(p.architecture_audit_requirement(pr), "FULL")

    def test_explicit_architecture_request_forces_full_even_on_same_head(self):
        pr = base_pr(
            change_domains=["transport"],
            user_requested_architecture_audit=True,
            architecture_audit={"head_sha": HEAD_A, "disposition": "VERIFIED"},
        )
        self.assertEqual(p.architecture_audit_requirement(pr), "FULL")


class FixForwardTests(unittest.TestCase):
    def test_bounded_defect_is_fixed_in_place(self):
        pr = base_pr(implementation_defect=True, bounded_fix=True)
        self.assertTrue(p.can_fix_in_place(pr))
        self.assertEqual(p.classify_pr(pr), "FIX_IMPLEMENTATION")

    def test_large_separate_repair_becomes_followup(self):
        pr = base_pr(implementation_defect=True, bounded_fix=True, separate_review_unit=True)
        self.assertFalse(p.can_fix_in_place(pr))
        self.assertEqual(p.classify_pr(pr), "FOLLOW_UP_REQUIRED")

    def test_other_worker_ownership_prevents_interference(self):
        pr = base_pr(implementation_defect=True, bounded_fix=True, owned_by_other_worker=True)
        self.assertEqual(p.classify_pr(pr), "ACTIVE_WORK")

    def test_conflict_is_resolved_before_ci_diagnosis(self):
        self.assertEqual(p.classify_pr(base_pr(conflicted=True, ci="red")), "RESOLVE_CONFLICT")

    def test_main_fix_is_preferred_over_reimplementing_red_ci_fix(self):
        pr = base_pr(ci="red", behind_main=4, main_likely_contains_fix=True)
        self.assertEqual(p.classify_pr(pr), "UPDATE_FROM_MAIN")

    def test_red_ci_routes_to_ci_fix_when_main_update_not_indicated(self):
        pr = base_pr(ci="red", behind_main=4, main_likely_contains_fix=False)
        self.assertEqual(p.classify_pr(pr), "FIX_CI")


class MergeGateTests(unittest.TestCase):
    def test_low_risk_green_reviewed_pr_can_merge(self):
        pr = base_pr()
        self.assertTrue(p.merge_eligible(pr))
        self.assertEqual(p.classify_pr(pr), "MERGE_NOW")

    def test_high_risk_green_pr_first_requires_adversarial_review(self):
        pr = base_pr(change_domains=["result-fidelity"])
        self.assertFalse(p.merge_eligible(pr))
        self.assertEqual(p.classify_pr(pr), "ADVERSARIAL_REVIEW_REQUIRED")

    def test_after_adversarial_review_high_risk_pr_requires_architecture_audit(self):
        pr = base_pr(
            change_domains=["result-fidelity"],
            adversarial_review={"head_sha": HEAD_A, "disposition": "NO_BLOCKER_FOUND"},
        )
        self.assertFalse(p.merge_eligible(pr))
        self.assertEqual(p.classify_pr(pr), "ARCHITECTURE_AUDIT_REQUIRED")

    def test_both_exact_head_gates_unlock_merge(self):
        pr = base_pr(
            change_domains=["schema-fidelity"],
            adversarial_review={"head_sha": HEAD_A, "disposition": "NO_BLOCKER_FOUND"},
            architecture_audit={"head_sha": HEAD_A, "disposition": "VERIFIED"},
        )
        self.assertTrue(p.merge_eligible(pr))
        self.assertEqual(p.classify_pr(pr), "MERGE_NOW")

    def test_medium_architecture_domain_requires_audit_without_adversarial(self):
        pr = base_pr(change_domains=["transport"])
        self.assertEqual(p.adversarial_review_requirement(pr), "NONE")
        self.assertFalse(p.merge_eligible(pr))
        self.assertEqual(p.classify_pr(pr), "ARCHITECTURE_AUDIT_REQUIRED")

    def test_just_merge_urgency_cannot_bypass_either_gate(self):
        pr = base_pr(change_domains=["concurrency"], user_merge_urgency=True)
        self.assertFalse(p.merge_eligible(pr))
        self.assertEqual(p.classify_pr(pr), "ADVERSARIAL_REVIEW_REQUIRED")
        pr["adversarial_review"] = {"head_sha": HEAD_A, "disposition": "VERIFIED"}
        self.assertEqual(p.classify_pr(pr), "ARCHITECTURE_AUDIT_REQUIRED")

    def test_old_reviews_never_unlock_new_head_directly(self):
        pr = base_pr(
            head_sha=HEAD_B,
            change_domains=["schema-fidelity"],
            adversarial_review={"head_sha": HEAD_A, "disposition": "NO_BLOCKER_FOUND"},
            architecture_audit={"head_sha": HEAD_A, "disposition": "VERIFIED"},
            delta_domains=["tests-only"],
        )
        self.assertFalse(p.merge_eligible(pr))
        self.assertEqual(p.classify_pr(pr), "ADVERSARIAL_REVIEW_REQUIRED")

    def test_incomplete_acceptance_blocks_merge(self):
        pr = base_pr(issue_acceptance_complete=False)
        self.assertFalse(p.merge_eligible(pr))
        self.assertEqual(p.classify_pr(pr), "FOLLOW_UP_REQUIRED")

    def test_pending_ci_waits_instead_of_pretending_green(self):
        pr = base_pr(ci="pending")
        self.assertFalse(p.merge_eligible(pr))
        self.assertEqual(p.classify_pr(pr), "WAITING")


class FleetLoopTests(unittest.TestCase):
    def test_plan_orders_safe_forward_actions_before_waiting(self):
        fleet = [
            base_pr(number=3, ci="pending"),
            base_pr(number=1),
            base_pr(number=2, ci="red"),
        ]
        plan = p.fleet_plan(fleet)
        self.assertEqual([x["state"] for x in plan], ["MERGE_NOW", "FIX_CI", "WAITING"])

    def test_plan_places_architecture_audit_after_adversarial_review(self):
        fleet = [
            base_pr(number=1, change_domains=["transport"]),
            base_pr(number=2, change_domains=["persistence"]),
        ]
        plan = p.fleet_plan(fleet)
        self.assertEqual(
            [x["state"] for x in plan],
            ["ADVERSARIAL_REVIEW_REQUIRED", "ARCHITECTURE_AUDIT_REQUIRED"],
        )

    def test_evaluation_exposes_both_review_gates(self):
        result = p.evaluate_pr(base_pr(change_domains=["transport"]))
        self.assertEqual(result["adversarial_review"], "NONE")
        self.assertEqual(result["architecture_audit"], "FULL")

    def test_fleet_not_at_fixed_point_when_any_safe_action_exists(self):
        self.assertFalse(p.at_fixed_point([base_pr(ci="pending"), base_pr(number=2)]))

    def test_fleet_fixed_point_when_only_active_or_external_waits_remain(self):
        fleet = [
            base_pr(active_work=True),
            base_pr(number=2, external_blocker=True),
            base_pr(number=3, ci="pending"),
        ]
        self.assertTrue(p.at_fixed_point(fleet))

    def test_status_mode_is_read_only_but_auto_mode_can_mutate(self):
        self.assertFalse(p.mutation_allowed("status"))
        self.assertFalse(p.mutation_allowed("inspect"))
        self.assertTrue(p.mutation_allowed("auto"))
        self.assertTrue(p.mutation_allowed("pr auto"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
