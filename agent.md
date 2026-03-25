# Repository Agent Contract

This repository is documentation-first and intentionally keeps most orchestration logic as portable docs, skills, and small tools instead of a large bundled control plane.

## Current Architecture Focus

- Catfish Effect system architecture lives under `docs/catfish/`.
- The Catfish docs are the source of truth for multi-project orchestration, intra-project competition, capability metadata, scoring, and rollout sequencing.
- Until runtime code lands, implementation work should follow the contracts and invariants defined in those docs instead of inventing ad hoc interfaces.

## Working Rules

- Keep work isolated to the active worktree and branch.
- Prefer explicit design docs, schemas, and examples before runtime code.
- Treat `Capability.md` metadata, parent-owned scorecards, and scheduling-graph state as stable interfaces that future code should consume directly.
- Preserve paper-friendly documentation quality: simple diagrams, clear terminology, grayscale-safe visuals, and auditable decision records.

## Expected Catfish Deliverables

- `docs/catfish/ARCHITECTURE_20260325.md`
- `docs/catfish/SCORING_AND_COMPETITION_20260325.md`
- `docs/catfish/MULTI_PROJECT_RUNTIME_20260325.md`
- `docs/catfish/ROADMAP_20260325.md`
- optional schemas under `docs/catfish/schemas/`
