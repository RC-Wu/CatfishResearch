# Catfish Parent Review And Capability Updates

## Scope

This document defines the parent-review and capability-update engine added on 2026-03-25. The implementation lives in:

- `tools/catfish_parent_review.py`
- `tools/catfish_capability_apply.py`

The goal is narrow and operational:

- only the parent node writes official scorecards and verdicts
- every child run can still contribute metadata, traces, self-assessment, and evidence
- the parent review emits both normalized scorecards and incremental capability updates that fit the current Catfish runtime and provider router

## Parent-Only Invariant

The review tool enforces two authorship checks before it emits official artifacts:

1. `official_writer_node_id` must equal `parent_node_id`
2. every official `evaluator_note.author_node_id` must equal `parent_node_id`

Child self-assessments are preserved only as advisory inputs inside the scorecard. They do not become official scores, verdicts, or capability ledger rows.

## Supported Dimensions

Every official scorecard requires all eight normalized dimensions:

- `idea`
- `model`
- `provider`
- `agent_group`
- `diversity_contribution`
- `resource_usage`
- `outcome_quality`
- `risk`

The scorecard stores the full eight-dimension view in snake case. It also emits a `legacy_projection` that maps the existing seven schema-compatible dimensions back to the current `scorecard.schema.json` surface for older consumers. `diversity_contribution` stays in the new normalized scorecard because the v1 schema did not reserve a field for it.

## Decision Modes

`catfish_parent_review.py` supports two official advancement modes:

- `winner_pick`
  - emits one selected winner
  - non-winners can still be marked `replay`, `hold`, `merge`, or `pruned`
- `portfolio_keep`
  - still emits one runtime winner for compatibility with `tools/catfish_runtime.py`
  - additionally records `retained_run_ids` and per-child `survive` decisions in verdict metadata so the parent can keep multiple children alive

Portfolio retention is diversity-aware. The parent review keeps a secondary child when it is close enough on composite score or contributes a meaningfully different provider/model/agent-group stack with high `diversity_contribution`.

## Output Surfaces

The review tool emits one JSON artifact with three important surfaces.

### 1. Normalized Scorecards

Each scorecard includes:

- parent and child ids
- stage metadata
- normalized weights
- all eight normalized dimensions
- raw and normalized composite values
- official decision and decision reason
- evidence references
- advisory child inputs
- a schema-compatible legacy projection

### 2. Runtime Verdict

The `runtime_verdict` field is shaped to pass directly into `CatfishRuntime.apply_parent_verdict(...)`:

- `verdict_id`
- `competition_id`
- `parent_node_id`
- `score_by_run_id`
- `capability_updates`
- `winner_run_id`
- `rationale`
- `submitted_at`
- `metadata`

The metadata carries the portfolio details and the full capability update audit log.

### 3. Router Capability Updates

The `router_capability_updates.entries` field is append-only provider memory for the existing router ledger:

- one provider row per reviewed child run
- current task category, difficulty, reasoning tier, and reasoning length
- inherited `parentScore`
- `routingEffect` and `scoreDelta`
- source review, verdict, and scorecard ids
- evidence references and dimension snapshots for auditability

## Incremental Apply Layer

`tools/catfish_capability_apply.py` applies review output without destructive overwrite:

- router entries are appended by id
- duplicate ids are skipped, not rewritten
- each apply pass writes an `auditLog` entry
- runtime application is emitted as an `apply_parent_verdict` operation for existing runtime operation streams

This keeps capability updates replayable and reviewable instead of silently mutating prior observations.

## Example Flow

Input:

- `assets/catfish_review_examples/portfolio_keep_input.json`

Generate review artifact:

```bash
python3 tools/catfish_parent_review.py \
  --input assets/catfish_review_examples/portfolio_keep_input.json \
  --output assets/catfish_review_examples/portfolio_keep_review_output.json
```

Apply router/runtime updates:

```bash
python3 tools/catfish_capability_apply.py \
  --review assets/catfish_review_examples/portfolio_keep_review_output.json \
  --ledger assets/router/catfish_capability_ledger.json \
  --project-id proj-parent-review
```

The example keeps one official winner plus one diversity-preserving survivor. The runtime still receives a compatible `winner_run_id`, while the parent verdict metadata records the extra retained child so the frontier does not collapse prematurely.

## Test Coverage

Focused tests live in `tools/tests/test_catfish_parent_review.py` and cover:

- parent-only authorship enforcement
- winner-pick verdict generation
- portfolio retention driven by diversity
- append-only capability application and runtime operation emission
- direct compatibility with the current `CatfishRuntime`
