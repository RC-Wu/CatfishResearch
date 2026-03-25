# Catfish Diversity And Competition Policy

## 1. Purpose

This document defines Catfish's explicit diversity policy for competitive execution. It extends the parent-owned scoring contract in [SCORING_AND_COMPETITION_20260325.md](SCORING_AND_COMPETITION_20260325.md), the routing constraints in [PROVIDER_ROUTING_20260325.md](PROVIDER_ROUTING_20260325.md), the system invariants in [ARCHITECTURE_20260325.md](ARCHITECTURE_20260325.md), and the future control-plane surface in [CONTROL_CENTER_20260325.md](CONTROL_CENTER_20260325.md).

The policy is normative for every Catfish stage:

- idea
- planning
- implementation
- experiment
- evaluation
- writing
- figures
- routing
- resource allocation

The machine-readable companion example lives at `assets/catfish_policy/diversity_policy.example.json`.

## 2. Core Rule

Every competitive child is scored as a bundle, not as a prompt in isolation. The bundle is:

`{provider, model, prompt_style, agent_role, group_strategy, evidence_plan}`

That rule exists because Catfish is trying to select working execution ecologies, not merely better strings. A good answer from a weak stack can be useful, but the parent should still know whether the win came from:

- provider reliability
- model capability
- prompt framing
- role selection
- team topology
- evidence quality

## 3. Diversity Axes

Catfish tracks six explicit diversity axes.

| Axis | Meaning | Why it matters |
| --- | --- | --- |
| `provider` | provider, gateway, or account route | avoids routing monoculture and quota or outage brittleness |
| `model` | model family and reasoning tier | separates "frontier depth" from "cheap throughput" assumptions |
| `prompt_style` | prompt family such as divergent ideation, checklist planning, skeptical review, or deterministic rendering | avoids overfitting to one instruction dialect |
| `agent_role` | role identity such as scout, planner, builder, critic, evaluator, writer, plotter, router, allocator | forces role-specific pressure instead of undifferentiated workers |
| `group_strategy` | topology such as solo, builder-plus-critic, swarm-plus-integrator, red-team, or paired-judge | captures coordination quality as a first-class decision variable |
| `evidence_type` | evidence families such as novelty notes, tests, telemetry, benchmark results, citations, render specs, or holdout judgments | prevents one fragile evidence mode from dominating selection |

`provider` and `model` are partly operational. The other four axes are how Catfish avoids turning every stage into the same frontier model with the same prompt and the same team pattern.

## 4. Two Kinds Of Diversity

Catfish distinguishes exploration diversity from evaluation diversity.

### 4.1 Exploration Diversity

Goal:

- widen the frontier
- expose hidden good ideas and group strategies
- avoid premature convergence

Default behavior:

- broad frontiers
- forced wildcard survival
- more prompt and role variation
- cheaper or less-proven stacks are still allowed if budget is bounded

Use exploration diversity when:

- the parent uncertainty is high
- the stage is early or reversible
- the scheduler needs coverage more than certainty

### 4.2 Evaluation Diversity

Goal:

- challenge claims with independent evidence
- reduce false positives
- identify brittle winners before downstream lock-in

Default behavior:

- smaller frontiers
- stronger independence requirements
- at least one holdout judge or evidence source that does not share the builder's full stack when alternatives are available

Use evaluation diversity when:

- a candidate is about to be promoted
- the stage writes scorecards or gate decisions
- the cost of a false positive exceeds the cost of one more independent check

## 5. Stage Policy

The summary matrix is maintained in [STAGE_COMPETITION_MATRIX_20260325.md](STAGE_COMPETITION_MATRIX_20260325.md). The normative rules are below.

### 5.1 Idea

Competition unit:

- idea bundle: hypothesis, scope, initial evidence plan, and execution ecology

Exploration policy:

- default mode: `top-k-survival` with one wildcard
- prioritize prompt-style, role, and group-strategy diversity
- keep at least one candidate that differs materially in evidence plan, not just wording

Evaluation policy:

- narrow to candidates with novelty notes plus tractability notes
- require at least two evidence types from `{problem brief, novelty check, baseline gap, feasibility estimate}`
- if possible, use a critic stack that differs on provider or model from the proposing stack

Collapse rule:

- allow narrowing once novelty and tractability are independently corroborated
- do not collapse both `agent_role` and `evidence_type` before idea selection is final

### 5.2 Planning

Competition unit:

- execution plan bundle: milestones, risks, dependencies, and evaluation plan

Exploration policy:

- compare planner-heavy, skeptic-heavy, and integrator-heavy group strategies
- force at least one candidate with an explicitly different sequencing strategy, not only different phrasing

Evaluation policy:

- require schedule evidence and risk evidence
- plans should be judged by implementation fitness, not prose polish alone

Collapse rule:

- allow narrowing when one plan dominates on dependency clarity and downstream testability
- retain at least one alternative evidence type until the plan is accepted

### 5.3 Implementation

Competition unit:

- patch bundle: code changes, tests, rationale, and risk note

Exploration policy:

- compete solo builders against builder-plus-critic and merge-oriented groups
- keep model or prompt variation smaller than in ideation, but still non-zero
- prefer evidence types that can be executed, not just argued

Evaluation policy:

- require executable evidence from `{unit tests, integration tests, static checks, repro steps}`
- at least one reviewer stack must differ from the selected builder on provider or model when the healthy route set allows it
- no implementation candidate self-grades into promotion

Collapse rule:

- builder frontier may narrow after repeated wins with passing tests and low rework risk
- even after builder collapse, evaluation must retain either stack independence or evidence-type independence

### 5.4 Experiment

Competition unit:

- experiment run plan or result bundle: config, ablations, metrics, and run provenance

Exploration policy:

- compete benchmark slices, ablation plans, and analysis prompts
- allow more group-strategy diversity than pure implementation because experiment design benefits from disagreement

Evaluation policy:

- require at least one quantitative evidence type and one reproducibility-oriented evidence type
- examples: benchmark metric plus seed sweep, or main result plus holdout rerun

Collapse rule:

- collapse is allowed only after the claimed effect survives at least one independent rerun or holdout slice

### 5.5 Evaluation

Competition unit:

- evaluation bundle: rubric, judge stack, benchmark slice, and evidence aggregation method

Exploration policy:

- compare eval templates, judge roles, and metric bundles
- preserve evidence-type diversity aggressively because judge monoculture is the main failure mode

Evaluation policy:

- this is the strictest stage for independence
- at least one judge or scoring path must differ from the builder stack on more than prompt wording when alternatives exist
- require mixed evidence, typically from `{benchmark, trace audit, failure-case sample, model-graded review, human or operator spot-check}`

Collapse rule:

- do not collapse to a single evidence type
- collapse to one judge stack is only acceptable when provider health or resource failure removes alternatives, and the scorecard must record that degradation explicitly

### 5.6 Writing

Competition unit:

- section draft bundle: text, citations or evidence refs, self-critique, and revision note

Exploration policy:

- compete outline-first, evidence-first, and editor-style prompt families
- vary roles between author, skeptic editor, and compression editor

Evaluation policy:

- require at least one evidence type tied to upstream artifacts, not only narrative quality
- examples: scorecard refs, experiment tables, code paths, or citation checks

Collapse rule:

- late-stage writing may collapse to one authoring stack for consistency
- factual review must remain independent whenever feasible

### 5.7 Figures

Competition unit:

- figure bundle: data slice, renderer prompt or spec, caption draft, and readability checks

Exploration policy:

- compete renderer styles and layout strategies from the same underlying data
- do not mistake "different data choice" for renderer diversity unless the stage explicitly allows data slicing competition

Evaluation policy:

- require evidence from `{data provenance, caption audit, grayscale readability, axis-label check, paper-export fit}`
- at least one evaluator should focus on faithfulness rather than aesthetics

Collapse rule:

- final renderer may narrow to a single stack for consistency
- data provenance and caption auditing must remain independent of the final rendering prompt

### 5.8 Routing

Competition unit:

- route bundle: provider, model, reasoning effort, search mode, and browser mode

Exploration policy:

- routing diversity is conditional on health and quota reality
- when multiple healthy routes exist, explore at least one non-default route for early-stage or uncertain work
- when only one healthy provider exists, keep model and evidence diversity elsewhere instead of pretending provider diversity exists

Evaluation policy:

- late-stage high-value evaluations should prefer stable routes with known success history
- a holdout evaluator route should differ from the builder route if health allows it

Collapse rule:

- route collapse is allowed when provider health, quota pressure, or repeated route wins make the frontier effectively one-dimensional
- the scorecard should record whether collapse was chosen for quality reasons or forced by health

### 5.9 Resource Allocation

Competition unit:

- allocation bundle: frontier width, budget slice, priority, and retry policy assigned to candidate branches

Exploration policy:

- compete resource strategies, not just task outputs
- examples: many-cheap-wide search versus narrower expensive search, or mixed frontier with one wildcard reserve

Evaluation policy:

- allocation plans are judged by realized reward, survival quality, fairness across projects, and waste
- evidence must include actual spend or occupancy telemetry, not intuition alone

Collapse rule:

- collapse to a narrow budget policy is allowed when one allocation strategy repeatedly dominates on realized reward per unit cost
- keep at least one reserve lane for re-inflation when uncertainty rises again

## 6. When Narrowing Is Allowed

Catfish is allowed to collapse a frontier to a narrower stack only when all of the following are true:

1. The parent score and evidence indicate the remaining uncertainty is materially lower than the cost of continued wide search.
2. The leading candidate has survived at least one evaluation path that is not identical to the builder path on every axis.
3. The collapse reason is explicit:
   - quality dominance
   - operational degradation
   - budget scarcity
   - packaging consistency
4. The retained winner still has enough evidence for later audit.

Global anti-collapse rules:

- never collapse scoring authority into the child
- never remove all evidence-type diversity from evaluation
- never claim provider diversity when router health currently makes it impossible
- after a forced collapse, re-inflate the frontier if score variance rises, failures recur, or health changes reopen alternatives

## 7. Machine-Readable Contract

The policy artifact consumed by scheduler, reviewer, and control-center workers should contain:

- `schemaVersion`
- `policyId`
- `updatedAt`
- `axisDefinitions`
- `references`
- `stages`

Each stage entry should contain:

- stage identity and class
- competition unit
- primary advancement mode
- `explorationPolicy`
- `evaluationPolicy`
- `collapsePolicy`

Each policy mode must define:

- candidate and advancement counts
- axis coverage expectations for all six axes
- required evidence types
- intended frontier behavior

The example JSON is designed to be:

- easy for schedulers to read
- strict enough for validators to reject missing stage coverage
- loose enough to evolve without forcing a full runtime implementation today

## 8. Why These Choices

These choices are informed by Catfish's own architecture plus several external projects, but the policy is not copied from any of them.

### 8.1 Catfish Internal Constraints

- [ARCHITECTURE_20260325.md](ARCHITECTURE_20260325.md) makes competition stage-agnostic and requires explicit accounting for provider, model, and agent-group choice.
- [SCORING_AND_COMPETITION_20260325.md](SCORING_AND_COMPETITION_20260325.md) makes parent-only scorecards the control surface for advancement.
- [PROVIDER_ROUTING_20260325.md](PROVIDER_ROUTING_20260325.md) shows that provider diversity is health-constrained, not wishful.
- [CONTROL_CENTER_20260325.md](CONTROL_CENTER_20260325.md) implies the policy must be inspectable by a future dashboard and event stream.

### 8.2 External Reference Inputs

- `promptfoo/promptfoo`
  - useful reference for declarative eval matrices, side-by-side comparisons, and CI-style gating
- `openai/evals`
  - useful reference for benchmark registries and reusable eval templates
- `UKGovernmentBEIS/inspect_ai`
  - useful reference for multi-turn, tool-using, model-graded evaluation components
- `BerriAI/litellm`
  - useful reference for treating provider and model routing as an explicit bundle with fallback and cost signals
- `langchain-ai/langgraph`
  - useful reference for durable graph execution and human intervention points, which supports stage-local policy instead of one monolithic agent loop
- `microsoft/autogen`
  - useful reference for making roles and multi-agent patterns first-class rather than implicit prompt variations
- `FoundationAgents/MetaGPT`
  - useful reference for SOP-like role decomposition across planning and implementation stages
- `crewAIInc/crewAI`
  - useful reference for explicit crew topology and event-driven flow separation
- `OpenHands/OpenHands`
  - useful reference for implementation-stage agent execution and scaling coding workers
- `langfuse/langfuse`
  - useful reference for traceable evidence, metrics, datasets, and eval observability
- `terrastruct/d2`
  - useful reference for treating figure generation as a reproducible renderer specification, not an opaque image prompt
- `agentskills/agentskills`
  - useful reference for keeping policy packaging machine-readable and portable

Concrete Catfish adaptations:

- Catfish elevates `group_strategy` and `evidence_type` into the policy itself, not just runtime metadata.
- Catfish separates exploration diversity from evaluation diversity instead of using one "more variation is always better" rule.
- Catfish allows route collapse when provider health is constrained, but requires that collapse to be recorded rather than hidden.

## 9. Operational Reading

If a scheduler needs a short interpretation:

- early stages should spend diversity budget on `prompt_style`, `agent_role`, and `group_strategy`
- late critical stages should spend diversity budget on `evidence_type` and independent evaluation
- `provider` diversity is desirable but subordinate to real provider health
- Catfish may narrow the builder frontier, but should keep evaluation independence alive as long as viable alternatives exist
