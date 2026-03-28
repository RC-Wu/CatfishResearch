# Provider and Module Scout Operations

CatfishResearch now has two small executable surfaces that connect the control-plane models to file-backed runtime artifacts:

`tools/catfish_provider_doctor.py`
- Reads the provider registry, provider health snapshot, and capability ledger.
- Resolves provider base URLs from env-backed configuration first, then registry fallbacks.
- Emits a failover-aware route preview and a detailed provider doctor report.
- When `--write` is used, writes `system/provider_route_preview.json` and `system/provider_doctor_report.json` into a Catfish `state-root`.

`tools/catfish_module_scout.py`
- Reads the existing `system/self_optimization.json` contract/state.
- Merges explicit allowlist manifests from `assets/external_repos/`.
- Evaluates candidates through the existing Catfish scoring logic.
- Can persist the normalized scout state back into `system/self_optimization.json`.
- Can materialize a bounded install bundle inside a caller-provided scratch directory.

## Safety Rules

- No secret values are written into the repo.
- Provider configuration is env-backed by name only.
- Module scout install attempts stay inside an explicit scratch root.
- Network cloning is opt-in with `--allow-network`.
- Skill conversion is explicit and materializes a local bundle instead of mutating downstream projects.

## Typical Commands

```bash
python tools/catfish_provider_doctor.py scan --state-root /path/to/state-root --write
python tools/catfish_module_scout.py scan --state-root /path/to/state-root --write
python tools/catfish_module_scout.py install --state-root /path/to/state-root --candidate-id candidate:promptfoo --scratch-root /tmp/catfish-scout
```

## State Artifacts

- `system/provider_route_preview.json`
- `system/provider_doctor_report.json`
- `system/self_optimization.json`
- `system/module_scout_runs` entries inside the scout state

The control center will pick up `provider_route_preview.json` on the next live-state load and mark the selected provider as active.
