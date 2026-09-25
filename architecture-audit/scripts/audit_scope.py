#!/usr/bin/env python3
"""Suggest SearchKernel audit modules and area labels for a requested scope.

The live implementation-plan/audit/README.md remains authoritative. This helper
only provides deterministic common-scope routing.
"""

from __future__ import annotations

import argparse
import json

BASE = ["00-audit-method.md"]
CROSS = ["18-cross-cutting-gates.md", "19-audit-record-and-freeze.md"]
ALL_MODULES = [f"{i:02d}-{name}" for i, name in [
    (0, "audit-method.md"),
    (1, "api-portable-contract.md"),
    (2, "flatbuffers-build.md"),
    (3, "searchkernel-protocol.md"),
    (4, "searchkernel-filter.md"),
    (5, "searchkernel-ir.md"),
    (6, "searchkernel-testkit.md"),
    (7, "searchkernel-rust-api.md"),
    (8, "searchkernel-dispatch.md"),
    (9, "searchkernel-ir-adapter.md"),
    (10, "searchkernel-vespa-bindings.md"),
    (11, "searchkernel-vespa-engine.md"),
    (12, "native-vespa-cpp.md"),
    (13, "searchkerneld.md"),
    (14, "client-python.md"),
    (15, "client-typescript.md"),
    (16, "tools.md"),
    (17, "reference-verifiers.md"),
    (18, "cross-cutting-gates.md"),
    (19, "audit-record-and-freeze.md"),
]]

ROUTES = {
    "api": (["01-api-portable-contract.md", "02-flatbuffers-build.md", "03-searchkernel-protocol.md"], ["area:protocol"]),
    "portable": (["01-api-portable-contract.md", "03-searchkernel-protocol.md", "05-searchkernel-ir.md"], ["area:protocol", "area:ir"]),
    "protocol": (["01-api-portable-contract.md", "03-searchkernel-protocol.md"], ["area:protocol"]),
    "flatbuffers": (["01-api-portable-contract.md", "02-flatbuffers-build.md", "03-searchkernel-protocol.md"], ["area:protocol"]),
    "filter": (["04-searchkernel-filter.md", "05-searchkernel-ir.md"], ["area:ir"]),
    "ir": (["05-searchkernel-ir.md"], ["area:ir"]),
    "testkit": (["06-searchkernel-testkit.md"], []),
    "rust": (["07-searchkernel-rust-api.md"], ["area:rust-api"]),
    "rust-api": (["07-searchkernel-rust-api.md"], ["area:rust-api"]),
    "dispatch": (["08-searchkernel-dispatch.md", "05-searchkernel-ir.md"], ["area:protocol", "area:ir"]),
    "adapter": (["09-searchkernel-ir-adapter.md", "05-searchkernel-ir.md", "11-searchkernel-vespa-engine.md"], ["area:ir", "area:vespa"]),
    "ir-adapter": (["09-searchkernel-ir-adapter.md", "05-searchkernel-ir.md", "11-searchkernel-vespa-engine.md"], ["area:ir", "area:vespa"]),
    "bindings": (["10-searchkernel-vespa-bindings.md", "12-native-vespa-cpp.md"], ["area:native", "area:vespa"]),
    "native": (["10-searchkernel-vespa-bindings.md", "11-searchkernel-vespa-engine.md", "12-native-vespa-cpp.md"], ["area:native", "area:vespa"]),
    "vespa": (["09-searchkernel-ir-adapter.md", "10-searchkernel-vespa-bindings.md", "11-searchkernel-vespa-engine.md", "12-native-vespa-cpp.md"], ["area:vespa", "area:native"]),
    "vespa-engine": (["11-searchkernel-vespa-engine.md", "12-native-vespa-cpp.md"], ["area:vespa", "area:native"]),
    "daemon": (["13-searchkerneld.md", "08-searchkernel-dispatch.md"], ["area:searchkerneld", "area:protocol"]),
    "searchkerneld": (["13-searchkerneld.md", "08-searchkernel-dispatch.md"], ["area:searchkerneld", "area:protocol"]),
    "python": (["14-client-python.md", "03-searchkernel-protocol.md", "08-searchkernel-dispatch.md"], ["area:python"]),
    "typescript": (["15-client-typescript.md", "03-searchkernel-protocol.md", "08-searchkernel-dispatch.md"], ["area:typescript"]),
    "tools": (["16-tools.md"], ["area:ci"]),
    "ci": (["16-tools.md", "17-reference-verifiers.md"], ["area:ci"]),
    "verifier": (["17-reference-verifiers.md"], ["area:ci"]),
    "verifiers": (["17-reference-verifiers.md"], ["area:ci"]),
    "cross-cutting": (["18-cross-cutting-gates.md"], []),
}


def select(scope: str) -> dict[str, object]:
    normalized = " ".join(scope.lower().replace("_", "-").split())
    if normalized in {"all", "repo", "repository", "repository-wide", "whole repo", "whole repository"}:
        return {"scope": scope, "audit_files": ALL_MODULES, "area_labels": [], "warning": None}

    matched_files: list[str] = []
    labels: list[str] = []
    for key, (files, areas) in ROUTES.items():
        if key in normalized:
            matched_files.extend(files)
            labels.extend(areas)

    warning = None
    if not matched_files:
        warning = "No deterministic route matched; inspect the live audit README and live repository inventory before selecting modules."

    ordered = []
    for path in BASE + matched_files + CROSS:
        if path not in ordered:
            ordered.append(path)

    return {
        "scope": scope,
        "audit_files": ordered,
        "area_labels": sorted(set(labels)),
        "warning": warning,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("scope", nargs="+", help="requested subsystem/audit scope")
    args = parser.parse_args()
    print(json.dumps(select(" ".join(args.scope)), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
