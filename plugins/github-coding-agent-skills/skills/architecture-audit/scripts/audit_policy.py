#!/usr/bin/env python3
"""Deterministic negative-conclusion gate for architecture audits."""
from __future__ import annotations
import argparse
import json
import sys

REQUIRED_EVIDENCE = (
    "implementation_delta",
    "contract",
    "execution_path",
    "independent_oracle",
    "layer_disagreement",
    "negative_boundary_cases",
    "false_green",
    "capability_claims",
    "fallbacks",
    "recorded_evidence",
)


def evaluate(payload: dict) -> dict:
    blockers = payload.get("blockers") or []
    if blockers:
        return {"disposition": "BLOCKED", "missing_evidence": [], "blocker_count": len(blockers)}

    if payload.get("depth", "adversarial") != "adversarial":
        return {"disposition": "UNVERIFIED", "missing_evidence": ["adversarial_depth"], "blocker_count": 0}

    evidence = payload.get("evidence") or {}
    missing = [key for key in REQUIRED_EVIDENCE if not evidence.get(key, False)]
    if missing:
        return {"disposition": "UNVERIFIED", "missing_evidence": missing, "blocker_count": 0}

    return {"disposition": "NO_BLOCKER_FOUND", "missing_evidence": [], "blocker_count": 0}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", help="JSON file; stdin when omitted")
    args = parser.parse_args()
    data = json.load(open(args.input)) if args.input else json.load(sys.stdin)
    json.dump(evaluate(data), sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
