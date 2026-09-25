#!/usr/bin/env python3
from __future__ import annotations

from typing import Any, Iterable, Mapping

import control_plane_policy as cp

FAIL_STATES = {"failure", "failed", "timed_out", "action_required", "cancelled"}


def classify_failure(ctx: Mapping[str, Any]) -> str:
    if bool(ctx.get("behind_main")) and bool(ctx.get("main_contains_plausible_fix")):
        return "STALE_PR_OR_FIXED_ON_MAIN"
    if bool(ctx.get("unrelated_lane_selected")) or bool(ctx.get("required_lane_missing")):
        return "WORKFLOW_SELECTION_OR_FANOUT"
    if bool(ctx.get("runner_problem")) or bool(ctx.get("toolchain_problem")) or bool(ctx.get("container_problem")):
        return "RUNNER_TOOLCHAIN_OR_CONTAINER"
    if bool(ctx.get("generated_drift")):
        return "GENERATED_ARTIFACT_DRIFT"
    if bool(ctx.get("native_build_or_link_failure")):
        return "BUILD_LINK_NATIVE_SDK"
    if bool(ctx.get("test_harness_defect")):
        return "TEST_OR_HARNESS_DEFECT"
    if bool(ctx.get("product_regression")):
        return "PRODUCT_REGRESSION"
    if bool(ctx.get("review_or_policy_block")):
        return "REVIEW_OR_POLICY_BLOCK"
    if bool(ctx.get("transient_evidence")) and int(ctx.get("rerun_count") or 0) == 0:
        return "TRANSIENT_FLAKE"
    return "UNKNOWN_NEEDS_DEEPER_EVIDENCE"


def action_mode(text: str) -> str:
    value = text.lower()
    if any(x in value for x in ["fix and merge", "merge when green", "finish this pr"]):
        return "CLOSURE"
    if any(x in value for x in ["fix it", "fix ci", "get ci green", "get this pr green", "move this pr forward", "repair"]):
        return "REPAIR"
    return "INSPECT"


def jobs_needing_logs(jobs: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [
        job for job in jobs
        if str(job.get("conclusion") or "").lower() in FAIL_STATES
        and not bool(job.get("cause_explicit"))
    ]


def should_rerun(ctx: Mapping[str, Any]) -> bool:
    return (
        classify_failure(ctx) == "TRANSIENT_FLAKE"
        and int(ctx.get("rerun_count") or 0) == 0
        and not bool(ctx.get("deterministic_signature"))
    )


def repair_allowed(ctx: Mapping[str, Any], mode: str) -> bool:
    if mode not in {"REPAIR", "CLOSURE"}:
        return False
    if bool(ctx.get("decision_required")) or bool(ctx.get("owned_by_other_worker")):
        return False
    return bool(ctx.get("bounded_fix")) and bool(ctx.get("write_capability", True))


def exact_head_verified(ctx: Mapping[str, Any]) -> bool:
    return cp.checks_current_and_green({
        "head_sha": ctx.get("head_sha"),
        "checks_head_sha": ctx.get("verified_head_sha"),
        "required_checks_green": bool(ctx.get("required_checks_green")),
        "head_moved_after_checks": bool(ctx.get("head_moved_after_verify")),
    })


def merge_allowed(ctx: Mapping[str, Any], mode: str) -> bool:
    if mode != "CLOSURE":
        return False
    shared = dict(ctx)
    shared["checks_head_sha"] = ctx.get("verified_head_sha")
    shared["head_moved_after_checks"] = bool(ctx.get("head_moved_after_verify"))
    shared["ordinary_review_complete"] = bool(ctx.get("required_review_complete", True))
    shared["acceptance_complete"] = bool(ctx.get("acceptance_complete", True))
    shared["unresolved_review_feedback"] = not bool(ctx.get("review_blockers_resolved", True))
    return cp.merge_eligible(shared)
