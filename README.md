# CatfishResearch

[中文版 README](README_CN.md) | English

CatfishResearch is the current identity of this repository. It keeps the ARIS workflow lineage visible, but the active framing is Catfish: a docs-first, file-backed research control plane with a small runtime core, provider routing, a backend-first control center, and explicit provenance for every stage of the stack.

The project stays conservative about claims. If a capability is only documented, it is treated as a contract or roadmap item. If it is implemented, the README points at the file path that actually exists.

## What Exists Now

- `docs/catfish/` holds the Catfish architecture, routing, control-center, and roadmap docs.
- `tools/catfish_runtime.py`, `tools/catfish_route_core.py`, `tools/catfish_route_eval.py`, `tools/catfish_remote_dispatch.py`, `tools/codex_route_preview.py`, and `tools/cc_switch_bridge.py` provide the runtime and control-plane helpers.
- `apps/catfish-control-center/` contains the current control-center CLI and dashboard code.
- `assets/router/` stores the provider registry, provider health snapshot, and capability ledger used by routing.
- `skills/skills-codex/` preserves the Codex-native skill tree alongside the upstream `skills/` lineage.

## Current Control Center Status

The control center is not a web app. It is a backend-first CLI that renders materialized snapshots or live `state-root` data.

Supported inputs:

- `--snapshot` for a materialized JSON snapshot.
- `--state-root` for a live Catfish state tree with `system/` and `projects/` files.

Supported views include:

- `dashboard`
- `projects`
- `stage-competitions`
- `pending-reviews`
- `provider-status`
- `recent-launches`
- `capability-summaries`
- `diversity-metrics`
- `recent-events`

Example:

```bash
python apps/catfish-control-center/main.py \
  --state-root /path/to/catfish-state \
  --view dashboard
```

The live-state path is documented in [`docs/catfish/CONTROL_CENTER_LIVE_20260325.md`](docs/catfish/CONTROL_CENTER_LIVE_20260325.md). The original scaffold remains in [`docs/catfish/CONTROL_CENTER_20260325.md`](docs/catfish/CONTROL_CENTER_20260325.md) for historical reference.

## Production Safety Goals

CatfishResearch is designed to be inspectable and replayable before it is ambitious.

- File-backed state is preferred over hidden in-memory behavior.
- Parent-owned scoring stays explicit in the competition and review docs.
- Provider selection is gated by registry, health, quota, and capability data.
- The control center reads the same snapshot/state contracts that the runtime writes.
- The repo avoids claiming a durable service, database, or web UI that does not exist yet.

These constraints are part of the current baseline, not a future aspiration.

## Onboarding Direction

The onboarding path for new downstream work, including 3d-edit, should start from the Catfish project contract rather than from a one-off integration:

1. Define the project boundary in a Catfish manifest.
2. Materialize a runtime snapshot under a `state-root`.
3. Let the control center read the same files that the runtime and dispatcher already understand.
4. Add project-specific docs under `docs/catfish/` only when they describe real implementation behavior.

That keeps onboarding uniform and avoids introducing a special-case runtime too early.

## Provenance

CatfishResearch inherits the ARIS workflow lineage, but it is not presented as an ARIS footnote.

- ARIS is the upstream workflow and historical provenance.
- CatfishResearch is the repository identity used in this worktree.
- The merge record is preserved in [`docs/catfish/MERGE_ARIS_20260325.md`](docs/catfish/MERGE_ARIS_20260325.md).
- The older ARIS-oriented README is preserved in [`docs/legacy/README_ARIS_20260328.md`](docs/legacy/README_ARIS_20260328.md).

## Start Here

- [`docs/catfish/INDEX_20260325.md`](docs/catfish/INDEX_20260325.md)
- [`docs/catfish/ARCHITECTURE_20260325.md`](docs/catfish/ARCHITECTURE_20260325.md)
- [`docs/catfish/RUNTIME_ENGINE_20260325.md`](docs/catfish/RUNTIME_ENGINE_20260325.md)
- [`docs/catfish/PROVIDER_ROUTING_20260325.md`](docs/catfish/PROVIDER_ROUTING_20260325.md)
- [`docs/catfish/REMOTE_DISPATCH_20260325.md`](docs/catfish/REMOTE_DISPATCH_20260325.md)
- [`docs/catfish/ROADMAP_20260325.md`](docs/catfish/ROADMAP_20260325.md)
- [`docs/catfish/CONTROL_CENTER_LIVE_20260325.md`](docs/catfish/CONTROL_CENTER_LIVE_20260325.md)

If you need the ARIS-era workflow narrative, use the legacy README reference instead of the main README.
