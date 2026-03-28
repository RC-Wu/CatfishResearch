from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
APP_ROOT = REPO_ROOT / "apps" / "catfish-control-center"
DEFAULT_SMOKE_STATE_ROOT = APP_ROOT / "examples" / "circleediting_production_smoke_state_root"
DEFAULT_PROJECT_ID = "circleediting-3d-edit"
GUARDRAIL_PROBE = TOOLS_DIR / "catfish_guardrail_probe.py"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from catfish_control_center.dashboard import render_view  # noqa: E402
from catfish_control_center.runtime import load_live_state  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Smoke test Catfish supervision of CircleEditing.")
    parser.add_argument(
        "--state-root",
        type=Path,
        default=DEFAULT_SMOKE_STATE_ROOT,
        help="State root to verify. Defaults to the bundled CircleEditing smoke artifact.",
    )
    parser.add_argument(
        "--materialize",
        type=Path,
        help="Copy the bundled smoke state-root to this destination before verification.",
    )
    parser.add_argument(
        "--project-id",
        default=DEFAULT_PROJECT_ID,
        help="Expected CircleEditing project id.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON report path.",
    )
    return parser


def materialize_smoke_state_root(destination: Path, source: Path = DEFAULT_SMOKE_STATE_ROOT) -> Path:
    source = source.resolve()
    destination = destination.resolve()
    if destination == source:
        return destination
    if destination.exists():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    import shutil

    shutil.copytree(source, destination)
    return destination


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_guardrail_probe(state_root: Path) -> dict[str, Any]:
    command = [
        sys.executable,
        str(GUARDRAIL_PROBE),
        "--state-root",
        str(state_root),
        "--root-dir",
        str(state_root),
        "--vepfs-root",
        str(state_root),
        "--cpu-percent",
        "12.5",
    ]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
    return json.loads(result.stdout)


def build_smoke_report(state_root: Path, *, project_id: str = DEFAULT_PROJECT_ID) -> dict[str, Any]:
    probe = run_guardrail_probe(state_root)
    snapshot = load_live_state(state_root)
    project = next((item for item in snapshot.projects if item.project_id == project_id), None)
    if project is None:
        raise RuntimeError(f"Missing project {project_id} in smoke state-root {state_root}")

    dashboard_view = render_view(snapshot, "dashboard")
    guardrails_view = render_view(snapshot, "guardrails")
    supervisor_view = render_view(snapshot, "supervisor")
    agentdoc_state = _load_json(state_root / "system" / "agentdoc_state.json")
    resource_manager_state = _load_json(state_root / "system" / "resource_manager_state.json")

    report = {
        "simulated": True,
        "state_root": str(state_root),
        "project_id": project.project_id,
        "project_label": project.label,
        "project_status": project.status,
        "project_summary": project.summary,
        "guardrail_overall_status": probe["guardrail_state"]["overall_status"] if probe.get("guardrail_state") else "missing",
        "supervisor_overall_status": probe["supervisor_state"]["overall_status"] if probe.get("supervisor_state") else "missing",
        "resource_manager_id": probe["guardrail_state"]["manager_id"] if probe.get("guardrail_state") else "",
        "guardrail_plan_decision": probe.get("plan", {}).get("decision", "unknown"),
        "agentdoc_receipts": len(agentdoc_state.get("agents", [])),
        "resource_requests": len(resource_manager_state.get("requests", [])),
        "view_checks": {
            "dashboard_mentions_circleediting": "CircleEditing" in dashboard_view,
            "guardrails_mentions_resource_manager": "circle3d-resource-manager" in guardrails_view,
            "supervisor_mentions_healthy": "healthy" in supervisor_view.lower(),
        },
        "dashboard_excerpt": dashboard_view[:400],
        "guardrails_excerpt": guardrails_view[:400],
        "supervisor_excerpt": supervisor_view[:400],
        "probe": probe,
    }
    return report


def verify_smoke_report(report: dict[str, Any]) -> None:
    if report.get("simulated") is not True:
        raise RuntimeError("Smoke report must explicitly label the artifact as simulated.")
    if report.get("project_id") != DEFAULT_PROJECT_ID:
        raise RuntimeError(f"Unexpected project id: {report.get('project_id')!r}")
    if report.get("project_status") != "running":
        raise RuntimeError(f"Unexpected project status: {report.get('project_status')!r}")
    if report.get("guardrail_overall_status") not in {"ok", "warning"}:
        raise RuntimeError(f"Guardrail status is not acceptable: {report.get('guardrail_overall_status')!r}")
    if report.get("supervisor_overall_status") != "healthy":
        raise RuntimeError(f"Supervisor status is not healthy: {report.get('supervisor_overall_status')!r}")
    if report.get("guardrail_plan_decision") not in {"hold", "restart-requested"}:
        raise RuntimeError(f"Unexpected guardrail plan decision: {report.get('guardrail_plan_decision')!r}")

    checks = report.get("view_checks") or {}
    if not checks.get("dashboard_mentions_circleediting"):
        raise RuntimeError("Dashboard view does not mention CircleEditing.")
    if not checks.get("guardrails_mentions_resource_manager"):
        raise RuntimeError("Guardrails view does not mention the Circle3D resource manager.")
    if not checks.get("supervisor_mentions_healthy"):
        raise RuntimeError("Supervisor view does not look healthy.")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    state_root = args.state_root
    if args.materialize is not None:
        state_root = materialize_smoke_state_root(args.materialize)

    report = build_smoke_report(state_root, project_id=args.project_id)
    verify_smoke_report(report)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
