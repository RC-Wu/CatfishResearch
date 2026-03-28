from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any


TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from catfish_route_core import (  # noqa: E402
    DEFAULT_HEALTH_PATH,
    DEFAULT_LEDGER_PATH,
    DEFAULT_REGISTRY_PATH,
    evaluate_provider,
    health_index,
    choose_reasoning_tier,
    load_router_inputs,
    reasoning_length_for_tier,
)


DEFAULT_ROUTE_PREVIEW_NAME = "provider_route_preview.json"
DEFAULT_DOCTOR_REPORT_NAME = "provider_doctor_report.json"


@dataclass
class ProviderDoctorCandidate:
    provider_id: str
    provider_display_name: str
    provider_base_url: str
    provider_base_url_source: str
    provider_env_key: str
    provider_base_url_env: str
    provider_requires_openai_auth: bool
    machine_id: str
    task_category: str
    difficulty: str
    tier_id: str
    reasoning_length: str
    reasoning_effort: str
    model: str
    score: float
    blockers: list[str]
    env_warnings: list[str]
    env_blockers: list[str]
    health: dict[str, Any]
    rationale: list[str]
    selected: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect Catfish provider health and produce a failover preview.")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY_PATH)
    parser.add_argument("--health", type=Path, default=DEFAULT_HEALTH_PATH)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER_PATH)
    parser.add_argument("--state-root", type=Path, default=None, help="Optional Catfish state-root to write into.")
    parser.add_argument("--machine", default="dev-intern-02")
    parser.add_argument("--task-category", default="builder")
    parser.add_argument("--difficulty", default="medium")
    parser.add_argument("--parent-score", type=float, default=0.5)
    parser.add_argument("--tier", default="", help="Explicit reasoning tier override.")
    parser.add_argument("--model", default="", help="Explicit model override.")
    parser.add_argument("--write", action="store_true", help="Write route preview/report files into the state-root.")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON output path.")
    return parser


def build_provider_doctor_report(
    registry: dict[str, Any],
    health_snapshot: dict[str, Any],
    ledger: dict[str, Any],
    *,
    machine_id: str,
    task_category: str,
    difficulty: str,
    parent_score: float,
    requested_tier: str | None = None,
    requested_model: str | None = None,
) -> dict[str, Any]:
    routing = dict(registry.get("routing", {}))
    tier_id = choose_reasoning_tier(
        routing,
        task_category=task_category,
        difficulty=difficulty,
        requested_tier=requested_tier,
    )
    reasoning_length = reasoning_length_for_tier(routing, tier_id)
    health_by_provider = health_index(health_snapshot)
    reference_date = date.today()

    candidates: list[ProviderDoctorCandidate] = []
    for provider in registry.get("providers", []):
        provider_id = str(provider.get("id", ""))
        health = health_by_provider.get(provider_id)
        evaluation = evaluate_provider(
            provider,
            health,
            ledger,
            machine_id=machine_id,
            task_category=task_category,
            difficulty=difficulty,
            tier_id=tier_id,
            reasoning_length=reasoning_length,
            parent_score=parent_score,
            requested_model=requested_model or None,
            reference_date=reference_date,
        )
        env_warnings, env_blockers = _provider_env_checks(provider)
        blockers = list(evaluation["blockers"])
        blocks_for_selection = list(blockers)
        candidate = ProviderDoctorCandidate(
            provider_id=provider_id,
            provider_display_name=str(evaluation.get("provider_display_name", provider_id)),
            provider_base_url=str(evaluation.get("provider_base_url", "")),
            provider_base_url_source=str(evaluation.get("provider_base_url_source", "unset")),
            provider_env_key=str(evaluation.get("provider_env_key", "")),
            provider_base_url_env=str(evaluation.get("provider_base_url_env", "")),
            provider_requires_openai_auth=bool(evaluation.get("provider_requires_openai_auth", False)),
            machine_id=machine_id,
            task_category=task_category,
            difficulty=difficulty,
            tier_id=tier_id,
            reasoning_length=reasoning_length,
            reasoning_effort=str(evaluation.get("reasoningEffort", "")),
            model=str(evaluation.get("model", "")),
            score=float(evaluation.get("score", 0.0)),
            blockers=blocks_for_selection,
            env_warnings=env_warnings,
            env_blockers=env_blockers,
            health=dict(health or {}),
            rationale=list(evaluation.get("rationale", [])),
        )
        candidates.append(candidate)

    selected = _choose_provider_candidate(candidates)
    route_preview = _build_route_preview(selected)
    report = {
        "schemaVersion": "catfish.provider-doctor.v1",
        "generatedAt": _utc_now(),
        "machineId": machine_id,
        "taskCategory": task_category,
        "difficulty": difficulty,
        "parentScore": parent_score,
        "tierId": tier_id,
        "reasoningLength": reasoning_length,
        "selectedProviderId": selected.provider_id,
        "selectedProviderDisplayName": selected.provider_display_name,
        "failoverRequired": bool(selected.blockers or selected.env_blockers),
        "routePreview": route_preview,
        "providers": [item.to_dict() for item in sorted(candidates, key=_candidate_sort_key)],
        "envSummary": _env_summary(candidates),
    }
    return report


def write_state_root(state_root: Path, report: dict[str, Any]) -> None:
    system_root = state_root / "system"
    system_root.mkdir(parents=True, exist_ok=True)
    (system_root / DEFAULT_ROUTE_PREVIEW_NAME).write_text(
        json.dumps(report["routePreview"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (system_root / DEFAULT_DOCTOR_REPORT_NAME).write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _provider_env_checks(provider: dict[str, Any]) -> tuple[list[str], list[str]]:
    env_warnings: list[str] = []
    env_blockers: list[str] = []
    base_url_env = str(provider.get("baseUrlEnv", "")).strip()
    env_key = str(provider.get("envKey", "")).strip()
    if base_url_env:
        if os.environ.get(base_url_env, "").strip():
            env_warnings.append(f"base-url-resolved-from-env:{base_url_env}")
        else:
            env_warnings.append(f"base-url-env-missing:{base_url_env}")
    if env_key:
        if os.environ.get(env_key, "").strip():
            env_warnings.append(f"auth-resolved-from-env:{env_key}")
        elif bool(provider.get("requiresOpenAIAuth", False)):
            env_blockers.append(f"missing-auth-env:{env_key}")
        else:
            env_warnings.append(f"auth-env-missing:{env_key}")
    return env_warnings, env_blockers


def _choose_provider_candidate(candidates: list[ProviderDoctorCandidate]) -> ProviderDoctorCandidate:
    healthy = [item for item in candidates if not item.blockers and not item.env_blockers]
    if healthy:
        return max(healthy, key=_candidate_sort_key)
    env_clean = [item for item in candidates if not item.blockers]
    if env_clean:
        return max(env_clean, key=_candidate_sort_key)
    return max(candidates, key=_candidate_sort_key)


def _candidate_sort_key(candidate: ProviderDoctorCandidate) -> tuple[int, float, int, str]:
    return (
        -(len(candidate.blockers) + len(candidate.env_blockers)),
        candidate.score,
        -(len(candidate.health.get("notes", [])) if isinstance(candidate.health.get("notes", []), list) else 0),
        candidate.provider_id,
    )


def _build_route_preview(candidate: ProviderDoctorCandidate) -> dict[str, Any]:
    return {
        "profileId": candidate.provider_id,
        "providerId": candidate.provider_id,
        "providerDisplayName": candidate.provider_display_name,
        "providerBaseUrl": candidate.provider_base_url,
        "providerBaseUrlSource": candidate.provider_base_url_source,
        "providerEnvKey": candidate.provider_env_key,
        "providerBaseUrlEnv": candidate.provider_base_url_env,
        "providerRequiresOpenAIAuth": candidate.provider_requires_openai_auth,
        "machineId": candidate.machine_id,
        "taskCategory": candidate.task_category,
        "difficulty": candidate.difficulty,
        "tierId": candidate.tier_id,
        "reasoningLength": candidate.reasoning_length,
        "reasoningEffort": candidate.reasoning_effort,
        "model": candidate.model,
        "search": False,
        "browserMode": "none",
        "rationale": candidate.rationale + candidate.env_warnings + candidate.env_blockers,
        "selected": True,
    }


def _env_summary(candidates: list[ProviderDoctorCandidate]) -> dict[str, Any]:
    missing = sorted(
        {
            warning.split(":", 1)[1]
            for candidate in candidates
            for warning in candidate.env_warnings + candidate.env_blockers
            if "missing:" in warning
        }
    )
    resolved = sorted(
        {
            warning.split(":", 1)[1]
            for candidate in candidates
            for warning in candidate.env_warnings
            if warning.startswith("base-url-resolved-from-env:") or warning.startswith("auth-resolved-from-env:")
        }
    )
    return {"missing": missing, "resolved": resolved}


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    registry, health_snapshot, ledger = load_router_inputs(args.registry, args.health, args.ledger)
    report = build_provider_doctor_report(
        registry,
        health_snapshot,
        ledger,
        machine_id=args.machine,
        task_category=args.task_category,
        difficulty=args.difficulty,
        parent_score=args.parent_score,
        requested_tier=args.tier or None,
        requested_model=args.model or None,
    )
    if args.write:
        if args.state_root is None:
            parser.error("--write requires --state-root")
        write_state_root(args.state_root, report)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
