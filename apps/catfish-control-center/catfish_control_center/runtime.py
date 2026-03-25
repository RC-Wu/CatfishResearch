from __future__ import annotations

import importlib.util
from dataclasses import replace
from pathlib import Path
from typing import Any

from .models import ControlEvent, ControlSnapshot, ProviderState
from .storage import JsonSnapshotStore


REPO_ROOT = Path(__file__).resolve().parents[3]
ROUTE_PREVIEW_PATH = REPO_ROOT / "tools" / "codex_route_preview.py"


def load_snapshot(snapshot_path: Path) -> ControlSnapshot:
    return JsonSnapshotStore(snapshot_path).load()


def merge_recent_events(snapshot: ControlSnapshot, events: list[ControlEvent]) -> ControlSnapshot:
    merged = tuple(sorted((*snapshot.events, *events), key=lambda event: event.timestamp))
    return replace(snapshot, events=merged)


def _load_route_preview_module() -> Any:
    spec = importlib.util.spec_from_file_location("codex_route_preview", ROUTE_PREVIEW_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load route preview module from {ROUTE_PREVIEW_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def apply_route_preview(
    snapshot: ControlSnapshot,
    *,
    config_path: Path,
    machine_id: str,
    task_kind: str,
    difficulty: str,
    requested_profile: str | None = None,
    locked_profile: str | None = None,
) -> ControlSnapshot:
    route_module = _load_route_preview_module()
    config = route_module.load_json(config_path)
    route_preview = route_module.select_route(
        config,
        machine_id=machine_id,
        task_kind=task_kind,
        difficulty=difficulty,
        requested_profile=requested_profile,
        locked_profile=locked_profile,
    )

    providers: tuple[ProviderState, ...] = tuple(
        replace(provider, selected=(provider.profile_id == route_preview["profileId"]))
        for provider in snapshot.providers
    )
    metadata = dict(snapshot.metadata)
    metadata["route_preview_source"] = str(config_path)
    return replace(snapshot, providers=providers, route_preview=route_preview, metadata=metadata)
