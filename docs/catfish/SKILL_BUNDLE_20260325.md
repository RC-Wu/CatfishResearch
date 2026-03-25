# Catfish Skill Bundle Additions

This note records the Catfish-native skills added on 2026-03-25 to make competition and diversity explicit across research stages instead of treating them as mostly a figure-generation concern.

## Added Skills

| Surface | Skill | Purpose |
| --- | --- | --- |
| `skills/` | `catfish-first-principles-occam` | first-principles and Occam critique for literature, ideas, plans, implementation routes, writing, figures, and review packets |
| `skills/skills-codex/` | `catfish-first-principles-occam` | Codex-native version of the same critique workflow with local-or-delegated execution notes |
| `skills/` | `catfish-stage-bakeoff` | generic multi-stage competitive generation with diversity axes, child packet contracts, and parent-owned scorecards |
| `skills/skills-codex/` | `catfish-stage-bakeoff` | Codex-native version of the same bakeoff workflow with parent-held scoring and optional delegated generation notes |

## What These Skills Change

The bundle now has Catfish-specific guidance for two complementary jobs:

1. **First-principles simplification pressure**
   - challenge literature maps, ideas, plans, implementation routes, drafts, and review findings from mechanism-first reasoning
   - force deletion tests and "smallest adequate mechanism" reasoning
   - keep papers as evidence instead of authority

2. **Cross-stage competitive generation**
   - run explicit bakeoffs at idea, literature, planning, implementation, writing, review, and figure stages
   - require meaningful diversity on hypotheses, mechanisms, stacks, or reviewer lenses before scoring
   - keep official scoring with the parent only

## Competitive Stage Coverage

The new `catfish-stage-bakeoff` skill explicitly covers these competitive stages:

- `literature`: competing synthesis styles such as mechanism-centric, benchmark/failure-mode, trend-and-gap, and anti-hype maps
- `idea`: competing hypotheses, intervention points, and novelty stories, including a diversity wildcard
- `planning`: competing risk curves such as minimal decisive, balanced paper-ready, fast falsification, and high-upside plans
- `implementation`: competing patch strategies such as surgical patch, adapter layer, and deeper refactor
- `writing`: competing narratives such as bottleneck-first, empirical-discovery, and method-first structures
- `review`: competing critic passes such as correctness, empirical sufficiency, simplicity, and narrative skepticism
- `figure`: competing visual routes such as comparison-first, mechanism-first, and conservative export-ready layouts

Diagram generation remains a valid figure-stage use case, but it is now only one example inside a broader cross-stage competition contract.

## Parent-Only Scoring Compatibility

Both skills are aligned to the integrated Catfish architecture and `docs/catfish/SCORING_AND_COMPETITION_20260325.md`:

- child outputs may include rationale, self-critique, uncertainty, and claimed resource usage
- official scorecards remain parent-owned
- diversity is treated as a parent-side shaping and adjustment concern
- merge operations require re-scoring of the merged artifact as a new candidate
- replay-under-constraint-shift remains available when the concept is good but the chosen stack is weak

## Intended Pairing

Use `catfish-first-principles-occam` before a bakeoff to define real diversity axes and again after a bakeoff to simplify the surviving route before implementation or packaging.
