#!/usr/bin/env python3
"""Deterministic structural classifier for issue-queue reconciliation."""
from __future__ import annotations
import argparse
import json
import sys

CANONICAL_STATES = {
    "status:ready",
    "status:in-progress",
    "status:blocked",
    "status:needs-followup",
}


def classify(issue: dict) -> dict:
    labels = set(issue.get("labels") or [])
    states = sorted(labels & CANONICAL_STATES)
    is_open = issue.get("state", "open") == "open"
    claim = bool(issue.get("claim_branch"))
    acceptance = bool(issue.get("acceptance_satisfied_on_default"))
    reachable = bool(issue.get("resolution_reachable_from_default"))
    blocker_satisfied = bool(issue.get("blocker_satisfied"))
    duplicate_of = issue.get("duplicate_of")
    priority = sorted(label for label in labels if label.startswith("priority:"))

    anomalies = []
    actions = []

    if not is_open:
        if states:
            anomalies.append("CLOSED_WITH_STATE")
            actions.append("REMOVE_WORKFLOW_STATE_LABELS")
        return {"anomalies": anomalies, "actions": actions}

    if not states:
        anomalies.append("MISSING_STATE")
        actions.append("NEEDS_CLASSIFICATION")
    elif len(states) > 1:
        anomalies.append("MULTIPLE_STATES")
        actions.append("NEEDS_CLASSIFICATION")

    state = states[0] if len(states) == 1 else None
    if state == "status:ready" and claim:
        anomalies.append("READY_WITH_CLAIM")
        actions.append("INVESTIGATE_CLAIM")
    if state == "status:in-progress" and not claim:
        anomalies.append("IN_PROGRESS_WITHOUT_CLAIM")
        actions.append("INVESTIGATE_OWNERSHIP")
    if state == "status:blocked" and blocker_satisfied:
        anomalies.append("BLOCKER_SATISFIED")
        actions.append("MOVE_TO_READY_IF_UNCLAIMED")

    if acceptance and reachable:
        anomalies.append("RESOLVED_ON_DEFAULT")
        actions.append("CLOSE_WITH_EVIDENCE")

    if duplicate_of:
        anomalies.append("DUPLICATE_OR_SUPERSEDED")
        actions.append("CLOSE_DUPLICATE_IF_CANONICAL_ISSUE_VALID")

    if not priority:
        anomalies.append("MISSING_PRIORITY")
        actions.append("CLASSIFY_PRIORITY")

    return {"anomalies": anomalies, "actions": actions}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", help="JSON file or stdin; accepts one issue or an array")
    args = parser.parse_args()
    data = json.load(open(args.input)) if args.input else json.load(sys.stdin)
    if isinstance(data, list):
        out = [dict(issue_number=item.get("number"), **classify(item)) for item in data]
    else:
        out = classify(data)
    json.dump(out, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
