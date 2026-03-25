from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY_PATH = REPO_ROOT / "assets" / "catfish_policy" / "diversity_policy.example.json"
REQUIRED_STAGES = (
    "idea",
    "planning",
    "implementation",
    "experiment",
    "evaluation",
    "writing",
    "figures",
    "routing",
    "resource_allocation",
)
REQUIRED_AXES = (
    "provider",
    "model",
    "prompt_style",
    "agent_role",
    "group_strategy",
    "evidence_type",
)
REQUIRED_TOP_LEVEL_FIELDS = (
    "schemaVersion",
    "policyId",
    "updatedAt",
    "axisDefinitions",
    "references",
    "stages",
)
REQUIRED_STAGE_FIELDS = (
    "stageId",
    "stageClass",
    "continuousControl",
    "competitionUnit",
    "primaryAdvancement",
    "explorationPolicy",
    "evaluationPolicy",
    "collapsePolicy",
)
REQUIRED_POLICY_FIELDS = (
    "objective",
    "frontierIntent",
    "competitionMode",
    "candidateCount",
    "advanceCount",
    "wildcardCount",
    "axisCoverage",
    "requiredEvidenceTypes",
)
REQUIRED_AXIS_FIELDS = (
    "priority",
    "targetDistinct",
    "minDistinct",
    "fallback",
)
ALLOWED_AXIS_PRIORITIES = {"primary", "secondary", "fixed"}


def _validate_axis_coverage(
    stage_id: str,
    policy_name: str,
    axis_coverage: Any,
    errors: list[str],
) -> None:
    if not isinstance(axis_coverage, dict):
        errors.append(f"{stage_id}.{policy_name}.axisCoverage must be an object")
        return

    missing_axes = [axis for axis in REQUIRED_AXES if axis not in axis_coverage]
    if missing_axes:
        errors.append(f"{stage_id}.{policy_name}.axisCoverage missing axes: {', '.join(missing_axes)}")

    for axis_name in REQUIRED_AXES:
        axis_payload = axis_coverage.get(axis_name)
        if not isinstance(axis_payload, dict):
            errors.append(f"{stage_id}.{policy_name}.axisCoverage.{axis_name} must be an object")
            continue
        for field_name in REQUIRED_AXIS_FIELDS:
            if field_name not in axis_payload:
                errors.append(f"{stage_id}.{policy_name}.axisCoverage.{axis_name} missing field {field_name}")
        priority = axis_payload.get("priority")
        if priority not in ALLOWED_AXIS_PRIORITIES:
            errors.append(
                f"{stage_id}.{policy_name}.axisCoverage.{axis_name}.priority "
                f"must be one of {sorted(ALLOWED_AXIS_PRIORITIES)}"
            )
        target_distinct = axis_payload.get("targetDistinct")
        min_distinct = axis_payload.get("minDistinct")
        if not isinstance(target_distinct, int) or target_distinct < 1:
            errors.append(f"{stage_id}.{policy_name}.axisCoverage.{axis_name}.targetDistinct must be an int >= 1")
        if not isinstance(min_distinct, int) or min_distinct < 1:
            errors.append(f"{stage_id}.{policy_name}.axisCoverage.{axis_name}.minDistinct must be an int >= 1")
        if isinstance(target_distinct, int) and isinstance(min_distinct, int) and target_distinct < min_distinct:
            errors.append(
                f"{stage_id}.{policy_name}.axisCoverage.{axis_name}.targetDistinct must be >= minDistinct"
            )
        fallback = axis_payload.get("fallback")
        if not isinstance(fallback, str) or not fallback.strip():
            errors.append(f"{stage_id}.{policy_name}.axisCoverage.{axis_name}.fallback must be a non-empty string")


def _validate_policy(stage_id: str, policy_name: str, payload: Any, errors: list[str]) -> None:
    if not isinstance(payload, dict):
        errors.append(f"{stage_id}.{policy_name} must be an object")
        return

    for field_name in REQUIRED_POLICY_FIELDS:
        if field_name not in payload:
            errors.append(f"{stage_id}.{policy_name} missing field {field_name}")

    for text_field in ("objective", "frontierIntent", "competitionMode"):
        value = payload.get(text_field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{stage_id}.{policy_name}.{text_field} must be a non-empty string")

    candidate_count = payload.get("candidateCount")
    advance_count = payload.get("advanceCount")
    wildcard_count = payload.get("wildcardCount")
    if not isinstance(candidate_count, int) or candidate_count < 1:
        errors.append(f"{stage_id}.{policy_name}.candidateCount must be an int >= 1")
    if not isinstance(advance_count, int) or advance_count < 1:
        errors.append(f"{stage_id}.{policy_name}.advanceCount must be an int >= 1")
    if not isinstance(wildcard_count, int) or wildcard_count < 0:
        errors.append(f"{stage_id}.{policy_name}.wildcardCount must be an int >= 0")
    if isinstance(candidate_count, int) and isinstance(advance_count, int) and advance_count > candidate_count:
        errors.append(f"{stage_id}.{policy_name}.advanceCount must be <= candidateCount")

    required_evidence_types = payload.get("requiredEvidenceTypes")
    if not isinstance(required_evidence_types, list) or not required_evidence_types:
        errors.append(f"{stage_id}.{policy_name}.requiredEvidenceTypes must be a non-empty array")
    elif not all(isinstance(item, str) and item.strip() for item in required_evidence_types):
        errors.append(f"{stage_id}.{policy_name}.requiredEvidenceTypes must contain non-empty strings")

    _validate_axis_coverage(stage_id, policy_name, payload.get("axisCoverage"), errors)


def _validate_collapse_policy(stage_id: str, payload: Any, errors: list[str]) -> None:
    if not isinstance(payload, dict):
        errors.append(f"{stage_id}.collapsePolicy must be an object")
        return
    allow = payload.get("allowFrontierNarrowing")
    when_all = payload.get("whenAll")
    retain = payload.get("retainDiversityOn")

    if not isinstance(allow, bool):
        errors.append(f"{stage_id}.collapsePolicy.allowFrontierNarrowing must be boolean")
    if not isinstance(when_all, list) or not when_all or not all(isinstance(item, str) and item.strip() for item in when_all):
        errors.append(f"{stage_id}.collapsePolicy.whenAll must be a non-empty array of strings")
    if not isinstance(retain, list) or not retain or not all(isinstance(item, str) for item in retain):
        errors.append(f"{stage_id}.collapsePolicy.retainDiversityOn must be a non-empty array of strings")
    elif unknown := [item for item in retain if item not in REQUIRED_AXES]:
        errors.append(f"{stage_id}.collapsePolicy.retainDiversityOn has unknown axes: {', '.join(sorted(unknown))}")


def _validate_stage(stage_id: str, payload: Any, errors: list[str]) -> None:
    if not isinstance(payload, dict):
        errors.append(f"stage {stage_id} must be an object")
        return

    for field_name in REQUIRED_STAGE_FIELDS:
        if field_name not in payload:
            errors.append(f"{stage_id} missing field {field_name}")

    actual_stage_id = payload.get("stageId")
    stage_class = payload.get("stageClass")
    competition_unit = payload.get("competitionUnit")
    primary_advancement = payload.get("primaryAdvancement")
    if actual_stage_id != stage_id:
        errors.append(f"{stage_id}.stageId must equal its object key")
    if not isinstance(stage_class, str) or not stage_class.strip():
        errors.append(f"{stage_id}.stageClass must be a non-empty string")
    if not isinstance(payload.get("continuousControl"), bool):
        errors.append(f"{stage_id}.continuousControl must be boolean")
    if not isinstance(competition_unit, str) or not competition_unit.strip():
        errors.append(f"{stage_id}.competitionUnit must be a non-empty string")
    if not isinstance(primary_advancement, str) or not primary_advancement.strip():
        errors.append(f"{stage_id}.primaryAdvancement must be a non-empty string")

    _validate_policy(stage_id, "explorationPolicy", payload.get("explorationPolicy"), errors)
    _validate_policy(stage_id, "evaluationPolicy", payload.get("evaluationPolicy"), errors)
    _validate_collapse_policy(stage_id, payload.get("collapsePolicy"), errors)


def validate_payload(payload: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["root payload must be an object"]

    for field_name in REQUIRED_TOP_LEVEL_FIELDS:
        if field_name not in payload:
            errors.append(f"missing top-level field {field_name}")

    for text_field in ("schemaVersion", "policyId", "updatedAt"):
        value = payload.get(text_field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{text_field} must be a non-empty string")

    axis_definitions = payload.get("axisDefinitions")
    if not isinstance(axis_definitions, dict):
        errors.append("axisDefinitions must be an object")
    else:
        missing_axes = [axis for axis in REQUIRED_AXES if axis not in axis_definitions]
        if missing_axes:
            errors.append(f"axisDefinitions missing axes: {', '.join(missing_axes)}")

    references = payload.get("references")
    if not isinstance(references, list) or not references:
        errors.append("references must be a non-empty array")

    stages = payload.get("stages")
    if not isinstance(stages, dict):
        errors.append("stages must be an object")
        return errors

    missing_stages = [stage_id for stage_id in REQUIRED_STAGES if stage_id not in stages]
    if missing_stages:
        errors.append(f"missing required stages: {', '.join(missing_stages)}")

    for stage_id in REQUIRED_STAGES:
        _validate_stage(stage_id, stages.get(stage_id), errors)

    return errors


def load_policy(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Catfish diversity policy JSON.")
    parser.add_argument(
        "policy",
        nargs="?",
        default=str(DEFAULT_POLICY_PATH),
        help="Path to diversity policy JSON. Defaults to the example policy in assets/catfish_policy/.",
    )
    args = parser.parse_args(argv)

    policy_path = Path(args.policy)
    payload = load_policy(policy_path)
    errors = validate_payload(payload)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "status": "ok",
                "policy": str(policy_path),
                "stageCount": len(payload["stages"]),
                "stages": list(REQUIRED_STAGES),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
