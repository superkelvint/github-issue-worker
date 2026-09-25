import unittest
from reconcile_policy import classify


class ReconcilePolicyTests(unittest.TestCase):
    def test_closed_issue_with_state_removes_only_state(self):
        result = classify({"state": "closed", "labels": ["status:ready", "priority:p1"]})
        self.assertEqual(result["anomalies"], ["CLOSED_WITH_STATE"])
        self.assertEqual(result["actions"], ["REMOVE_WORKFLOW_STATE_LABELS"])

    def test_open_issue_without_state_requires_classification(self):
        result = classify({"state": "open", "labels": ["priority:p1"]})
        self.assertIn("MISSING_STATE", result["anomalies"])
        self.assertIn("NEEDS_CLASSIFICATION", result["actions"])

    def test_ready_with_claim_is_not_auto_reclassified(self):
        result = classify({"state": "open", "labels": ["status:ready", "priority:p1"], "claim_branch": True})
        self.assertIn("READY_WITH_CLAIM", result["anomalies"])
        self.assertIn("INVESTIGATE_CLAIM", result["actions"])
        self.assertNotIn("MOVE_TO_IN_PROGRESS", result["actions"])

    def test_in_progress_without_claim_requires_ownership_investigation(self):
        result = classify({"state": "open", "labels": ["status:in-progress", "priority:p2"], "claim_branch": False})
        self.assertIn("IN_PROGRESS_WITHOUT_CLAIM", result["anomalies"])
        self.assertIn("INVESTIGATE_OWNERSHIP", result["actions"])

    def test_resolved_on_default_requires_both_acceptance_and_reachability(self):
        base = {"state": "open", "labels": ["status:ready", "priority:p1"]}
        self.assertNotIn("RESOLVED_ON_DEFAULT", classify({**base, "acceptance_satisfied_on_default": True})["anomalies"])
        result = classify({**base, "acceptance_satisfied_on_default": True, "resolution_reachable_from_default": True})
        self.assertIn("RESOLVED_ON_DEFAULT", result["anomalies"])
        self.assertIn("CLOSE_WITH_EVIDENCE", result["actions"])

    def test_satisfied_blocker_can_be_released_only_conditionally(self):
        result = classify({"state": "open", "labels": ["status:blocked", "priority:p1"], "blocker_satisfied": True})
        self.assertIn("BLOCKER_SATISFIED", result["anomalies"])
        self.assertIn("MOVE_TO_READY_IF_UNCLAIMED", result["actions"])

    def test_multiple_states_are_never_guessed(self):
        result = classify({"state": "open", "labels": ["status:ready", "status:blocked", "priority:p1"]})
        self.assertIn("MULTIPLE_STATES", result["anomalies"])
        self.assertIn("NEEDS_CLASSIFICATION", result["actions"])


if __name__ == "__main__":
    unittest.main()
