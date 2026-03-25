# CatfishResearch External Repos And Skills

Checked on `2026-03-25` for CatfishResearch on `dev-intern-02`.

## Scope And Method

- Focus:
  - autonomous research
  - multi-agent orchestration
  - evaluation
  - provider routing
  - monitoring and long-running remote workers
  - prompt and skill packaging
  - structured review
  - diagram and figure generation
  - reasoning patterns such as first-principles and Occam-style simplification
- Primary sources used:
  - official GitHub repos
  - branch-head metadata via `git ls-remote`
  - official `commits/<branch>.atom` and `releases.atom` feeds
  - root `README` and `LICENSE` files when clarification was needed
- Decision rule:
  - prefer small, portable components as external dependencies or narrowly wrapped skills
  - treat full frameworks as architecture references unless Catfish has a clear replacement need

## Executive Shortlist

Most immediately useful for CatfishResearch:

1. `promptfoo/promptfoo`
   - Best near-term addition for structured prompt and agent evaluation, regression checks, and CI gating.
2. `BerriAI/litellm`
   - Best external option for provider routing, fallbacks, and multi-provider normalization, but keep it outside the repo because of mixed open-core licensing and runtime weight.
3. `terrastruct/d2`
   - Best lightweight text-to-diagram tool for architecture figures and workflow diagrams.
4. `wshuyi/research-to-diagram`
   - Best small experimental skill for source-backed knowledge maps if Graphviz becomes a standard dependency.
5. `agentskills/agentskills`
   - Best packaging-spec reference for keeping Catfish manifests compatible with the broader skill ecosystem.
6. `langfuse/langfuse`
   - Best observability reference if Catfish outgrows file-based logs and needs run tracing across workers.

Outcome of this pass:

- No third-party skill code was vendored.
- A concrete manifest was added under `assets/external_repos/`.
- Recommendation: keep upstream code external for now and wrap only the highest-leverage tools in a later implementation pass.

## Installable Small Skills And Components

### 1. K-Dense-AI/claude-scientific-skills

- Repo URL: <https://github.com/K-Dense-AI/claude-scientific-skills>
- Checked date: `2026-03-25`
- Latest visible commit:
  - `cb364cc3d8d0ae7a26367cb61cfd323af5da0ea1` on `2026-03-23T23:27:05Z`
  - branch: `main`
- Latest visible release:
  - `v2.30.1` on `2026-03-23T23:27:19Z`
- Why useful:
  - largest high-quality scientific skill pack in this scan
  - directly relevant to literature review, citation handling, writing, and research support workflows
  - best upstream source when Catfish needs a narrow research subskill instead of a full framework
- Integration cost: `medium`
- License and risk:
  - MIT
  - low license risk
  - operational risk is upstream breadth: bulk copying would add too much noise and overlap existing Catfish skills
- Recommended action:
  - keep as a primary upstream source repo
  - do not vendor wholesale
  - if Catfish later imports anything, cap it at one narrowly scoped skill at a time

### 2. Orchestra-Research/AI-Research-SKILLs

- Repo URL: <https://github.com/Orchestra-Research/AI-Research-SKILLs>
- Checked date: `2026-03-25`
- Latest visible commit:
  - `e1897fa6b1c5caf2b8d07fbac40838791ced62d7` on `2026-03-24T01:47:53Z`
  - branch: `main`
- Latest visible release:
  - `v1.4.0 - Autoresearch: Autonomous AI Research from Idea to Paper` on `2026-03-16T20:29:00Z`
- Why useful:
  - strong upstream source for AI research engineering skills
  - directly relevant to ideation, paper workflows, and autonomous-research scaffolding
  - good prompt design reference when extending Catfish research skills
- Integration cost: `medium`
- License and risk:
  - MIT
  - low license risk
  - main risk is overlap with Catfish's current research pipeline and rapid upstream movement
- Recommended action:
  - reference selectively
  - do not vendor whole categories
  - revisit only if Catfish wants one missing, tightly scoped research-writing skill

### 3. wshuyi/research-to-diagram

- Repo URL: <https://github.com/wshuyi/research-to-diagram>
- Checked date: `2026-03-25`
- Latest visible commit:
  - `c13ec59f3c894da607d7d5b17a18fccdba0bc389` on `2026-01-02T07:13:32Z`
  - branch: `main`
- Latest visible release:
  - no GitHub release entry visible in `releases.atom` on `2026-03-25`
- Why useful:
  - tightly scoped skill for research-backed relationship diagrams
  - especially relevant for concept maps, architecture overviews, and source-attributed knowledge graphs
  - good complement to Catfish's existing paper-figure and paper-illustration flows
- Integration cost: `low` if Graphviz is already standard, otherwise `medium`
- License and risk:
  - MIT
  - low license risk
  - runtime risk: depends on Graphviz and web-search-heavy execution
- Recommended action:
  - mark as the best small-skill pilot if Catfish later chooses to vendor a third-party skill
  - for now, keep external and add only a manifest entry

### 4. promptfoo/promptfoo

- Repo URL: <https://github.com/promptfoo/promptfoo>
- Checked date: `2026-03-25`
- Latest visible commit:
  - `f85704f428a948fb8936d6203e8f58dc0fe830c5` on `2026-03-25T04:12:39Z`
  - branch: `main`
- Latest visible release:
  - `0.121.3` on `2026-03-24T22:53:00Z`
- Why useful:
  - mature CLI and library for LLM evals and red teaming
  - best fit in this scan for regression-testing Catfish prompts, review loops, and agent outputs
  - explicitly supports multi-provider comparisons and CI integration
- Integration cost: `low`
- License and risk:
  - MIT
  - low license risk
  - external dependency risk is low because Catfish can treat it as a CLI tool rather than vendored source
- Recommended action:
  - adopt as an external dependency
  - add Catfish wrappers and canned eval configs in a follow-up implementation pass
  - highest-priority install among the small components

### 5. BerriAI/litellm

- Repo URL: <https://github.com/BerriAI/litellm>
- Checked date: `2026-03-25`
- Latest visible commit:
  - `10a48f7655225b0dc765d5521839a8bf621805d9` on `2026-03-25T02:43:13Z`
  - branch: `main`
- Latest visible release:
  - `v1.82.6.rc.2` on `2026-03-24T03:39:29Z`
- Why useful:
  - strongest widely used routing layer in this scan for provider normalization, fallback routing, quotas, and budget-aware usage
  - good fit if Catfish wants to stop hardcoding provider-specific model adapters
- Integration cost: `medium`
- License and risk:
  - mixed open-core licensing
  - vendor risk is higher than MIT/Apache tools
  - operational risk comes from introducing a gateway layer that changes failure modes and tracing
- Recommended action:
  - use only as an optional external gateway
  - do not vendor or copy source into Catfish
  - gate adoption behind a real routing or failover need

### 6. terrastruct/d2

- Repo URL: <https://github.com/terrastruct/d2>
- Checked date: `2026-03-25`
- Latest visible commit:
  - `93f97201a956189049ebb0f5828c75325e6abc1b` on `2025-10-14T17:57:28Z`
  - branch: `master`
- Latest visible release:
  - `v0.7.1` on `2025-08-19T13:50:56Z`
- Why useful:
  - lightweight, text-native diagram tool for architecture figures, agent workflow diagrams, and reproducible documentation assets
  - lower friction than custom SVG generation for routine architecture sketches
- Integration cost: `low`
- License and risk:
  - MPL-2.0
  - acceptable external-tool risk
  - low operational risk if used as a CLI dependency instead of vendored library code
- Recommended action:
  - install externally
  - add a Catfish wrapper for architecture and control-plane diagrams
  - pair with existing paper-illustration flow rather than replacing it

### 7. agentskills/agentskills

- Repo URL: <https://github.com/agentskills/agentskills>
- Checked date: `2026-03-25`
- Latest visible commit:
  - `b5ce2a438123f9f9c9b167c5af297c048f15395b` on `2026-03-23T19:27:47Z`
  - branch: `main`
- Latest visible release:
  - no GitHub release entry visible in `releases.atom` on `2026-03-25`
- Why useful:
  - open skill specification plus reference SDK
  - directly relevant to prompt and skill packaging, discovery, manifests, and cross-agent portability
  - useful design reference for keeping Catfish external manifests future-compatible
- Integration cost: `low`
- License and risk:
  - Apache-2.0 for code, with docs under separate terms
  - low license risk if Catfish uses the spec and layout ideas instead of copying docs verbatim
- Recommended action:
  - adopt as a packaging-spec reference
  - align Catfish manifests and external-skill metadata to its conventions where practical
  - do not vendor the SDK yet

## Reference-Only Frameworks And Design References

### 8. langchain-ai/langgraph

- Repo URL: <https://github.com/langchain-ai/langgraph>
- Checked date: `2026-03-25`
- Latest visible commit:
  - `e74864ab0cd1b0400b74c5c58b1e8aa89e1f32aa` on `2026-03-24T07:03:16Z`
  - branch: `main`
- Latest visible release:
  - `langgraph-cli==0.4.19` on `2026-03-20T22:12:33Z`
- Why useful:
  - durable graph-based orchestration with explicit state transitions
  - strongest reference for checkpointed multi-step flows if Catfish outgrows prompt-file orchestration
- Integration cost: `high`
- License and risk:
  - MIT
  - low license risk
  - architectural risk is bringing in an entire runtime model that overlaps Catfish's current lightweight execution pattern
- Recommended action:
  - reference only
  - borrow state-machine and checkpoint ideas, not the framework itself

### 9. mastra-ai/mastra

- Repo URL: <https://github.com/mastra-ai/mastra>
- Checked date: `2026-03-25`
- Latest visible commit:
  - `18261c232dd368662e9e29144e5660c8f210e9b6` on `2026-03-25T14:34:45Z`
  - branch: `main`
- Latest visible release:
  - `mastracode@0.9.2` on `2026-03-24T23:01:25Z`
- Why useful:
  - modern agent workflow runtime with tools, memory, observability, and deployment story in one stack
  - useful reference for how to separate orchestration, runtime services, and UI surfaces
- Integration cost: `high`
- License and risk:
  - mixed open-core licensing
  - vendor risk is high
  - operational risk is framework lock-in
- Recommended action:
  - architecture reference only
  - do not copy or adopt wholesale

### 10. microsoft/autogen

- Repo URL: <https://github.com/microsoft/autogen>
- Checked date: `2026-03-25`
- Latest visible commit:
  - `b0477309d2a0baf489aa256646e41e513ab3bfe8` on `2026-03-11T19:42:46Z`
  - branch: `main`
- Latest visible release:
  - `python-v0.7.5` on `2025-09-30T06:18:26Z`
- Why useful:
  - major reference implementation for multi-agent chat, MCP-style tool use, and agent studio patterns
  - good source of ideas for planner-worker-reviewer separation
- Integration cost: `high`
- License and risk:
  - non-standard for software vendoring in Catfish because the repo license file is `Attribution 4.0 International`
  - high policy risk for direct code reuse
- Recommended action:
  - reference only
  - do not vendor code

### 11. OpenHands/OpenHands

- Repo URL: <https://github.com/OpenHands/OpenHands>
- Checked date: `2026-03-25`
- Latest visible commit:
  - `3cd85a07b78a2d9d2e28b2904e1b42096d47a802` on `2026-03-25T12:55:39Z`
  - branch: `main`
- Latest visible release:
  - `1.5.0` on `2026-03-11T18:50:28Z`
- Why useful:
  - strong reference for long-running worker UX, runtime state, sandbox lifecycle, and visible progress handling
  - useful for Catfish monitor and run-status design even though the core product is coding-agent focused
- Integration cost: `high`
- License and risk:
  - mixed open-core licensing
  - high vendor risk
  - replacing Catfish's current lightweight remote-worker pattern would be expensive and unnecessary
- Recommended action:
  - use as a monitoring and runtime-pattern reference only

### 12. assafelovic/gpt-researcher

- Repo URL: <https://github.com/assafelovic/gpt-researcher>
- Checked date: `2026-03-25`
- Latest visible commit:
  - `7c321744ce336949949b1e95b4652e2d455a33f9` on `2026-03-14T13:16:20Z`
  - branch: `main`
- Latest visible release:
  - `v3.4.3` on `2026-03-13T14:06:38Z`
- Why useful:
  - mature open-source deep-research stack with explicit research-to-report workflow
  - strongest report-generation reference in this scan
- Integration cost: `high`
- License and risk:
  - Apache-2.0
  - low license risk
  - architectural overlap is high, so direct adoption would fragment Catfish's current skill-first model
- Recommended action:
  - reference only
  - use for report-structure and planner/researcher flow ideas

### 13. langchain-ai/open_deep_research

- Repo URL: <https://github.com/langchain-ai/open_deep_research>
- Checked date: `2026-03-25`
- Latest visible commit:
  - `b847e54be4859d0e99a2f3782330ce6736e745c4` on `2026-03-19T04:35:14Z`
  - branch: `main`
- Latest visible release:
  - no GitHub release entry visible in `releases.atom` on `2026-03-25`
- Why useful:
  - leaner open deep-research template than the larger end-to-end products
  - good reference for a minimal planner-search-synthesis loop
- Integration cost: `medium-high`
- License and risk:
  - MIT
  - low license risk
  - still too framework-specific to copy into Catfish directly
- Recommended action:
  - reference only
  - use to pressure-test Catfish's own deep-research loop design

### 14. langfuse/langfuse

- Repo URL: <https://github.com/langfuse/langfuse>
- Checked date: `2026-03-25`
- Latest visible commit:
  - `82f6a9cf719238d8dc2b2cf7e49e6a5ad1719ad7` on `2026-03-25T13:26:32Z`
  - branch: `main`
- Latest visible release:
  - `v3.162.0` on `2026-03-24T15:28:17Z`
- Why useful:
  - strongest observability candidate in this scan for traces, experiments, prompt versions, and run analytics
  - especially relevant if Catfish wants monitoring beyond local logs and markdown notes
- Integration cost: `high`
- License and risk:
  - mixed open-core licensing
  - deployment and data-governance cost is the real risk, more than code quality
- Recommended action:
  - reference only for now
  - consider only after Catfish proves a need for central tracing across many concurrent workers

### 15. logikon-ai/awesome-deliberative-prompting

- Repo URL: <https://github.com/logikon-ai/awesome-deliberative-prompting>
- Checked date: `2026-03-25`
- Latest visible commit:
  - `f79a2eca8cfdd528901b147f04718c46f1e9bd67` on `2025-02-03T20:00:33Z`
  - branch: `main`
- Latest visible release:
  - no GitHub release entry visible in `releases.atom` on `2026-03-25`
- Why useful:
  - not an install target, but the best compact reference found here for deliberate reasoning patterns and evaluation vocabulary
  - useful source material for an internal Catfish skill centered on first-principles pruning, Occam-style simplification, and explicit alternative comparison
- Integration cost: `low` as a reading reference
- License and risk:
  - CC0-1.0
  - low reuse risk for ideas
  - not suitable as runtime code because it is a curated reference list
- Recommended action:
  - keep as a reasoning-pattern reference only
  - synthesize Catfish-native prompts from it rather than importing anything mechanically

## Recommendations

### Adopt Externally First

- `promptfoo/promptfoo`
- `terrastruct/d2`
- optionally `BerriAI/litellm` if provider routing pain is real

### Best Small-Skill Pilot If Catfish Later Vendors Something

- `wshuyi/research-to-diagram`

### Best Upstream Skill Libraries To Mine Carefully

- `K-Dense-AI/claude-scientific-skills`
- `Orchestra-Research/AI-Research-SKILLs`

### Best Architecture References

- `langchain-ai/langgraph`
- `OpenHands/OpenHands`
- `langfuse/langfuse`
- `assafelovic/gpt-researcher`

### Best Reasoning-Method Reference

- `logikon-ai/awesome-deliberative-prompting`

## Why Nothing Was Vendored In This Pass

- The strongest upstream skill packs are moving quickly and overlap Catfish's existing skills.
- The most attractive operational additions are external CLIs or services, not portable in-repo snippets.
- The user-owned scope for this pass emphasized curation and planning under `docs/catfish/` and optional manifests, not a broad third-party code intake.
- The best candidate for future vendoring is small enough to revisit later without losing any value by waiting.
