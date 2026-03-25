# CatfishResearch Skill Install And Integration Plan

Checked on `2026-03-25`.

## Decision Summary

- Do not vendor third-party skill code in this pass.
- Keep upstream frameworks external.
- Prefer three near-term external integrations:
  - `promptfoo` for evaluation
  - `d2` for routine architecture diagrams
  - optional `litellm` gateway only if Catfish needs provider routing and failover
- Keep `research-to-diagram` as the leading pilot if Catfish later decides to vendor exactly one outside skill.

## Why This Plan Is Better Than Bulk Skill Copying

- Catfish already has strong native research and remote-worker skills.
- The highest-value gaps are not missing prompt text. They are:
  - structured regression evaluation
  - optional provider routing abstraction
  - low-friction diagram generation
  - better manifesting of external sources
- Pulling in large upstream skill packs now would increase overlap, review burden, and maintenance without solving those sharper gaps.

## Install Waves

### Wave 0: Done In This Pass

- added a Catfish curation note under `docs/catfish/`
- added a machine-readable external manifest under `assets/external_repos/`
- classified candidates into:
  - small installable components
  - reference-only frameworks and design references

### Wave 1: Fast, High-Leverage External Tools

#### 1. Promptfoo

- Goal:
  - make Catfish prompts and agent outputs regression-testable
- Proposed integration:
  - add a small Catfish wrapper that emits `promptfooconfig.yaml` from local task artifacts
  - store canned eval suites for:
    - research-summary quality
    - review quality
    - instruction-following and citation hygiene
    - long-running worker status quality
- Expected cost: `1-2` focused implementation sessions
- Exit criteria:
  - one sample Catfish eval suite runs locally
  - one baseline report can be regenerated from committed fixtures

#### 2. D2

- Goal:
  - generate maintainable workflow and architecture diagrams from text
- Proposed integration:
  - add a wrapper script or doc convention for `.d2` sources next to Catfish docs
  - use it for:
    - control-plane diagrams
    - worker-monitor-finalizer lifecycle diagrams
    - research pipeline overviews
- Expected cost: `low`
- Exit criteria:
  - one Catfish architecture diagram is checked in from a `.d2` source

#### 3. LiteLLM

- Goal:
  - centralize provider routing, failover, and model aliasing only if Catfish starts juggling too many providers
- Proposed integration:
  - keep it as an optional sidecar or gateway
  - do not make Catfish depend on it for normal local use
- Expected cost: `medium`
- Exit criteria:
  - one optional route profile works end-to-end without changing Catfish's default no-gateway path

### Wave 2: Narrow Skill Intake, If Still Needed

This wave should happen only after Wave 1 proves a real gap remains.

#### Candidate A: research-to-diagram

- Why first:
  - smallest portable skill in the shortlist
  - direct value for source-backed concept maps and architecture visuals
- Preconditions:
  - Graphviz is standardized on the target machine
  - Catfish wants diagram generation beyond current paper-illustration coverage
- Intake rule:
  - wrap or vendor only the narrow skill folder
  - preserve source attribution and original license
  - isolate all machine-specific assumptions behind a Catfish wrapper

#### Candidate B: One Subskill From K-Dense Or Orchestra

- Why second:
  - both repos are large enough that selective import is mandatory
- Preconditions:
  - a concrete Catfish gap is identified that existing native skills do not already cover
- Intake rule:
  - import at most one skill at a time
  - capture upstream commit SHA in the manifest
  - rewrite path assumptions and keep the diff narrow

### Wave 3: Architecture Borrowing, Not Framework Adoption

#### Borrow From LangGraph

- explicit durable state transitions
- resumable checkpoints for long jobs
- graph-shaped orchestration documentation

#### Borrow From OpenHands

- better run-status surfaces
- clearer worker lifecycle states
- improved runtime and log discoverability

#### Borrow From Langfuse

- prompt version lineage
- trace IDs across worker runs
- experiment/result observability vocabulary

#### Borrow From GPT-Researcher And Open Deep Research

- clearer planner -> search -> synthesis split
- stronger report artifact conventions
- more explicit source accounting in generated outputs

## Reasoning-Skill Opportunity

No clean off-the-shelf repo in this scan should be copied into Catfish for first-principles or Occam-style reasoning. The right move is to author a Catfish-native skill later using:

- Catfish's existing `research-refine`, `peer-review`, and remote-worker patterns
- references from `logikon-ai/awesome-deliberative-prompting`

Target behavior for that future internal skill:

- force one sharp problem statement
- compare a minimal route against one frontier-native alternative
- penalize contribution sprawl
- require explicit simplification and assumption pruning
- require a short "why this is the smallest adequate mechanism" section

## Concrete Next Actions

1. Implement a small `promptfoo` integration path first.
2. Add a minimal `d2` wrapper or documented rendering convention second.
3. Reassess whether Catfish still needs a provider gateway. If yes, pilot `litellm` externally.
4. Delay all skill vendoring until one real missing workflow remains after those tool integrations.
5. If vendoring later happens, start with `research-to-diagram`, not a mega skill pack.

## Non-Recommendations

- Do not copy `langgraph`, `mastra`, `autogen`, `OpenHands`, or `gpt-researcher` into Catfish.
- Do not bulk-import `K-Dense-AI/claude-scientific-skills` or `Orchestra-Research/AI-Research-SKILLs`.
- Do not introduce `langfuse` until Catfish truly needs centralized tracing.

## Acceptance Criteria For A Follow-Up Implementation Pass

- one reproducible prompt evaluation suite exists
- one text-authored diagram path exists
- optional routing stays optional
- no duplicated mega-skill trees are added to Catfish
