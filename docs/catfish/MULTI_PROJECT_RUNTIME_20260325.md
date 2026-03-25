# Catfish Multi-Project Runtime

## 1. Goal

Catfish must run many research projects in one repository or control domain without collapsing them into one shared workspace. The design target is "isolated execution, unified observation, budget-aware scheduling".

## 2. Project As The Isolation Unit

Each active project gets a `ProjectRuntime` record with its own:

- `projectId`
- `workspaceRoot`
- `artifactRoot`
- `eventLog`
- `scoreLedger`
- `budgetLedger`
- `memoryStore`
- `teamTopology`
- `stageFrontier`
- `projectPostmortemState`

No mutable file path or runtime state should be shared across projects by default.

## 3. Unified Management Without Shared Mutation

The system layer may aggregate read-only summaries from projects:

- current stage
- budget burn
- active child count
- latest score delta
- estimated completion confidence
- last failure class

The system layer may not:

- rewrite a project's artifacts in place
- merge score ledgers
- inject undocumented context into project-local prompts
- reuse project memory in another project without explicit export/import

## 4. Recommended Storage Layout

The architecture does not force the final implementation path, but the following layout keeps isolation explicit:

```text
runtime/
  system/
    scheduler_state.json
    capability_registry_index.json
    global_postmortems/
  projects/
    <project_id>/
      manifest.json
      events/
      scorecards/
      checkpoints/
      artifacts/
      memory/
      postmortems/
```

In this repo's current documentation-first phase, the same structure can exist as examples and generated artifacts before a full service exists.

## 5. Intra-Project High Concurrency

The runtime must support many simultaneous children inside one project while preserving clear ownership.

Recommended controls:

- per-project slot budget
- per-team slot budget
- per-provider concurrency cap
- per-model concurrency cap
- per-stage replay cap

This prevents a single promising stage from consuming the entire system.

## 6. Team Hierarchy

One project can be decomposed into a tree of teams:

```text
project-director
|
+-- ideation-team
|   +-- idea-scout-a
|   +-- idea-scout-b
|   `-- skeptic-a
|
+-- build-team
|   +-- builder-a
|   +-- builder-b
|   `-- verifier-a
|
`-- figure-team
    +-- chart-planner-a
    +-- renderer-a
    `-- caption-editor-a
```

Each internal team node scores only its direct children. It may summarize upstream, but it does not bypass the tree.

## 7. Cross-Project Scheduler

The system scheduler operates over a graph whose root frontier is active projects. It decides:

- which projects receive the next compute slice
- whether to expand exploration or advance integration
- whether to let a project self-update before more spending

Project priority should combine:

- strategic priority from operator policy
- recent realized quality gain
- marginal utility of another slot
- fairness constraints
- remaining budget
- provider availability

## 8. Scheduling Graph Example

```text
SystemRoot
|
+-- Project A: ideation frontier wide, cheap to expand
+-- Project B: implementation blocked, expensive verifier waiting
`-- Project C: figure stage near completion
```

Possible scheduler decision:

- give one extra slot to Project A because exploration value is still high
- keep Project B at current width but route a stronger verifier stack
- finish Project C quickly because its completion unlocks report packaging

This is why the scheduler must be graph-aware rather than queue-only.

## 9. Resource Negotiation

Negotiation happens with explicit resource classes:

- machine slots
- provider quota
- premium model budget
- wall-clock deadlines
- review bandwidth

Each project proposes expansion requests. The scheduler accepts, delays, or shrinks them based on:

- projected value uplift
- current congestion
- diversity needs
- fairness
- deadline pressure

## 10. Failure Containment

If a project enters a bad state, containment should stay local.

Examples:

- provider outage in Project X should not corrupt Project Y scorecards
- runaway replay loops in one team should hit that project's replay cap first
- malformed artifacts in one project should not poison global capability priors until reviewed

System-level policies may react, but the initial blast radius remains bounded.

## 11. Project-Level Self-Update Loop

Every project should periodically ask:

- which stage is over-spending for weak gain
- which stacks consistently underperform
- where integration bottlenecks appear
- whether the current rubric is rewarding the wrong behavior

Outputs:

- updated local priors
- changed frontier width
- tighter or looser critic participation
- revised stage specifications

## 12. Team-Level Self-Update Loop

Teams improve their own operating pattern.

Examples:

- idea team increases skeptic ratio because novelty scores are inflated
- build team adds a verifier child whenever code patch size exceeds threshold
- figure team lowers concurrency but adds stronger merge logic because variants are too redundant

## 13. System-Level Self-Update Loop

The system loop synthesizes evidence across projects.

It may update:

- capability priors
- routing weights
- default concurrency caps
- visualization templates
- alert thresholds

It must not silently rewrite historical project records. Global updates apply prospectively with versioned policy changes.

## 14. Documentation Gates

Before a new project becomes schedulable, Catfish should require:

- project brief
- manifest
- initial team topology
- stage graph
- budget policy
- success definition

Before a new stage expands aggressively, require:

- stage rubric
- capability filters
- replay cap
- artifact naming convention

This makes runtime behavior reproducible and reviewable.

## 15. Visualization Surfaces

The multi-project runtime needs two serious visualization outputs.

### 15.1 Operator View

One system figure showing:

- active projects
- frontier width
- budget burn
- current bottleneck
- recent score trend

### 15.2 Paper-Oriented View

One clean project-tree figure showing:

- hierarchy
- competition sites
- score ownership
- resource flow

These should be generated from the same scheduling graph data, with different formatting layers.

## 16. Implementation Cut Lines

To keep the first version tractable, implement in this order:

1. project manifest and state loader
2. project-local event and scorecard storage
3. project/team/node identifiers and lineage rules
4. cross-project scheduler state object
5. visualization export for hierarchy and frontier snapshots
6. self-update hooks with explicit evidence inputs

Do not start with a full distributed service mesh. A replayable file-backed runtime is sufficient for the first Catfish implementation in this repo.
