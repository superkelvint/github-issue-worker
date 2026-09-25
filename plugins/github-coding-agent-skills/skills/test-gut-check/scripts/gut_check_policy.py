#!/usr/bin/env python3
from __future__ import annotations
from typing import Any, Mapping


def exact_head_verified(ctx: Mapping[str, Any]) -> bool:
    return bool(ctx.get("head_sha")) and str(ctx.get("head_sha")) == str(ctx.get("verified_head_sha"))


def disposition(ctx: Mapping[str, Any]) -> str:
    if bool(ctx.get("external_blocker")):
        return "BLOCKED"
    if bool(ctx.get("meaningful_gap")) or bool(ctx.get("plausible_false_green")):
        return "GAPS_FOUND"
    if not bool(ctx.get("lineage_understood")) or not bool(ctx.get("acceptance_mapped")):
        return "BLOCKED"
    return "SUFFICIENT"


def remediation_required(ctx: Mapping[str, Any]) -> bool:
    return disposition(ctx) == "GAPS_FOUND" and bool(ctx.get("gap_actionable", True))


def regression_first_required(ctx: Mapping[str, Any]) -> bool:
    return bool(ctx.get("new_test_exposes_product_defect"))


def completion_allowed(ctx: Mapping[str, Any]) -> bool:
    if disposition(ctx) == "BLOCKED":
        return False
    if remediation_required(ctx) and not bool(ctx.get("gaps_rectified")):
        return False
    if regression_first_required(ctx) and not bool(ctx.get("pre_fix_failure_observed")):
        return False
    return all([
        bool(ctx.get("test_inventory_complete")),
        bool(ctx.get("acceptance_mapped")),
        bool(ctx.get("false_green_challenged")),
        exact_head_verified(ctx),
    ])
