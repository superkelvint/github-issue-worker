#!/usr/bin/env python3
from __future__ import annotations

from typing import Any, Iterable, Mapping

TERMINAL_SUCCESS = {"success", "neutral"}
PENDING = {"queued", "in_progress", "pending", "waiting", "requested"}


def is_draft_candidate(pr: Mapping[str, Any]) -> bool:
    return bool(pr.get("open", True)) and bool(pr.get("draft"))


def exact_head_current(pr: Mapping[str, Any]) -> bool:
    tested = str(pr.get("tested_head") or "")
    current = str(pr.get("head_sha") or "")
    return bool(tested) and tested == current


def required_checks_state(pr: Mapping[str, Any]) -> str:
    checks = list(pr.get("required_checks") or [])
    if not checks:
        return "PASS" if bool(pr.get("required_checks_not_applicable", True)) else "UNKNOWN"
    conclusions = {str(c).lower() for c in checks}
    if conclusions & PENDING:
        return "PENDING"
    if all(c in TERMINAL_SUCCESS for c in conclusions):
        return "PASS"
    return "FAIL"


def repair_allowed(pr: Mapping[str, Any]) -> bool:
    return all([
        is_draft_candidate(pr),
        bool(pr.get("head_writable")),
        exact_head_current(pr),
        bool(pr.get("repair_in_scope")),
        not bool(pr.get("contract_change_required")),
        not bool(pr.get("concurrent_change")),
        bool(pr.get("prepush_verification_passed")),
    ])


def ready_allowed(pr: Mapping[str, Any]) -> bool:
    return all([
        is_draft_candidate(pr),
        exact_head_current(pr),
        bool(pr.get("local_verification_passed")),
        required_checks_state(pr) == "PASS",
        not bool(pr.get("unresolved_verification_failure")),
        not bool(pr.get("concurrent_change")),
    ])


def classify(pr: Mapping[str, Any]) -> str:
    if not is_draft_candidate(pr):
        return "IGNORE"
    if bool(pr.get("environment_recovery_available")) and bool(pr.get("environment_failure")):
        return "REMEDIATE_ENV"
    if pr.get("tested_head") and not exact_head_current(pr):
        return "RESTART_HEAD_CHANGED"
    check_state = required_checks_state(pr)
    if check_state == "PENDING":
        return "DRAFT_BLOCKED"
    if bool(pr.get("verification_failed")) or check_state == "FAIL":
        return "REPAIR" if repair_allowed(pr) else "DRAFT_FAILED"
    if ready_allowed(pr):
        return "READY"
    return "DRAFT_BLOCKED"


def queue(prs: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [pr for pr in prs if is_draft_candidate(pr)]
