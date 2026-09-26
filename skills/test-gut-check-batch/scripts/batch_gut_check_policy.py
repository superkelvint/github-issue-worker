#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re
from typing import Any, Iterable, Mapping

MARKER = "<!-- test-gut-check-batch -->"
FIELD = re.compile(r"^(head_sha|disposition):\s*(.+?)\s*$", re.M)
CURRENT_OK = {"SUFFICIENT", "GAPS_RECTIFIED", "N/A", "NOT_LANDED"}
SCOPE = re.compile(r"^(open|closed(?::([1-9]\d*)([hd]))?)$", re.I)
DEFAULT_CLOSED_LOOKBACK = timedelta(hours=72)


def parse_scope_argument(value: str | None) -> dict[str, Any]:
    raw = (value or "").strip().lower()
    if not raw:
        return {"mode": "open", "lookback": None, "canonical": "open"}

    match = SCOPE.fullmatch(raw)
    if not match:
        raise ValueError(
            "scope must be 'open', 'closed', 'closed:<N>h', or 'closed:<N>d'"
        )

    if match.group(1) == "open":
        return {"mode": "open", "lookback": None, "canonical": "open"}

    amount = match.group(2)
    unit = match.group(3)
    if amount is None:
        delta = DEFAULT_CLOSED_LOOKBACK
        canonical = "closed:72h"
    else:
        n = int(amount)
        delta = timedelta(hours=n) if unit == "h" else timedelta(days=n)
        canonical = f"closed:{n}{unit}"

    return {"mode": "closed", "lookback": delta, "canonical": canonical}


def _as_utc(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def in_scope(
    pr: Mapping[str, Any],
    scope: str | None = None,
    now: datetime | str | None = None,
) -> bool:
    spec = parse_scope_argument(scope)
    state = str(pr.get("state") or "").lower()

    if spec["mode"] == "open":
        return state == "open"

    if state != "closed":
        return False

    closed_at = pr.get("closed_at")
    if not closed_at:
        return False

    current = _as_utc(now) if now is not None else datetime.now(timezone.utc)
    closed = _as_utc(closed_at)
    cutoff = current - spec["lookback"]
    return cutoff <= closed <= current


def parse_marker(text: str):
    if MARKER not in text:
        return None
    vals = {k: v.strip() for k, v in FIELD.findall(text)}
    head = vals.get("head_sha", "")
    disp = vals.get("disposition", "").upper()
    if not re.fullmatch(r"[0-9a-fA-F]{40}", head):
        return None
    if disp not in {
        "SUFFICIENT",
        "GAPS_RECTIFIED",
        "GAPS_REMAIN",
        "N/A",
        "NOT_LANDED",
        "BLOCKED",
    }:
        return None
    return {"head_sha": head.lower(), "disposition": disp}


def audit_state(pr: Mapping[str, Any], scope: str | None = None) -> str:
    spec = parse_scope_argument(scope)
    if spec["mode"] == "closed" and not bool(pr.get("merged")):
        return "NOT_LANDED"
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


def should_audit(
    pr: Mapping[str, Any],
    fresh: bool = False,
    scope: str | None = None,
) -> bool:
    state = audit_state(pr, scope=scope)
    if state in {"ACTIVE", "BLOCKED"}:
        return False
    if state in {"N/A", "NOT_LANDED"}:
        return current_marker(pr) is None
    marker = current_marker(pr)
    if fresh or not marker:
        return True
    return marker["disposition"] not in CURRENT_OK


def mutation_allowed(pr: Mapping[str, Any], scope: str | None = None) -> bool:
    spec = parse_scope_argument(scope)
    if spec["mode"] == "closed":
        return False
    return all(
        [
            audit_state(pr, scope=scope) == "AUDIT",
            bool(pr.get("writable")),
            not bool(pr.get("head_moving")),
            not bool(pr.get("separate_review_unit")),
        ]
    )


def remaining(
    prs: Iterable[Mapping[str, Any]],
    scope: str | None = None,
    now: datetime | str | None = None,
) -> list[int]:
    return [
        int(pr.get("number"))
        for pr in prs
        if in_scope(pr, scope=scope, now=now)
        and should_audit(pr, scope=scope)
    ]
