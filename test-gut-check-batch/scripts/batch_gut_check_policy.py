#!/usr/bin/env python3
from __future__ import annotations
import re
from typing import Any, Iterable, Mapping

MARKER = "<!-- test-gut-check-batch -->"
FIELD = re.compile(r"^(head_sha|disposition):\s*(.+?)\s*$", re.M)
CURRENT_OK = {"SUFFICIENT", "GAPS_RECTIFIED", "N/A"}


def parse_marker(text: str):
    if MARKER not in text:
        return None
    vals = {k: v.strip() for k, v in FIELD.findall(text)}
    head = vals.get("head_sha", "")
    disp = vals.get("disposition", "").upper()
    if not re.fullmatch(r"[0-9a-fA-F]{40}", head):
        return None
    if disp not in {"SUFFICIENT", "GAPS_RECTIFIED", "GAPS_REMAIN", "N/A", "BLOCKED"}:
        return None
    return {"head_sha": head.lower(), "disposition": disp}


def audit_state(pr: Mapping[str, Any]) -> str:
    if bool(pr.get("head_moving")):
        return "ACTIVE"
    if bool(pr.get("external_blocker")):
        return "BLOCKED"
    if bool(pr.get("runtime_tests_not_applicable")):
        return "N/A"
    return "AUDIT"


def current_marker(pr: Mapping[str, Any]):
    head = str(pr.get("head_sha") or "").lower()
    markers = [parse_marker(x) for x in pr.get("comments") or []]
    valid = [m for m in markers if m and m["head_sha"] == head]
    return valid[-1] if valid else None


def should_audit(pr: Mapping[str, Any], fresh: bool = False) -> bool:
    state = audit_state(pr)
    if state in {"ACTIVE", "BLOCKED", "N/A"}:
        return state == "N/A" and current_marker(pr) is None
    marker = current_marker(pr)
    if fresh or not marker:
        return True
    return marker["disposition"] not in CURRENT_OK


def mutation_allowed(pr: Mapping[str, Any]) -> bool:
    return all([
        audit_state(pr) == "AUDIT",
        bool(pr.get("writable")),
        not bool(pr.get("head_moving")),
        not bool(pr.get("separate_review_unit")),
    ])


def remaining(prs: Iterable[Mapping[str, Any]]) -> list[int]:
    return [int(pr.get("number")) for pr in prs if should_audit(pr)]
