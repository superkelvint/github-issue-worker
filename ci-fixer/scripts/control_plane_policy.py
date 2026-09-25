#!/usr/bin/env python3
"""Shared deterministic closure policy for GitHub coding-agent skills."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

VALID_REVIEW_DISPOSITIONS = {"NO_BLOCKER_FOUND", "VERIFIED"}

@dataclass(frozen=True)
class Authority:
    update_from_main: bool = False
    diagnose_ci: bool = False
    fix_implementation: bool = False
    ordinary_review: bool = False
    adversarial_review: bool = False
    architecture_audit: bool = False
    merge: bool = False
    reconcile_issue: bool = False
    propagate_shared_fix: bool = False
    handoff: bool = False

ROLE_AUTHORITIES = {
    "issue": Authority(fix_implementation=True, handoff=True),
    "issue-followup": Authority(fix_implementation=True, handoff=True),
    "ci-fixer-inspect": Authority(),
    "ci-fixer-repair": Authority(update_from_main=True, diagnose_ci=True, fix_implementation=True),
    "ci-fixer-closure": Authority(update_from_main=True, diagnose_ci=True, fix_implementation=True, ordinary_review=True, adversarial_review=True, architecture_audit=True, merge=True, reconcile_issue=True),
    "issue-fixer": Authority(update_from_main=True, diagnose_ci=True, fix_implementation=True, ordinary_review=True, adversarial_review=True, architecture_audit=True, merge=True, reconcile_issue=True),
    "pr-auto": Authority(update_from_main=True, diagnose_ci=True, fix_implementation=True, ordinary_review=True, adversarial_review=True, architecture_audit=True, merge=True, reconcile_issue=True, propagate_shared_fix=True),
}

def authority_for(role: str) -> Authority:
    try:
        return ROLE_AUTHORITIES[role.strip().lower()]
    except KeyError as exc:
        raise ValueError(f"unknown workflow role: {role}") from exc

def _str(state: Mapping[str, Any], key: str) -> str:
    return str(state.get(key) or "").strip()

def exact_head_evidence_current(state: Mapping[str, Any], evidence_key: str) -> bool:
    head = _str(state, "head_sha").lower()
    evidence = state.get(evidence_key) or {}
    evidence_head = str(evidence.get("head_sha") or "").strip().lower()
    return bool(head) and evidence_head == head

def gate_current(state: Mapping[str, Any], evidence_key: str) -> bool:
    evidence = state.get(evidence_key) or {}
    disposition = str(evidence.get("disposition") or "").strip().upper()
    return exact_head_evidence_current(state, evidence_key) and disposition in VALID_REVIEW_DISPOSITIONS

def review_requirement(state: Mapping[str, Any], *, required: bool, evidence_key: str, user_requested: bool = False, delta_reopens: bool = False) -> str:
    if user_requested:
        return "FULL"
    if not required:
        return "NONE"
    if gate_current(state, evidence_key):
        return "CURRENT"
    evidence = state.get(evidence_key) or {}
    if not str(evidence.get("head_sha") or "").strip():
        return "FULL"
    return "FULL" if delta_reopens else "DELTA"

def base_update_required(state: Mapping[str, Any]) -> bool:
    return bool(state.get("behind_main")) and bool(state.get("main_contains_relevant_fix") or state.get("main_likely_contains_fix"))

def checks_current_and_green(state: Mapping[str, Any]) -> bool:
    if not bool(state.get("required_checks_green")):
        return False
    if bool(state.get("head_moved_after_checks")):
        return False
    return bool(_str(state, "head_sha")) and _str(state, "checks_head_sha") == _str(state, "head_sha")

def merge_eligible(state: Mapping[str, Any]) -> bool:
    if not bool(state.get("merge_evidence_complete")):
        return False
    if bool(state.get("draft")) or bool(state.get("conflicted")):
        return False
    if not bool(state.get("mergeable", True)) or base_update_required(state):
        return False
    if not checks_current_and_green(state):
        return False
    if not bool(state.get("acceptance_complete", state.get("issue_acceptance_complete", True))):
        return False
    if not bool(state.get("ordinary_review_complete", state.get("required_review_complete", False))):
        return False
    if bool(state.get("unresolved_review_feedback")):
        return False
    for key, required_key in (("adversarial_review", "adversarial_review_required"), ("architecture_audit", "architecture_audit_required")):
        if bool(state.get(required_key)) and not gate_current(state, key):
            return False
    return True

def post_merge_reconciled(state: Mapping[str, Any]) -> bool:
    if not bool(state.get("merged")):
        return False
    if not bool(state.get("reconciliation_evidence_complete")):
        return False
    return all([
        bool(state.get("merge_reachable_from_main")),
        bool(state.get("linked_issue_state_correct")),
        bool(state.get("acceptance_complete", state.get("issue_acceptance_complete"))),
        state.get("stale_labels_or_duplicate_work") is False,
    ])

def propagation_required(state: Mapping[str, Any]) -> bool:
    return all([bool(state.get("shared_fix_landed")), bool(state.get("affected_sibling_prs")), not bool(state.get("propagation_complete"))])

def _review_action(prefix: str, requirement: str) -> str | None:
    if requirement == "FULL":
        return f"FULL_{prefix}"
    if requirement == "DELTA":
        return f"DELTA_{prefix}"
    return None

def _dedupe(actions: Iterable[str]) -> list[str]:
    out = []
    seen = set()
    for action in actions:
        if action not in seen:
            seen.add(action)
            out.append(action)
    return out

def required_actions(state: Mapping[str, Any], authority: Authority) -> list[str]:
    actions = []
    if bool(state.get("external_blocker")):
        return ["WAIT_EXTERNAL"]
    if base_update_required(state):
        actions.append("UPDATE_FROM_MAIN")
    if bool(state.get("ci_red")):
        actions.append("DIAGNOSE_CI")
    elif bool(state.get("checks_pending")):
        actions.append("WAIT_CHECKS")
    if bool(state.get("implementation_defect")):
        actions.append("FIX_IMPLEMENTATION")
    if bool(state.get("ready_for_review")) and not bool(state.get("ordinary_review_complete", False)):
        actions.append("NORMAL_REVIEW")
    adv = review_requirement(state, required=bool(state.get("adversarial_review_required")), evidence_key="adversarial_review", user_requested=bool(state.get("user_requested_adversarial")), delta_reopens=bool(state.get("adversarial_delta_reopens")))
    action = _review_action("ADVERSARIAL_REVIEW", adv)
    if action:
        actions.append(action)
    arch = review_requirement(state, required=bool(state.get("architecture_audit_required")), evidence_key="architecture_audit", user_requested=bool(state.get("user_requested_architecture_audit")), delta_reopens=bool(state.get("architecture_delta_reopens")))
    action = _review_action("ARCHITECTURE_AUDIT", arch)
    if action:
        actions.append(action)
    if bool(state.get("merged")):
        if not post_merge_reconciled(state):
            actions.append("RECONCILE_ISSUE")
        if propagation_required(state):
            actions.append("PROPAGATE_SHARED_FIX")
        return _dedupe(actions)
    if not actions:
        if bool(state.get("handoff_ready")):
            actions.append("HANDOFF")
        elif merge_eligible(state):
            actions.append("MERGE")
    return _dedupe(actions)

def action_owned(action: str, authority: Authority) -> bool:
    return bool({"UPDATE_FROM_MAIN": authority.update_from_main, "DIAGNOSE_CI": authority.diagnose_ci, "WAIT_CHECKS": False, "FIX_IMPLEMENTATION": authority.fix_implementation, "NORMAL_REVIEW": authority.ordinary_review, "FULL_ADVERSARIAL_REVIEW": authority.adversarial_review, "DELTA_ADVERSARIAL_REVIEW": authority.adversarial_review, "FULL_ARCHITECTURE_AUDIT": authority.architecture_audit, "DELTA_ARCHITECTURE_AUDIT": authority.architecture_audit, "MERGE": authority.merge, "RECONCILE_ISSUE": authority.reconcile_issue, "PROPAGATE_SHARED_FIX": authority.propagate_shared_fix, "HANDOFF": authority.handoff, "WAIT_EXTERNAL": False}.get(action, False))

def evaluate(state: Mapping[str, Any], authority: Authority) -> dict[str, Any]:
    actions = required_actions(state, authority)
    owned = [action for action in actions if action_owned(action, authority)]
    unowned = [action for action in actions if not action_owned(action, authority)]
    return {"disposition": "COMPLETE" if not actions else ("ACTION_REQUIRED" if owned else "HANDOFF_OR_WAIT"), "actions": actions, "owned_actions": owned, "unowned_actions": unowned, "terminal_for_workflow": not owned, "merge_eligible": merge_eligible(state), "post_merge_reconciled": post_merge_reconciled(state) if state.get("merged") else None}

def _main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate shared GitHub workflow closure policy")
    parser.add_argument("role", choices=sorted(ROLE_AUTHORITIES))
    parser.add_argument("path", nargs="?", help="normalized JSON state; stdin when omitted")
    args = parser.parse_args()
    if args.path:
        with open(args.path, "r", encoding="utf-8") as handle:
            state = json.load(handle)
    else:
        state = json.load(__import__("sys").stdin)
    json.dump(evaluate(state, authority_for(args.role)), __import__("sys").stdout, indent=2, sort_keys=True)
    __import__("sys").stdout.write("\n")
    return 0

if __name__ == "__main__":
    raise SystemExit(_main())
