---
name: "catfish-first-principles-occam"
description: "Force literature, idea, plan, implementation, writing, or review critique through first principles plus Occam's razor. Use when a research route feels citation-led, benchmark-led, or overbuilt; when a parent node wants a Catfish-native skeptic before scoring; or when the user wants the smallest defensible mechanism and explicit deletion tests before advancing."
---

# Catfish First-Principles + Occam Critique

Use this skill when the job is not to generate more content, but to strip an artifact back to the smallest adequate mechanism before the parent decides whether it should advance.

## Purpose

This skill produces a **critique packet**, not an official scorecard. It is designed for Catfish-style parent nodes that want stronger skeptical pressure during literature review, idea selection, planning, implementation review, writing review, or final packaging.

## Non-Negotiable Catfish Rules

- **Scoring stays with the parent.** This skill may recommend likely pressure on `idea`, `outcomeQuality`, `resourceUsage`, or `risk`, but it never writes the official composite or ledger entry.
- **Competition is stage-agnostic.** The same critique method applies to literature maps, ideas, plans, patches, drafts, figures, and review packets.
- **Papers are evidence, not authority.** Treat citations as mechanism references, assumptions, and failure-mode evidence, not as proof that a copied route is correct.
- **Simplicity wins by default.** Every new module, loss, benchmark, subsystem, or narrative branch needs a direct bottleneck it uniquely solves.

## Required Inputs

- `stage`: `literature` | `idea` | `planning` | `implementation` | `writing` | `figure` | `review`
- `problem_anchor`: what must be solved, plus non-goals
- `artifact_under_review`
- `constraints`: compute, time, data, tooling, venue, deployment limits
- `closest_baseline_or_status_quo`
- optional `candidate_set` if the parent is comparing multiple children

If any required input is missing, reconstruct the smallest reasonable version from the current project state and clearly mark the assumption.

## Deliverable

Write a compact critique memo with these sections:

1. **Irreducible problem**: the problem in plain language with no field jargon.
2. **Necessary assumptions**: what must be true for the artifact to work at all.
3. **Hidden leaps**: where the argument jumps from evidence to wishful thinking.
4. **Deletion table**: every major component, why it exists, and what breaks if removed.
5. **Smallest adequate version**: the leanest artifact still worth testing or advancing.
6. **Failure-triggered simplification**: what to cut first if execution stalls or evidence weakens.
7. **Parent questions**: the highest-leverage unresolved questions before advancement.
8. **Advisory stage pressure**: optional notes on likely upward or downward pressure on `idea`, `outcomeQuality`, `resourceUsage`, `risk`, and diversity value.

## Workflow

### Step 1: Restate the task without jargon

Translate the artifact into plain operational language:

- what goes in
- what changes
- what comes out
- what concrete failure the artifact claims to reduce

If the artifact cannot be explained without abstract labels, the abstraction is probably hiding a weak mechanism.

### Step 2: Build a first-principles ledger

Reduce the artifact to a ledger of:

- objective
- observables
- invariants
- transformations
- constraints
- failure conditions

Every important claim in the artifact should map onto this ledger. If a major claim has no ledger slot, flag it as unsupported.

### Step 3: Separate evidence from prestige

For each cited paper, precedent, or copied recipe, extract:

- the actual mechanism used
- the assumption imported into the current artifact
- the transfer risk under the present constraints
- what would still be true if the citation disappeared

Do not accept "a recent paper did this" as sufficient justification for keeping a mechanism.

### Step 4: Run the Occam sweep

For every major component, training stage, benchmark, evaluator, figure element, or narrative branch, ask:

1. Is it directly tied to the bottleneck?
2. Can an existing component absorb the same job?
3. Can it be delayed until after the core claim is validated?
4. What concrete evidence justifies keeping it now?

Classify each item as:

- `essential`
- `replaceable`
- `premature`
- `vanity`

### Step 5: Produce the minimal counterproposal

Always emit two alternatives:

- **Lean route**: the smallest defensible version worth advancing.
- **Kill route**: the evidence threshold that would justify pruning the artifact entirely.

The lean route is not a rewrite of the same complexity with nicer wording. It must delete real moving parts, claims, or stages.

### Step 6: Apply stage-specific pressure

Use the relevant checks for the current stage.

#### `literature`

- Are we extracting mechanisms and failure modes, or just collecting paper names?
- Which assumptions recur across the cited work?
- What contradictory or negative evidence is being ignored?

#### `idea`

- Is the hypothesis falsifiable?
- What is the cheapest decisive test that could kill it quickly?
- Is the claimed novelty real, or just a renamed composition of standard parts?

#### `planning`

- Does the plan validate the main claim directly, or is it padded with activity?
- Which ablations are essential and which exist only to look complete?
- What is the smallest experiment package that would still convince a skeptical parent?

#### `implementation`

- Is the current patch the smallest patch that could validate the claim?
- Are we rewriting infrastructure because it is easier emotionally than proving the mechanism?
- What can be prototyped or mocked before a deep refactor?

#### `writing`

- Is there one dominant contribution, or several weak ones competing for attention?
- Which claims lack evidence or precise wording?
- What can be deleted without harming the paper's core story?

#### `figure`

- Does the figure surface a decision-relevant fact, or only decorate the story?
- Is the visual encoding faithful to the data and readable in grayscale?
- Can the claim survive if the figure is removed?

#### `review`

- Are critiques tied to evidence and concrete fixes instead of style preferences?
- Is the reviewer identifying downstream risk, not just local annoyance?
- Which finding would actually change the parent decision?

### Step 7: Hand back a parent-facing recommendation

End with one recommendation:

- `advance`
- `hold`
- `replay-after-simplification`
- `prune`

Then justify it with evidence. Do **not** assign the official score or composite.

## Codex Execution Notes

- If explicit subagent delegation is allowed for the task, this skill can be used as the brief for a skeptic child. The skeptic still emits critique only; the parent owns the scorecard.
- If delegation is not allowed, run the full critique locally and preserve the same deliverable structure.

## Anti-Patterns To Call Out Explicitly

- citation accumulation without mechanism extraction
- adding LLM, VLM, RL, or diffusion components because they sound current
- multi-stage plans that are really fear-driven padding
- infrastructure rewrites without clear claim lift
- papers with multiple weak contributions and no dominant thesis
- reviews that punish style while missing risk, evidence, or hidden complexity

## Good Pairings

- Run before `/catfish-stage-bakeoff` to define meaningful diversity axes.
- Run after `/catfish-stage-bakeoff` on finalists to simplify the survivor before parent scoring.
- Pair with `/research-refine`, `/experiment-plan`, `/research-review`, `/paper-write`, or `/paper-figure` when the current route feels bloated.
