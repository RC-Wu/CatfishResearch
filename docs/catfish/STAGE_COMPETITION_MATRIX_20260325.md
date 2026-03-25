# Catfish Stage Competition Matrix

This matrix is the compact operational view of the policy in [DIVERSITY_AND_COMPETITION_20260325.md](DIVERSITY_AND_COMPETITION_20260325.md).

Axis legend:

- `P` = provider
- `M` = model
- `S` = prompt style
- `R` = agent role
- `G` = group strategy
- `E` = evidence type

Notation:

- `P2/M2/...` means target distinct count during that policy mode
- `min` means the lowest acceptable distinct count before the policy is considered degraded
- `fixed` means the axis is intentionally not diversified in that mode

## 1. Stage Matrix

| Stage | Competition Unit | Exploration Targets | Evaluation Targets | Default Advancement | Collapse Allowed When | Required Evidence Focus |
| --- | --- | --- | --- | --- | --- | --- |
| `idea` | idea bundle | `P2 min1 / M2 min1 / S4 min3 / R4 min3 / G3 min2 / E3 min2` | `P2 min1 / M2 min1 / S2 min2 / R2 min2 / G2 min1 / E3 min2` | `top-k-survival + wildcard` | novelty and tractability are independently corroborated | novelty check, baseline gap, feasibility note |
| `planning` | execution plan bundle | `P2 min1 / M2 min1 / S3 min2 / R3 min2 / G3 min2 / E3 min2` | `P2 min1 / M2 min1 / S2 min1 / R2 min2 / G2 min1 / E3 min2` | `top-k-survival`, then `winner-take-all` | dependency clarity and testability materially dominate alternatives | milestone plan, dependency risk, verification path |
| `implementation` | patch bundle | `P2 min1 / M2 min1 / S2 min1 / R3 min2 / G3 min2 / E3 min2` | `P2 min1 / M2 min1 / S1 fixed / R2 min2 / G2 min1 / E4 min3` | `merge-then-re-score` or `winner-take-all` | passing executable evidence plus repeated low-risk wins | tests, static checks, repro steps |
| `experiment` | run-plan or result bundle | `P2 min1 / M2 min1 / S3 min2 / R3 min2 / G3 min2 / E4 min3` | `P2 min1 / M2 min1 / S2 min1 / R2 min2 / G2 min1 / E4 min3` | `top-k-survival`, then `merge-then-re-score` | claimed effect survives independent rerun or holdout slice | metrics, ablations, reruns, provenance |
| `evaluation` | rubric-and-judge bundle | `P2 min1 / M2 min1 / S3 min2 / R3 min2 / G3 min2 / E4 min3` | `P2 min1 / M2 min1 / S2 min1 / R3 min2 / G2 min1 / E4 min3` | `winner-take-all` for scorecard owner, `merge` for evidence | never to one evidence type; single judge only if health forces it | benchmark, trace audit, failure samples, holdout review |
| `writing` | section draft bundle | `P2 min1 / M2 min1 / S3 min2 / R3 min2 / G2 min1 / E3 min2` | `P2 min1 / M2 min1 / S2 min1 / R2 min2 / G2 min1 / E3 min2` | `merge-then-re-score` | consistency benefits outweigh wider drafting and factual review stays independent | artifact refs, citations, table refs, scorecards |
| `figures` | figure bundle | `P2 min1 / M2 min1 / S3 min2 / R3 min2 / G2 min1 / E4 min3` | `P2 min1 / M2 min1 / S1 fixed / R2 min2 / G2 min1 / E4 min3` | `merge-then-re-score` then `winner-take-all` | final rendering stack is stable and faithfulness checks remain separate | data provenance, caption audit, readability checks |
| `routing` | route bundle | `P2 min1 / M2 min1 / S1 fixed / R2 min1 / G1 fixed / E2 min1` | `P2 min1 / M2 min1 / S1 fixed / R2 min1 / G1 fixed / E2 min1` | `winner-take-all` with replay on constraint shift | provider health, quota pressure, or repeated route wins collapse the frontier | health snapshot, capability ledger, parent score |
| `resource_allocation` | allocation bundle | `P1 fixed / M1 fixed / S2 min1 / R2 min1 / G3 min2 / E3 min2` | `P1 fixed / M1 fixed / S1 fixed / R2 min1 / G2 min1 / E3 min2` | `winner-take-all` with reserve lane | one budget policy repeatedly dominates on realized reward per cost | spend telemetry, occupancy, survival quality |

## 2. Stage Notes

### Idea

- Spend diversity budget on `S`, `R`, and `G`.
- Keep one wildcard survivor unless budget is critically constrained.

### Planning

- Compete sequencing strategies, not only wording.
- Low-risk prose with weak verification should lose to uglier but executable plans.

### Implementation

- Builder diversity may shrink earlier than evaluator diversity.
- `E` is the hard floor in late implementation because executable proof matters more than stylistic variety.

### Experiment

- Evidence diversity is the main protection against fragile headline metrics.
- A rerun or holdout slice is the preferred collapse gate.

### Evaluation

- This stage is not allowed to become monocultural on evidence.
- If router health removes provider alternatives, compensate with different roles, group strategy, and evidence types.

### Writing

- Collapse to one authoring stack is acceptable near packaging time.
- Keep at least one factual or evidence-linked reviewer alive.

### Figures

- Rendering diversity is useful; data provenance diversity is mandatory.
- A beautiful figure with weak provenance should lose.

### Routing

- Routing diversity is bounded by live health.
- If only one healthy provider exists, record degraded provider diversity instead of faking it.

### Resource Allocation

- This stage competes frontier-width strategies and retry policies.
- A narrow, high-confidence plan should still reserve capacity for re-inflation if uncertainty spikes.

## 3. Collapse Summary

| Stage | Can Builder Frontier Collapse? | Must Evaluation Stay Diverse? | Typical Re-Inflation Trigger |
| --- | --- | --- | --- |
| `idea` | yes | yes | new contradiction, novelty overlap, or weak tractability |
| `planning` | yes | yes | missed dependency or infeasible milestone |
| `implementation` | yes | yes | test failures, rework spikes, or reviewer disagreement |
| `experiment` | yes | yes | non-reproducible result or holdout regression |
| `evaluation` | only partially | always on `E`, preferably also `P` or `M` | judge disagreement or evidence sparsity |
| `writing` | yes | yes | factual conflict or unsupported claim |
| `figures` | yes | yes on provenance and caption audit | data mismatch or readability failure |
| `routing` | yes | yes if alternatives reopen | provider recovery or ledger drift |
| `resource_allocation` | yes | yes on telemetry evidence | reward variance or queue pressure change |
