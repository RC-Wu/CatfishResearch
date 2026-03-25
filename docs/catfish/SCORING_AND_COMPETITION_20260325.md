# Catfish Scoring And Competition

## 1. Purpose

This document defines how Catfish compares alternatives, advances winners, and prevents scoring authority from drifting into child nodes. The key rule is simple: competition may happen anywhere, but scoring is always owned by the parent that requested the competition.

## 2. Competition Contract

Every competitive stage uses the same contract.

Inputs:

- parent stage spec
- candidate count or frontier width
- budget envelope
- capability filters
- score rubric
- advancement policy

Child outputs:

- primary artifact
- trace and rationale
- self-critique
- claimed resource usage
- optional confidence and uncertainty notes

Parent outputs:

- one scorecard per child
- comparative ranking
- advancement decision
- merge instruction or replay instruction
- stage postmortem note if the competition exposed rubric failure

## 3. Parent-Only Scoring Rule

Children may estimate their own quality but their estimate is advisory only. The official score is produced by the parent node using both child outputs and independent runtime telemetry.

Forbidden patterns:

- child writes its own composite score into the official ledger
- sibling A writes the official score of sibling B
- system layer overwrites a parent decision without creating a new higher-level decision record

Allowed patterns:

- child emits `selfAssessment`
- parent requests a critic child to produce evidence
- parent uses system-measured resource telemetry in the final scorecard

## 4. Score Dimensions

Each parent scorecard must include the following dimensions on a normalized `0.0` to `1.0` scale.

| Dimension | Meaning | Typical evidence |
| --- | --- | --- |
| `idea` | conceptual novelty, fit, leverage, or insight quality | proposal text, comparison to brief, novelty notes |
| `model` | appropriateness of selected model for this stage | model capability prior, observed completion quality |
| `provider` | routing suitability and operational reliability | latency, failures, quota incidents, consistency |
| `agentGroup` | quality of the chosen team composition | merge success, role coverage, conflict rate |
| `resourceUsage` | efficiency relative to outcome | token use, wall time, slot occupancy, cost |
| `outcomeQuality` | direct quality of the produced artifact | rubric checks, reviewer judgments, tests |
| `risk` | probability of downstream harm or rework | instability, unsupported claims, poor traceability |

The `composite` score is derived from these dimensions using stage-specific weights.

## 5. Stage-Specific Weighting

The weight vector changes by stage; the dimension set does not.

Example default weights:

| Stage | idea | model | provider | agentGroup | resourceUsage | outcomeQuality | risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ideation | 0.30 | 0.10 | 0.05 | 0.15 | 0.10 | 0.20 | 0.10 |
| planning | 0.20 | 0.10 | 0.05 | 0.15 | 0.10 | 0.25 | 0.15 |
| implementation | 0.05 | 0.10 | 0.10 | 0.15 | 0.15 | 0.30 | 0.15 |
| review | 0.05 | 0.10 | 0.10 | 0.10 | 0.10 | 0.30 | 0.25 |
| figure generation | 0.10 | 0.10 | 0.05 | 0.15 | 0.10 | 0.35 | 0.15 |

These are defaults only. Each parent node may override them in its stage spec.

## 6. Composite Score

Recommended calculation:

```text
composite =
  sum(weight[d] * score[d] for d in positive_dimensions)
  - weight[risk] * risk
  + diversity_adjustment
  + confidence_adjustment
```

Where:

- `positive_dimensions` are all dimensions except `risk`
- `diversity_adjustment` rewards candidates that contribute useful exploration against a collapsing frontier
- `confidence_adjustment` is negative when evidence is sparse or contradictory

The parent should store both raw dimensions and final composite. Never keep only the composite.

## 7. Competition Modes

Catfish supports four parent advancement modes.

### 7.1 Winner-Take-All

Use when the stage needs one canonical output, such as selecting a final project plan.

Advance:

- top child only

### 7.2 Top-K Survival

Use in broad search stages such as idea generation.

Advance:

- top `K` children
- optionally with one forced-diversity wildcard

### 7.3 Merge Then Re-Score

Use when multiple children each contain non-overlapping value, such as separate figure drafts or complementary implementation patches.

Advance:

- integrator child receives selected artifacts
- parent re-scores the merged output as a new child candidate

### 7.4 Replay Under Constraint Shift

Use when the parent believes the concept is strong but the stack is wrong.

Replay changes may include:

- different provider
- different model
- different agent-group composition
- tighter budget
- stronger critic involvement

## 8. Competition At Any Stage

Competition is stage-agnostic by design.

Examples:

### 8.1 Idea Generation

Children compete on:

- novelty
- fit to research brief
- expected empirical tractability
- differentiation from nearby candidates

### 8.2 Figure Generation

Children compete on:

- faithfulness to the data
- caption readiness
- readability in grayscale
- density without clutter
- suitability for paper export

### 8.3 Review

Children compete on:

- bug finding depth
- false positive rate
- actionability
- coverage of claims and evidence

This common structure lets Catfish inject "catfish" pressure into any weak stage, not just content generation.

## 9. Anti-Gaming Controls

The scoring system must resist local optimization that harms global quality.

Controls:

- parent-owned ledger only
- score dimensions include efficiency and risk, not just output beauty
- child self-assessment never counts as ground truth
- repeated winner stacks incur diminishing diversity bonus
- a parent may require holdout critics who do not share the builder's model/provider stack
- outcomes with poor traceability are capped even if superficially strong

## 10. Resource Usage Scoring

`resourceUsage` should reward efficient output, not mere cheapness.

Recommended normalization:

```text
resource_efficiency =
  realized_outcome_quality / max(realized_cost, epsilon)
```

Then clip and normalize against stage-specific reference bands.

Important:

- high absolute spend may still score well if it bought clearly superior output in a late, high-value stage
- low spend should not be rewarded if the output is unusable

## 11. Scorecard Lifecycle

1. child finishes or is interrupted
2. telemetry is attached
3. parent fills raw dimension scores
4. parent records evidence references
5. parent computes composite
6. parent writes decision
7. parent optionally writes a superseding scorecard if new evidence arrives

Scorecards are immutable by default. Supersession must reference the earlier scorecard id.

## 12. Minimal Scorecard Fields

The machine-readable scorecard surface should include:

- `scorecardId`
- `parentNodeId`
- `childNodeId`
- `stageId`
- `timestamp`
- `weights`
- `scores`
- `composite`
- `decision`
- `decisionReason`
- `evidenceRefs`
- `resourceSnapshot`
- `supersedes`

See `docs/catfish/schemas/scorecard.schema.json`.

## 13. Example Parent Decision Patterns

### 13.1 Narrow Idea Frontier

If three ideas score similarly on `outcomeQuality` but one uses a distinct provider-model-group stack and materially increases exploration coverage, the parent should advance that candidate or keep it as the wildcard survivor.

### 13.2 Figure Drafts

If one figure is visually strong but slightly misleading and another is accurate but dense, the parent should prefer merge-then-re-score instead of picking the visually cleaner artifact outright.

### 13.3 Cheap Builder Versus Expensive Builder

If the expensive builder only marginally improves implementation quality while consuming much more budget, the parent should lower its `resourceUsage` score and likely replay the cheaper stack with one stronger critic rather than keep paying the premium.

## 14. Relationship To Scheduling

Scorecards do not only rank siblings. They feed back into the scheduling graph as:

- realized reward
- updated capability priors
- failure penalties
- frontier pruning signals

This is how local parent judgments influence system-wide resource negotiation without violating isolation.
