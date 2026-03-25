# Catfish Effect System Architecture

## 1. Intent

The Catfish Effect system is a documentation-first orchestration architecture for autonomous research. Its purpose is to make one repository support:

- multiple isolated research projects under one unified control surface
- very high concurrency inside a single project
- hierarchical agent teams with role-specific subagents
- competition at any stage of work, not only at final review
- parent-owned scoring and selection at every node
- explicit accounting for idea quality, model choice, provider choice, agent-group design, resource usage, and final outcome quality
- self-improvement at project, team, and system scopes

The design is deliberately implementation-oriented. Each major concept below maps to a future runtime object, file contract, or scheduling decision instead of remaining a vague orchestration metaphor.

## 2. Non-Negotiable Invariants

1. Project isolation is stronger than management convenience. Unified management must not allow one project to mutate another project's state, budget, or artifacts.
2. Scoring is parent-only. A child may emit candidates, traces, confidence, and self-critique, but only the parent node writes the scorecard that decides advancement.
3. Any stage may become competitive. Idea generation, literature search, planning, implementation, review, figure generation, and final packaging all share the same competition contract.
4. Capability metadata is explicit. Models, providers, agent roles, and agent groups are not selected from memory; they are selected through declared `Capability.md` metadata plus observed performance.
5. Scheduling is graph-based, budget-aware, and iterative. Allocation is not a fixed pipeline; it is an expanding and pruning search over possible next actions.
6. Documentation is part of the runtime. The system does not treat docs as after-the-fact reporting. Stage specs, scorecards, capability sheets, and postmortems are runtime inputs.

## 3. System View

The architecture has four layers.

| Layer | Scope | Owns | Never Owns |
| --- | --- | --- | --- |
| Catfish system | whole repository or control domain | global routing policy, capability registry, shared resource market, cross-project scheduler, visualization exports | project-local artifacts, project secrets |
| Project runtime | one research project | project plan, project budget, stage graph, local memory, team roster, project postmortems | other projects' mutable state |
| Team runtime | one hierarchical group inside a project | child assignment, parent scoring, local strategy, role mix, retries | global routing policy |
| Node runtime | one stage execution unit | candidate generation, child expansion requests, evidence emission, trace capture | its own final score |

A paper-friendly structural view:

```text
CatfishSystem
|
+-- GlobalCapabilityRegistry
|   +-- provider/*/Capability.md
|   +-- model/*/Capability.md
|   +-- agent-role/*/Capability.md
|   `-- agent-group/*/Capability.md
|
+-- ResourceMarket
|   +-- machine pools
|   +-- provider quotas
|   `-- budget policies
|
+-- CrossProjectScheduler
|   `-- SchedulingGraph(root = all active projects)
|
`-- ProjectRuntime[*]
    +-- ProjectManifest
    +-- ProjectKnowledgeBase
    +-- TeamRuntime(root)
    |   +-- TeamRuntime(child groups)
    |   `-- NodeRuntime(leaves and internal stages)
    +-- ProjectScoreLedger
    `-- ProjectPostmortemLoop
```

## 4. Core Runtime Objects

### 4.1 ProjectManifest

One manifest describes the project boundary and the root stage graph.

Required fields:

- `projectId`
- `workspaceRoot`
- `artifactRoot`
- `budgetPolicy`
- `priority`
- `defaultIsolationClass`
- `stageGraph`
- `teamTopology`
- `documentationGate`

The manifest is the scheduler's unit of isolation. If the manifest is paused, all descendant nodes are paused without affecting other projects.

### 4.2 TeamRuntime

A team is a parent node with strategy authority over a set of children. Teams are recursive, so a project can express:

- a root project director team
- subteams for ideation, planning, build, review, and figure generation
- deeper role-specific teams such as `idea-scout`, `skeptic`, `coder`, `editor`, `plotter`, or `paper-critic`

Each team owns:

- child creation policy
- capability filters
- scoring rubric weights
- retry and pruning policy
- local memory visible to descendants
- the parent-owned score ledger for its children

### 4.3 NodeRuntime

A node is a single stage execution context. Nodes can be:

- `stage-parent`
- `competitive-leaf`
- `integrator`
- `reviewer-parent`
- `terminal`

Every node implements the same lifecycle:

1. load stage spec and parent context
2. request resources and candidate child actions
3. execute or expand children
4. collect candidate artifacts and traces
5. have the parent score children
6. advance winners, merge outputs, or terminate

### 4.4 CompetitionCell

Competition is not a special subsystem bolted onto idea generation. It is the default execution primitive of any parent node.

A CompetitionCell contains:

- one parent decision context
- `N` child candidates
- one score rubric
- one budget envelope
- one advancement policy

Examples:

- idea generation: many idea scouts compete on novelty and fit
- implementation: two builders and one skeptic compete on patch quality and risk
- figure generation: multiple renderer groups compete on clarity, faithfulness, and publication-readiness

### 4.5 ScoreCard

The parent writes one scorecard per child candidate. A scorecard is append-only except for explicit supersession by the same parent revision.

Minimum dimensions:

- `idea`
- `model`
- `provider`
- `agentGroup`
- `resourceUsage`
- `outcomeQuality`
- `risk`
- `composite`

The scorecard is the only object that can move a child from "candidate" to "selected", "held", "replayed", or "pruned".

### 4.6 CapabilityRegistry

Catfish depends on a documentation-backed capability registry instead of implicit operator memory. The registry normalizes metadata for:

- providers
- models
- agent roles
- agent groups

Each entity publishes a `Capability.md` with stable front matter plus explanatory body text. The front matter is machine-readable; the body is human-auditable rationale and operational notes.

## 5. Capability.md Mechanism

The required `Capability.md` mechanism is the bridge between paper-grade documentation and machine selection logic.

### 5.1 Required Semantics

Every capability document must answer:

- what the entity is
- what stages it is allowed to operate in
- what it is good at
- what it is bad at
- what it costs
- what latency and throughput profile it has
- what failure modes are common
- how much parallelism it tolerates
- what evidence supports its current priors

### 5.2 Canonical Locations

Recommended future layout:

```text
registry/
  providers/<provider_id>/Capability.md
  models/<model_id>/Capability.md
  agent-roles/<role_id>/Capability.md
  agent-groups/<group_id>/Capability.md
```

### 5.3 Selection Logic

The scheduler and parent teams use capability documents for:

- hard filtering
  - allowed stages, security class, required tools, max parallelism
- prior estimation
  - expected quality, cost, latency, reliability
- diversity shaping
  - avoid all candidates using the same provider-model-role stack
- postmortem updates
  - revise priors after measured results

This avoids two common failures:

- choosing an expensive model because it is famous instead of fit-for-stage
- over-using one successful team layout until it becomes brittle

## 6. Multi-Project Isolation With Unified Management

The Catfish system must let one operator observe and schedule many projects without allowing projects to contaminate each other.

### 6.1 Isolation Boundaries

Per project, isolate:

- workspace root
- artifact root
- event log
- score ledger
- budget ledger
- prompt history
- derived memory cache
- secret namespace

Cross-project components may read summaries but may not write into another project's roots except through explicit import/export contracts.

### 6.2 Unified Management Surface

The system layer provides:

- one project table with health, budget, current frontier, and recent wins
- one scheduling graph across projects
- one capability registry
- one visualization export pipeline

This yields centralized visibility without shared mutable project state.

## 7. High-Concurrency Runtime Inside One Project

The project runtime must support bursty parallelism because research stages often benefit from many weakly correlated attempts.

Concurrency model:

- wide speculative expansion in early stages
- narrower, higher-cost branches in build and verification
- reinflation of competition when the parent confidence interval is too wide

The root project team may run, for example:

- 12 ideation leaves
- 4 literature synthesis leaves
- 3 plan integrators
- 6 implementation leaves
- 4 review leaves
- 5 figure-generation leaves

The design requirement is not "maximum simultaneous processes" but "parallel attempts whose outputs remain attributable, comparable, and prunable".

## 8. Hierarchical Agent Groups

Catfish formalizes agent groups because one flat pool cannot express the necessary coordination patterns.

Recommended group types:

| Group type | Typical parent role | Typical children |
| --- | --- | --- |
| director | sets stage policy | planners, critics, budgeters |
| scout swarm | searches wide solution space | idea scouts, paper scouts, baseline scouts |
| builder cell | executes concrete changes | coder, tester, verifier |
| critic panel | attacks proposed outputs | skeptic, reproducibility checker, style reviewer |
| renderer studio | produces figures and tables | chart planner, renderer, caption editor |
| integrator | merges winners | editor, consistency checker, final packager |

Each group itself gets a `Capability.md` because group composition affects performance independently of any single child model.

## 9. Parent-Only Scoring

Parent-only scoring is a hard architectural rule, not a convention.

Why:

- prevents self-reward hacking
- keeps selection authority aligned with stage goals
- makes score provenance auditable
- allows different parent teams to use different rubrics without retraining children

Enforcement model:

- child nodes write artifacts, traces, self-critique, and claimed costs
- system runtime writes observed cost and resource telemetry
- only the parent writes the official scorecard and advancement decision
- siblings never score each other directly

This means a node cannot advance itself by claiming a high self-score.

## 10. Scheduling Graph And Search

The runtime scheduler is not a linear queue. It is a graph search process over possible allocations and next actions.

### 10.1 Graph Definition

Each graph node represents:

- project or team context
- partial allocation of resources
- current frontier of candidate tasks
- accumulated evidence and scores
- remaining budget

Edges represent actions such as:

- launch child candidate
- deepen a promising branch
- replay a branch with a different provider or model
- merge winners
- pause, prune, or archive
- trigger self-update before further expansion

### 10.2 MCTS-Like Behavior

The design should feel closer to budgeted tree search than FIFO scheduling.

Recommended selection score:

```text
selection_value =
  exploitation_mean
  + c_puct * prior * sqrt(parent_visits) / (1 + child_visits)
  + diversity_bonus
  - cost_penalty
  - risk_penalty
```

Where:

- `prior` comes from `Capability.md` plus historical performance
- `exploitation_mean` comes from realized parent-written composite scores
- `diversity_bonus` discourages collapsing too early onto one stack
- `cost_penalty` reflects remaining budget and queue pressure
- `risk_penalty` reflects failure history and constraint violations

This is "MCTS-like" rather than literal Monte Carlo search because some rollouts are real agent executions and some are lightweight forecasts.

### 10.3 Negotiation

Negotiation occurs at three levels:

- system level
  - which project gets shared compute or provider quota next
- project level
  - which team gets more budget or parallel slots
- team level
  - which candidate children are expanded, replayed, or stopped

## 11. Self-Update Loops

Catfish learns at three scopes.

### 11.1 Project-Level Self-Update

Adjusts:

- stage rubrics
- project-local capability priors
- project templates
- project memory compaction rules

Input:

- local score histories
- postmortems
- observed bottlenecks

### 11.2 Team-Level Self-Update

Adjusts:

- role mix
- parent prompt policy
- retry strategy
- competition width and pruning thresholds

Input:

- child score distributions
- disagreement rates
- merge failure modes

### 11.3 System-Level Self-Update

Adjusts:

- global capability priors
- cross-project scheduling policy
- provider routing preferences
- visualization defaults and review thresholds

Input:

- aggregated outcomes across projects
- provider incidents
- measured latency and cost envelopes

Update writes must remain scoped. A project cannot directly mutate system policy; it can only submit evidence or proposals upstream.

## 12. Documentation-First Workflow

The Catfish runtime should begin with docs, not treat docs as cleanup.

Required documents before execution:

- project brief
- stage spec
- capability references
- score rubric
- budget envelope
- acceptance criteria

Required documents after execution:

- parent scorecards
- selection decision note
- stage postmortem
- updated capability evidence if relevant

This makes every competition cell inspectable after the fact and suitable for later paper figures or methodology sections.

## 13. Visualization Strategy

Visualization must be serious and publication-friendly.

Design rules:

- default to grayscale-safe linework with one accent color at most
- prefer DAG or tree layouts with explicit parent-child ownership
- annotate edges with budget, decision, and score deltas instead of decorative badges
- export SVG and PDF-friendly layouts first; dashboards are secondary
- avoid dense neon node-link diagrams that cannot survive printing

Recommended canonical figures:

1. System stack diagram
2. Project runtime hierarchy
3. Competition cell sequence diagram
4. Scheduling graph snapshot with frontier highlighting
5. Score breakdown chart per stage

These figures should be generated from structured graph data, not manually redrawn each time.

## 14. Repository Landing Zones

This repo currently contains docs and lightweight tools. A practical future implementation path is:

```text
docs/catfish/
  ARCHITECTURE_20260325.md
  SCORING_AND_COMPETITION_20260325.md
  MULTI_PROJECT_RUNTIME_20260325.md
  ROADMAP_20260325.md
  schemas/

tools/catfish/
  manifests.py
  capability_registry.py
  scoring.py
  scheduler.py
  visualization.py
  update_loops.py

tools/examples/catfish/
  project_manifest.example.json
  scheduling_graph.example.json
```

This keeps the repository consistent with its current "docs plus portable tools" philosophy.

## 15. Immediate Implementation Priorities

The first code wave should implement the minimum viable contracts, not a full autonomous operating system.

Priority order:

1. project manifest loader and validation
2. capability registry parser for `Capability.md`
3. scorecard writer with parent-only enforcement
4. scheduling-graph state object and replayable event log
5. visualization export from scheduling graph
6. self-update hooks backed by explicit postmortem inputs

If these six pieces exist, the Catfish architecture becomes executable without overbuilding the first iteration.
