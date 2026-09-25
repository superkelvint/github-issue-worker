#!/usr/bin/env python3
from __future__ import annotations

from typing import Any, Iterable, Mapping

import control_plane_policy as cp

NEEDS = "status:needs-followup"
IN_PROGRESS = "status:in-progress"


def status_labels(issue: Mapping[str, Any]) -> set[str]:
    return {str(x) for x in issue.get("status_labels") or []}


def eligible(issue: Mapping[str, Any]) -> bool:
    labels = status_labels(issue)
    return all([
        bool(issue.get("open", True)),
        labels == {NEEDS},
        int(issue.get("open_pr_count") or 0) == 1,
        bool(issue.get("followup_specific", True)),
        not bool(issue.get("pr_needs_cto_review")),
    ])


def claim_transition_valid(before: Mapping[str, Any], after: Mapping[str, Any]) -> bool:
    return status_labels(before) == {NEEDS} and status_labels(after) == {IN_PROGRESS}


def exact_head_current(work: Mapping[str, Any]) -> bool:
    return cp.exact_head_evidence_current(
        {
            "head_sha": work.get("head_sha"),
            "verification": {"head_sha": work.get("tested_head")},
        },
        "verification",
    )


def handoff_allowed(work: Mapping[str, Any]) -> bool:
    return all([
        bool(work.get("pr_open", True)),
        bool(work.get("claimed")),
        bool(work.get("verification_complete")),
        bool(work.get("verification_passed")),
        exact_head_current(work),
        not bool(work.get("required_check_failing")),
        not bool(work.get("concurrent_change")),
    ])


def classify(issue: Mapping[str, Any], work: Mapping[str, Any] | None = None) -> str:
    if not eligible(issue):
        return "NO_ELIGIBLE_ISSUE"
    if work is None or not bool(work.get("claimed")):
        return "CLAIM"
    if bool(work.get("invalid_followup")):
        return "RELEASE"
    if bool(work.get("environment_failure")) and bool(work.get("environment_recovery_available")):
        return "REMEDIATE_ENV"
    if work.get("tested_head") and not exact_head_current(work):
        return "RESTART_HEAD_CHANGED"
    if bool(work.get("code_change_required")) and not bool(work.get("head_writable", True)):
        return "BLOCKED"
    if handoff_allowed(work):
        return "HANDOFF"
    if bool(work.get("verification_complete")) and not bool(work.get("verification_passed")):
        return "BLOCKED"
    return "WORK"


def queue(issues: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [issue for issue in issues if eligible(issue)]
