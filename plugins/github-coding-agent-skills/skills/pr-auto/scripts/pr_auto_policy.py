#!/usr/bin/env python3
"""Deterministic policy helper for the PR Auto skill.

This helper does not replace repository rules or CTO judgment. It normalizes the
repeatable parts of PR fleet management so review attention stays on real code,
not on re-deriving the state machine.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

HIGH_RISK_DOMAINS = {
    "lifecycle", "concurrency", "portable-semantics", "canonical-semantics",
    "schema-fidelity", "persistence", "reopen", "result-fidelity",
    "native-boundary", "protocol", "architecture", "security", "verifier",
    "frozen-contract", "error-domain",
}
MEDIUM_RISK_DOMAINS = {
    "transport", "ranking", "query-lowering", "ci-selector", "build-tooling",
    "generated-artifacts", "client-core", "packaging",
}
BEHAVIORAL_DOMAINS = HIGH_RISK_DOMAINS | MEDIUM_RISK_DOMAINS

# Mirror Issue Fixer's architecture-audit triggers. A PR may require this gate
# even when it does not require a heavyweight adversarial review (for example,
# a transport or CI-selector change that can alter cross-layer coverage).
ARCHITECTURE_AUDIT_DOMAINS = {
    "lifecycle", "concurrency", "shutdown", "ownership",
    "portable-semantics", "canonical-semantics", "query-lowering", "ranking",
    "schema-fidelity", "protocol", "generated-artifacts",
    "persistence", "reopen", "migration",
    "native-boundary", "ffi", "abi", "error-domain",
    "result-fidelity", "grouping", "sorting", "response-semantics",
    "transport", "daemon", "client-core", "client-parity",
    "ci-selector", "verification-architecture", "acceptance-harness", "verifier",
    "architecture", "security", "trust-boundary", "frozen-contract",
}

ACTION_PRIORITY = {
    "MERGE_NOW": 10,
    "UPDATE_FROM_MAIN": 20,
    "FIX_CI": 30,
    "RESOLVE_CONFLICT": 40,
    "FIX_IMPLEMENTATION": 50,
    "REVIEW_NOW": 60,
    "ADVERSARIAL_REVIEW_REQUIRED": 70,
    "ARCHITECTURE_AUDIT_REQUIRED": 75,
    "FOLLOW_UP_REQUIRED": 80,
    "STALE_OR_SUPERSEDED": 90,
    "ACTIVE_WORK": 100,
    "WAITING": 110,
}
ACTIONABLE_STATES = {
    "MERGE_NOW", "UPDATE_FROM_MAIN", "FIX_CI", "RESOLVE_CONFLICT",
    "FIX_IMPLEMENTATION", "REVIEW_NOW", "ADVERSARIAL_REVIEW_REQUIRED",
    "ARCHITECTURE_AUDIT_REQUIRED", "FOLLOW_UP_REQUIRED",
    "STALE_OR_SUPERSEDED",
}

_ADVERSARIAL_MARKER = "<!-- pr-auto:adversarial-review -->"
_ARCHITECTURE_MARKER = "<!-- pr-auto:architecture-audit -->"
_FIELD_RE = re.compile(r"^(head_sha|disposition|scope|reviewed_at):\s*(.+?)\s*$", re.M)
_VALID_DISPOSITIONS = {"NO_BLOCKER_FOUND", "CHANGES_REQUIRED", "VERIFIED"}


@dataclass(frozen=True)
class ReviewRecord:
    head_sha: str
    disposition: str
    scope: str = ""
    reviewed_at: str = ""


def _domains(pr: Mapping[str, Any], key: str = "change_domains") -> set[str]:
    raw = pr.get(key) or []
    return {str(item).strip().lower() for item in raw if str(item).strip()}


def _int(pr: Mapping[str, Any], key: str) -> int:
    try:
        return int(pr.get(key) or 0)
    except (TypeError, ValueError):
        return 0


def blast_radius(pr: Mapping[str, Any], *, delta: bool = False) -> str:
    """Return LOW, MEDIUM, or HIGH for the normalized PR record."""
    domains = _domains(pr, "delta_domains" if delta else "change_domains")
    file_key = "delta_file_count" if delta else "changed_file_count"
    line_key = "delta_changed_lines" if delta else "changed_lines"
    file_count = _int(pr, file_key)
    changed_lines = _int(pr, line_key)

    if bool(pr.get("policy_requires_adversarial")) and not delta:
        return "HIGH"
    if domains & HIGH_RISK_DOMAINS:
        return "HIGH"
    if len(domains & BEHAVIORAL_DOMAINS) >= 3 or file_count >= 20 or changed_lines >= 800:
        return "HIGH"
    if domains & MEDIUM_RISK_DOMAINS or file_count >= 8 or changed_lines >= 300:
        return "MEDIUM"
    return "LOW"


def _parse_gate_comment(text: str, marker: str) -> ReviewRecord | None:
    if marker not in text:
        return None
    values = {name: value for name, value in _FIELD_RE.findall(text)}
    head = values.get("head_sha", "").strip()
    disposition = values.get("disposition", "").strip().upper()
    if len(head) != 40 or not re.fullmatch(r"[0-9a-fA-F]{40}", head):
        return None
    if disposition not in _VALID_DISPOSITIONS:
        return None
    return ReviewRecord(
        head_sha=head.lower(),
        disposition=disposition,
        scope=values.get("scope", "").strip(),
        reviewed_at=values.get("reviewed_at", "").strip(),
    )


def parse_review_comment(text: str) -> ReviewRecord | None:
    return _parse_gate_comment(text, _ADVERSARIAL_MARKER)


def parse_architecture_audit_comment(text: str) -> ReviewRecord | None:
    return _parse_gate_comment(text, _ARCHITECTURE_MARKER)


def latest_review_record(comments: Iterable[str]) -> ReviewRecord | None:
    latest = None
    for comment in comments:
        parsed = parse_review_comment(comment)
        if parsed is not None:
            latest = parsed
    return latest


def latest_architecture_audit_record(comments: Iterable[str]) -> ReviewRecord | None:
    latest = None
    for comment in comments:
        parsed = parse_architecture_audit_comment(comment)
        if parsed is not None:
            latest = parsed
    return latest


def adversarial_review_requirement(pr: Mapping[str, Any]) -> str:
    """Return NONE, CURRENT, DELTA, or FULL."""
    requires = bool(pr.get("policy_requires_adversarial")) or blast_radius(pr) == "HIGH"
    delta_domains = _domains(pr, "delta_domains")
    delta_reopens = (
        blast_radius(pr, delta=True) == "HIGH"
        or bool(delta_domains & HIGH_RISK_DOMAINS)
        or bool(pr.get("delta_changes_semantics"))
    )
    return cp.review_requirement(
        pr,
        required=requires,
        evidence_key="adversarial_review",
        user_requested=bool(pr.get("user_requested_adversarial")),
        delta_reopens=delta_reopens,
    )


def architecture_audit_requirement(pr: Mapping[str, Any]) -> str:
    """Return NONE, CURRENT, DELTA, or FULL for the architecture-audit gate."""
    domains = _domains(pr)
    requires = bool(pr.get("policy_requires_architecture_audit")) or bool(
        domains & ARCHITECTURE_AUDIT_DOMAINS
    )
    delta_domains = _domains(pr, "delta_domains")
    delta_reopens = (
        bool(pr.get("delta_reopens_architecture"))
        or bool(delta_domains & ARCHITECTURE_AUDIT_DOMAINS)
        or blast_radius(pr, delta=True) == "HIGH"
    )
    return cp.review_requirement(
        pr,
        required=requires,
        evidence_key="architecture_audit",
        user_requested=bool(pr.get("user_requested_architecture_audit")),
        delta_reopens=delta_reopens,
    )


def can_fix_in_place(pr: Mapping[str, Any]) -> bool:
    return all([
        bool(pr.get("bounded_fix")),
        not bool(pr.get("separate_review_unit")),
        not bool(pr.get("owned_by_other_worker")),
        not bool(pr.get("decision_required")),
        bool(pr.get("verification_available", True)),
    ])


def _gate_allows_merge(requirement: str, record: Mapping[str, Any]) -> bool:
    if requirement not in {"NONE", "CURRENT"}:
        return False
    if requirement == "CURRENT" and str(record.get("disposition") or "").upper() == "CHANGES_REQUIRED":
        return False
    return True


def merge_eligible(pr: Mapping[str, Any]) -> bool:
    shared = dict(pr)
    shared["required_checks_green"] = (
        str(pr.get("ci") or "").lower() == "green"
        and bool(pr.get("required_checks_complete", True))
    )
    shared["checks_head_sha"] = pr.get("checks_head_sha") or pr.get("head_sha")
    shared["acceptance_complete"] = bool(pr.get("issue_acceptance_complete", True))
    shared["ordinary_review_complete"] = bool(pr.get("ordinary_review_complete", False))
    shared["adversarial_review_required"] = adversarial_review_requirement(pr) != "NONE"
    shared["architecture_audit_required"] = architecture_audit_requirement(pr) != "NONE"
    return cp.merge_eligible(shared)


def classify_pr(pr: Mapping[str, Any]) -> str:
    if bool(pr.get("active_work")) or bool(pr.get("owned_by_other_worker")):
        return "ACTIVE_WORK"
    if bool(pr.get("external_blocker")):
        return "WAITING"
    if bool(pr.get("stale_or_superseded")):
        return "STALE_OR_SUPERSEDED"
    if bool(pr.get("conflicted")):
        return "RESOLVE_CONFLICT"

    if _int(pr, "behind_main") > 0 and bool(pr.get("main_likely_contains_fix")):
        return "UPDATE_FROM_MAIN"

    ci = str(pr.get("ci") or "unknown").lower()
    if ci == "red":
        return "FIX_CI"

    if bool(pr.get("implementation_defect")):
        return "FIX_IMPLEMENTATION" if can_fix_in_place(pr) else "FOLLOW_UP_REQUIRED"

    if not bool(pr.get("issue_acceptance_complete", True)):
        return "FOLLOW_UP_REQUIRED"

    if ci in {"pending", "queued", "running"}:
        return "WAITING"

    if adversarial_review_requirement(pr) in {"FULL", "DELTA"}:
        return "ADVERSARIAL_REVIEW_REQUIRED"

    if architecture_audit_requirement(pr) in {"FULL", "DELTA"}:
        return "ARCHITECTURE_AUDIT_REQUIRED"

    if bool(pr.get("ready_for_review")) and not bool(pr.get("ordinary_review_complete", False)):
        return "REVIEW_NOW"

    if merge_eligible(pr):
        return "MERGE_NOW"

    return "WAITING"


def evaluate_pr(pr: Mapping[str, Any]) -> dict[str, Any]:
    state = classify_pr(pr)
    return {
        "number": pr.get("number"),
        "head_sha": pr.get("head_sha"),
        "state": state,
        "blast_radius": blast_radius(pr),
        "adversarial_review": adversarial_review_requirement(pr),
        "architecture_audit": architecture_audit_requirement(pr),
        "merge_eligible": merge_eligible(pr),
        "fix_in_place": can_fix_in_place(pr) if pr.get("implementation_defect") else None,
        "actionable": state in ACTIONABLE_STATES,
    }


def fleet_plan(prs: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    evaluated = [evaluate_pr(pr) for pr in prs]
    return sorted(evaluated, key=lambda item: (ACTION_PRIORITY[item["state"]], item.get("number") or 0))


def at_fixed_point(prs: Iterable[Mapping[str, Any]]) -> bool:
    return not any(evaluate_pr(pr)["actionable"] for pr in prs)


def mutation_allowed(mode: str) -> bool:
    return mode.strip().lower() not in {"status", "read-only", "readonly", "inspect"}


def _main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate normalized PR Auto fleet JSON")
    parser.add_argument("path", nargs="?", help="JSON file containing a PR object or list; stdin if omitted")
    args = parser.parse_args()
    if args.path:
        with open(args.path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    else:
        data = json.load(__import__("sys").stdin)

    if isinstance(data, list):
        output: Any = {"fixed_point": at_fixed_point(data), "plan": fleet_plan(data)}
    elif isinstance(data, dict):
        output = evaluate_pr(data)
    else:
        raise SystemExit("input must be a JSON object or list")

    json.dump(output, __import__("sys").stdout, indent=2, sort_keys=True)
    __import__("sys").stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
