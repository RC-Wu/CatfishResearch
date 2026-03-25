---
name: catfish-stage-bakeoff
description: Run a Catfish-native competitive generation stage across ideas, planning, implementation, writing, review, and figure work. Use when a parent should request multiple diverse child candidates under one rubric and then score them parent-side, instead of accepting the first plausible draft.
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, WebSearch, WebFetch
---

# Catfish Stage Bakeoff

Use this skill to turn any stage into a controlled competition with explicit diversity pressure, shared artifact contracts, and **parent-only scoring**.

## Purpose

This skill is the generic Catfish competition playbook. It is not limited to diagram generation. It can be used for:

- idea generation
- literature synthesis
- planning
- implementation
- writing
- review
- figure generation

If the stage would benefit from more than one plausible route, run a bakeoff instead of over-trusting the first draft.

## Required Stage Spec

Before generating any candidates, the parent must define:

- `stage_id`
- `parent_goal`
- `artifact_contract`
- `candidate_count` or frontier width
- `budget_envelope`
- `capability_filters`
- `diversity_axes`
- `score_rubric`
- `advancement_mode`

If any field is missing, infer the narrowest safe default and mark it in the stage note.

## Non-Negotiable Catfish Rules

- **The parent owns all official scores.** Children may emit `selfAssessment`, but never the official scorecard or composite.
- **Diversity is upstream of scoring.** Do not generate `N` cosmetic rewrites of the same route and then pretend the stage was competitive.
- **Advancement is stage-specific, not ego-specific.** If the strongest concept is paired with the wrong stack, replay under a better constraint mix instead of forcing the weak run to win.
- **Merge requires re-score.** If two children are merged, the merged artifact is a new candidate that must be scored by the parent.

## Candidate Packet Contract

Every child in the bakeoff should return:

- primary artifact
- short rationale
- self-critique
- uncertainty or open-risk note
- claimed resource usage
- mergeability note

The parent must be able to compare candidates side by side without reconstructing their intent from scratch.

## Workflow

### Step 1: Freeze the parent contract

Write a one-block stage contract that includes:

- stage and objective
- candidate count
- budget ceiling
- diversity axes
- stage-specific rubric
- advancement mode
- explicit note: `scoring_policy = parent-only`

### Step 2: Force diversity before generation

Each candidate should differ on at least **two** meaningful axes whenever possible:

- hypothesis or problem framing
- mechanism or decomposition
- provider or model stack
- agent-group or reviewer lens
- budget level
- evidence plan
- final presentation style

Superficial wording changes do not count as diversity.

### Step 3: Generate candidate families by stage

Use the relevant playbook for the stage.

#### `literature`

Generate 2-4 competing syntheses that differ in what they optimize for:

- mechanism-centric map
- benchmark/failure-mode map
- trend-and-gap map
- critical anti-hype map

#### `idea`

Generate 3-6 competing ideas that differ in:

- causal hypothesis
- intervention point
- empirical tractability
- novelty story

At least one candidate should be a diversity wildcard rather than a polished version of the leading cluster.

#### `planning`

Generate 2-4 plans with different risk curves, for example:

- minimal decisive plan
- balanced paper-ready plan
- fast falsification plan
- high-upside but risky plan

#### `implementation`

Generate 2-3 implementation routes, for example:

- surgical patch
- adapter or shim layer
- deeper but cleaner refactor

Each route should state what it touches, how it will be validated, and what rework risk it creates.

#### `writing`

Generate 2-3 narrative routes, for example:

- bottleneck-first argument
- empirical-discovery argument
- method-first argument

Routes should differ in claim structure and evidence ordering, not just sentence wording.

#### `review`

Generate 2-4 reviewer passes with different lenses:

- correctness skeptic
- empirical sufficiency skeptic
- simplicity skeptic
- narrative or claim skeptic

The parent can then combine or prune findings after comparison.

#### `figure`

Generate 2-4 visual routes, for example:

- comparison-first figure
- mechanism-first diagram
- ablation-focused table/plot layout
- paper-export conservative layout

Diagram generation is one instance of this stage, not the whole skill.

### Step 4: Collect child packets without letting children self-score

Children may include:

- confidence
- self-assessment
- estimated risk

But they must **not** emit the official scorecard, official ranking, or final decision.

### Step 5: Score with the parent rubric

Use the Catfish score dimensions:

- `idea`
- `model`
- `provider`
- `agentGroup`
- `resourceUsage`
- `outcomeQuality`
- `risk`

Keep raw dimension scores plus the final composite. Never keep only the composite.

Recommended default stage weights:

| Stage | idea | model | provider | agentGroup | resourceUsage | outcomeQuality | risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| literature | 0.25 | 0.05 | 0.05 | 0.15 | 0.10 | 0.25 | 0.15 |
| idea | 0.30 | 0.10 | 0.05 | 0.15 | 0.10 | 0.20 | 0.10 |
| planning | 0.20 | 0.10 | 0.05 | 0.15 | 0.10 | 0.25 | 0.15 |
| implementation | 0.05 | 0.10 | 0.10 | 0.15 | 0.15 | 0.30 | 0.15 |
| writing | 0.10 | 0.10 | 0.05 | 0.10 | 0.10 | 0.35 | 0.20 |
| review | 0.05 | 0.10 | 0.10 | 0.10 | 0.10 | 0.30 | 0.25 |
| figure | 0.10 | 0.10 | 0.05 | 0.15 | 0.10 | 0.35 | 0.15 |

Apply diversity and confidence adjustments on the parent side only.

### Step 6: Choose an advancement mode

Select one of the standard Catfish modes:

- `winner-take-all`
- `top-k-survival`
- `merge-then-re-score`
- `replay-under-constraint-shift`

Use `top-k-survival` with a diversity wildcard in search-heavy stages. Use `merge-then-re-score` when different children each hold non-overlapping value.

### Step 7: Write the parent decision note

Record:

- per-child scorecard
- ranking
- advancement decision
- reason for any wildcard or replay
- postmortem note if the rubric failed to separate obviously different candidates

## Anti-Patterns

- generating multiple near-clones and calling it competition
- letting a child write the official score or choose the winner
- applying diversity only to visual styling, not to mechanisms or stacks
- merging two candidates and forgetting to re-score the merged artifact
- optimizing for polish while ignoring `resourceUsage` or `risk`

## Good Pairings

- Run `/catfish-first-principles-occam` before the bakeoff to design sharper diversity axes.
- Run `/catfish-first-principles-occam` after parent scoring on the winner to remove unnecessary complexity before implementation or packaging.
- Pair with `/research-refine`, `/experiment-plan`, `/research-review`, `/paper-write`, `/paper-figure`, and `/mermaid-diagram` when those stages need true alternatives instead of one-shot output.
