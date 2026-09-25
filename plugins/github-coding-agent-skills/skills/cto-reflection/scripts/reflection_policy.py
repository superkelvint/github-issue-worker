#!/usr/bin/env python3
from __future__ import annotations
from typing import Any, Mapping


def evidence_strength(item: Mapping[str, Any]) -> str:
    if int(item.get("repeat_count") or 0) >= 2:
        return "RECURRING"
    if bool(item.get("high_severity")):
        return "HIGH_SEVERITY_ONE_OFF"
    return "HYPOTHESIS"


def recommended_fix(item: Mapping[str, Any]) -> str:
    if bool(item.get("repository_tooling_cause")):
        return "REPOSITORY_TOOLING"
    if bool(item.get("workflow_policy_cause")):
        return "CTO_WORKFLOW"
    if bool(item.get("clear_future_trigger")) and bool(item.get("repeated_polling")):
        return "AUTOMATION"
    if bool(item.get("existing_skill_should_own")) and (
        int(item.get("repeat_count") or 0) >= 2 or bool(item.get("high_severity"))
    ):
        return "SKILL_CHANGE"
    if bool(item.get("distinct_missing_workflow")) and int(item.get("repeat_count") or 0) >= 2:
        return "NEW_SKILL"
    if bool(item.get("user_habit_cause")):
        return "USER_HABIT"
    return "NO_CHANGE"


def shortcut_safe(item: Mapping[str, Any]) -> bool:
    return not any([
        bool(item.get("skips_required_tests")),
        bool(item.get("stale_cache_risk")),
        bool(item.get("merge_before_exact_head")),
        bool(item.get("strands_work")),
    ])


def skill_change_warranted(item: Mapping[str, Any]) -> bool:
    return recommended_fix(item) == "SKILL_CHANGE" and shortcut_safe(item)
