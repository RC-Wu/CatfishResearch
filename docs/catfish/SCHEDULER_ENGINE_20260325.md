# Catfish Scheduler Engine

## Purpose

`tools/catfish_scheduler.py` is the missing file-backed scheduler layer that sits on top of `tools/catfish_runtime.py`.

The runtime already stores projects, nodes, competitions, runs, and parent verdicts. The scheduler added here is responsible for deciding what to do next:

- expand a competitive frontier
- deepen a promising branch
- replay a branch under a shifted stack
- force parent review when scoring is pending
- prune weak or budget-harming branches

The implementation stays lightweight:

- standard library only
- JSON graph on disk
- no daemon
- no background queue
- replayable action log

## Files

- `tools/catfish_project_graph.py`
  - graph format, stage defaults, diversity policy, schema-style snapshot export
- `tools/catfish_scheduler.py`
  - best-first scheduler, route integration, budget checks, CLI
- `tools/tests/test_catfish_scheduler.py`
  - focused tests for competition defaults, diversity pressure, parent-only review, pruning, and CLI flow
- `assets/catfish_scheduler_examples/competitive_research_graph.example.json`
  - small graph example

## Competition By Default

Competition is now encoded into every standard stage:

- `idea`
- `planning`
- `implementation`
- `evaluation`
- `writing`
- `figure`

Each stage defaults to:

- `competition_mode="top-k"`
- `min_competitors >= 2`
- explicit frontier width
- replay cap
- stage-local pruning threshold

That means idea generation, planning, implementation, evaluation, writing, and figure work all behave as competitive cells, not a single-lane pipeline.

## Diversity As A First-Class Constraint

Each stage carries `diversity_targets` with explicit controls for:

- provider diversity
- model diversity
- agent-group diversity
- style diversity
- anti-collapse stack share threshold

Selection adds a diversity bonus when an action introduces a missing provider, model, agent group, or style before the frontier has diversified enough. It subtracts an anti-collapse penalty when the scheduler keeps trying to deepen the same full stack too early.

Important detail:

- targets are clipped to what is actually feasible
- if only one provider is launchable, provider diversity does not create an impossible constraint
- model, agent-group, and style diversity still apply

This lets the scheduler stay diversity-aware without deadlocking under real provider outages or quota blocks.

## Search Behavior

The scheduler is best-first with an MCTS-like scoring shape:

```text
selection_value =
  exploitation
  + c_puct * prior * sqrt(parent_visits) / (1 + visits)
  + diversity_bonus
  + action_bias
  - cost_penalty
  - replay_or_failure_penalty
```

Inputs:

- `exploitation`
  - official parent scores only
- `prior`
  - provider route score plus stage priors
- `parent_visits`
  - stage frontier traffic
- `diversity_bonus`
  - new provider/model/group/style coverage
- `cost_penalty`
  - project and stage budget pressure
- `replay_or_failure_penalty`
  - repeated failures or replay loops

Supported explicit actions:

- `expand`
- `deepen`
- `replay`
- `review`
- `prune`

## Parent-Only Scoring

The scheduler never treats child self-scores as official evidence.

Branch ranking uses:

- `branch.parent_scores`
- runtime-backed parent verdicts when present

Branch self-estimates can be stored, but they are ignored for official scheduling decisions.

When a branch is complete but unscored, the scheduler emits `review` instead of promoting or deepening it. This keeps the runtime and scheduler aligned with the parent-only scoring contract already defined in `tools/catfish_runtime.py` and `docs/catfish/SCORING_AND_COMPETITION_20260325.md`.

## Provider And Capability Integration

The scheduler builds directly on the existing Catfish routing assets:

- `assets/router/catfish_provider_registry.json`
- `assets/router/catfish_provider_health_20260325.json`
- `assets/router/catfish_capability_ledger.json`
- `tools/catfish_route_core.py`

For `expand` and `replay`, the scheduler evaluates provider-tier variants with the existing route logic, then mixes that with diversity pressure and budgets.

The result is:

- provider eligibility is enforced
- capability history influences priors
- unhealthy or quota-blocked providers are filtered out
- diversity can still shift model, agent-group, and style choices on the healthy provider

## CLI

Bootstrap from runtime operations:

```bash
python3 tools/catfish_scheduler.py bootstrap \
  --ops /path/to/runtime_ops.json \
  --project-id proj-alpha \
  --graph-out /tmp/proj-alpha.scheduler.json
```

Recommend the next action:

```bash
python3 tools/catfish_scheduler.py next-action \
  --graph /tmp/proj-alpha.scheduler.json
```

Apply the chosen action back into the graph:

```bash
python3 tools/catfish_scheduler.py next-action \
  --graph /tmp/proj-alpha.scheduler.json \
  --apply
```

Render a schema-style scheduling snapshot:

```bash
python3 tools/catfish_scheduler.py snapshot \
  --graph /tmp/proj-alpha.scheduler.json \
  --schema
```

## What The First Version Does Not Attempt

This engine intentionally does not implement:

- a daemon
- worker execution
- leases or locks
- distributed coordination
- automatic parent scoring

It decides and records the next orchestration step. That is the right first implementation boundary for this repository’s current Catfish layer.
