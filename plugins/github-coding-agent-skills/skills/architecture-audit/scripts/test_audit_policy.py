import unittest
from audit_policy import REQUIRED_EVIDENCE, evaluate


def full_evidence():
    return {key: True for key in REQUIRED_EVIDENCE}


class AuditPolicyTests(unittest.TestCase):
    def test_blocker_wins_even_with_complete_evidence(self):
        result = evaluate({"blockers": ["semantic bypass"], "evidence": full_evidence()})
        self.assertEqual(result["disposition"], "BLOCKED")

    def test_triage_cannot_produce_clean_conclusion(self):
        result = evaluate({"depth": "triage", "evidence": full_evidence()})
        self.assertEqual(result["disposition"], "UNVERIFIED")
        self.assertIn("adversarial_depth", result["missing_evidence"])

    def test_missing_oracle_prevents_no_blocker_found(self):
        evidence = full_evidence()
        evidence["independent_oracle"] = False
        result = evaluate({"depth": "adversarial", "evidence": evidence})
        self.assertEqual(result["disposition"], "UNVERIFIED")
        self.assertEqual(result["missing_evidence"], ["independent_oracle"])

    def test_complete_adversarial_evidence_allows_no_blocker_found(self):
        result = evaluate({"depth": "adversarial", "evidence": full_evidence()})
        self.assertEqual(result["disposition"], "NO_BLOCKER_FOUND")

    def test_policy_never_claims_verified(self):
        for payload in (
            {"blockers": ["x"], "evidence": full_evidence()},
            {"depth": "triage", "evidence": full_evidence()},
            {"depth": "adversarial", "evidence": full_evidence()},
        ):
            self.assertNotEqual(evaluate(payload)["disposition"], "VERIFIED")


if __name__ == "__main__":
    unittest.main()
