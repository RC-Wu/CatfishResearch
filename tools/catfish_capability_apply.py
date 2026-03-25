from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Sequence

from catfish_parent_review import utc_now


SCHEMA_VERSION = "catfish.capability-apply.v1"


def load_json(path: Path) -> dict[str, Any] | list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_router_entries(
    ledger: dict[str, Any],
    entries: Sequence[dict[str, Any]],
    *,
    review_id: str,
    applied_at: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    updated = deepcopy(ledger)
    updated.setdefault("entries", [])
    existing_ids = {str(entry.get("id")) for entry in updated["entries"]}
    added_entries: list[dict[str, Any]] = []
    skipped_entry_ids: list[str] = []

    for entry in entries:
        entry_id = str(entry["id"])
        if entry_id in existing_ids:
            skipped_entry_ids.append(entry_id)
            continue
        updated["entries"].append(deepcopy(entry))
        existing_ids.add(entry_id)
        added_entries.append(deepcopy(entry))

    applied_timestamp = applied_at or utc_now()
    updated["updatedAt"] = applied_timestamp
    updated.setdefault("auditLog", [])
    audit_record = {
        "appliedAt": applied_timestamp,
        "reviewId": review_id,
        "addedEntryIds": [entry["id"] for entry in added_entries],
        "skippedEntryIds": skipped_entry_ids,
    }
    updated["auditLog"].append(audit_record)
    return updated, audit_record


def build_runtime_verdict_operation(project_id: str, runtime_verdict: dict[str, Any]) -> dict[str, Any]:
    return {
        "op": "apply_parent_verdict",
        "project_id": project_id,
        "verdict": deepcopy(runtime_verdict),
    }


def append_runtime_operation(
    operations_payload: list[dict[str, Any]] | dict[str, Any],
    *,
    project_id: str,
    runtime_verdict: dict[str, Any],
) -> list[dict[str, Any]] | dict[str, Any]:
    operation = build_runtime_verdict_operation(project_id, runtime_verdict)
    if isinstance(operations_payload, list):
        updated = list(operations_payload)
        updated.append(operation)
        return updated
    if isinstance(operations_payload, dict):
        updated = deepcopy(operations_payload)
        operations = list(updated.get("operations") or [])
        operations.append(operation)
        updated["operations"] = operations
        return updated
    raise ValueError("Operations payload must be a list or an object with an operations key")


def apply_review_output(
    review_output: dict[str, Any],
    *,
    ledger: dict[str, Any] | None = None,
    operations_payload: list[dict[str, Any]] | dict[str, Any] | None = None,
    project_id: str | None = None,
    applied_at: str | None = None,
) -> dict[str, Any]:
    review_id = str(review_output.get("reviewId") or "")
    runtime_verdict = dict(review_output["runtime_verdict"])
    router_entries = list(dict(review_output.get("router_capability_updates") or {}).get("entries") or [])
    applied_timestamp = applied_at or utc_now()

    result: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "reviewId": review_id,
        "appliedAt": applied_timestamp,
        "router": {
            "addedEntryIds": [],
            "skippedEntryIds": [],
        },
        "runtime": {
            "operationAdded": False,
        },
    }

    if ledger is not None:
        updated_ledger, audit_record = append_router_entries(
            ledger,
            router_entries,
            review_id=review_id,
            applied_at=applied_timestamp,
        )
        result["router"].update(
            {
                "ledger": updated_ledger,
                "addedEntryIds": list(audit_record["addedEntryIds"]),
                "skippedEntryIds": list(audit_record["skippedEntryIds"]),
            }
        )

    resolved_project_id = project_id or str(review_output.get("projectId") or review_output.get("project_id") or "")
    if operations_payload is not None:
        if not resolved_project_id:
            raise ValueError("project_id is required to append a runtime verdict operation")
        result["runtime"]["operations"] = append_runtime_operation(
            operations_payload,
            project_id=resolved_project_id,
            runtime_verdict=runtime_verdict,
        )
        result["runtime"]["operationAdded"] = True
        result["runtime"]["projectId"] = resolved_project_id
        result["runtime"]["verdictId"] = runtime_verdict.get("verdict_id")
    elif resolved_project_id:
        result["runtime"]["operation"] = build_runtime_verdict_operation(resolved_project_id, runtime_verdict)
        result["runtime"]["projectId"] = resolved_project_id
        result["runtime"]["verdictId"] = runtime_verdict.get("verdict_id")

    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Append Catfish parent-review capability updates to router/runtime artifacts."
    )
    parser.add_argument("--review", type=Path, required=True, help="Parent review JSON output file")
    parser.add_argument("--ledger", type=Path, help="Optional existing router ledger JSON file")
    parser.add_argument("--ledger-output", type=Path, help="Optional path for the updated ledger JSON file")
    parser.add_argument("--runtime-ops", type=Path, help="Optional existing runtime operations JSON file")
    parser.add_argument(
        "--runtime-ops-output",
        type=Path,
        help="Optional path for the updated runtime operations JSON file",
    )
    parser.add_argument("--project-id", default="", help="Project id for runtime operation generation")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    review_output = dict(load_json(args.review))
    ledger_payload = dict(load_json(args.ledger)) if args.ledger else None
    operations_payload = load_json(args.runtime_ops) if args.runtime_ops else None
    result = apply_review_output(
        review_output,
        ledger=ledger_payload,
        operations_payload=operations_payload,
        project_id=args.project_id or None,
    )

    if args.ledger_output and "ledger" in result["router"]:
        write_json(args.ledger_output, result["router"]["ledger"])
    if args.runtime_ops_output and "operations" in result["runtime"]:
        write_json(args.runtime_ops_output, result["runtime"]["operations"])

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
