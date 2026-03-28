# CircleEditing Production Smoke

This smoke package proves the Catfish control plane can supervise a CircleEditing 3d-edit wave through a file-backed `state-root` and explicit contracts.

The smoke is intentionally synthetic. It is not the live CircleEditing repo, and it does not edit downstream code. It is a realistic control-plane artifact that exercises the same supervision surfaces Catfish uses in production:

- `system/catfish_runtime_policy.json` for the resource manager, CPU reserve, GPU ceiling, and AgentDoc cadence
- `system/resource_manager_state.json` for child approvals and active leases
- `system/agentdoc_state.json` for receipt freshness and heartbeat checks
- `system/supervisor_state.json` for restart budgeting and health
- `projects/circleediting-3d-edit/manifest.json` and `runtime_snapshot.json` for the supervised project itself

## Run It

From the CatfishResearch repo root:

```bash
python tools/catfish_production_smoke.py --output /tmp/catfish-circleediting-smoke.json
```

To materialize the bundled sample state-root into a scratch directory first:

```bash
python tools/catfish_production_smoke.py \
  --materialize /tmp/catfish-circleediting-smoke-root \
  --output /tmp/catfish-circleediting-smoke.json
```

The script fails if any of these are false:

- the CircleEditing project is not present
- guardrails are not `ok` or `warning`
- the supervisor is not `healthy`
- the dashboard does not mention the CircleEditing supervision chain

## What It Proves

The smoke proves the current Catfish shape can:

1. load CircleEditing supervision data from a `state-root`
2. respect parent-owned resource governance
3. enforce AgentDoc freshness
4. render the resulting state through the control-center CLI without touching CircleEditing source files directly

Because the sample is synthetic, it should be treated as a contract test for the control plane rather than a claim about the live downstream project.
