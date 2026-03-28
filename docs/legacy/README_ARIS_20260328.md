# Legacy README Snapshot

This document preserves the pre-rewrite ARIS-oriented README framing for reference. The main `README.md` now describes CatfishResearch as the repository identity; this file keeps the older wording style and workflow-centric orientation available without making it the primary entrypoint.

If you need the exact historical file, inspect git history. This snapshot is meant to keep the main ideas readable in one place.

## Legacy Framing

The prior README described the repository as an ARIS workflow stack with Catfish as an added architectural layer. It emphasized the upstream ARIS lineage, the Codex-first fork history, and the use of cross-model execution and review.

The legacy README also treated these workflow entrypoints as the main user surface:

- `/idea-discovery`
- `/experiment-bridge`
- `/auto-review-loop`
- `/paper-writing`
- `/rebuttal`
- `/research-pipeline`

## Legacy Quick Start

The older README focused on installing the upstream skill tree, setting up Codex MCP for review-heavy workflows, and then using Claude Code or Codex CLI to run the pipelines.

The key setup pattern was:

```bash
git clone https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep.git
cp -r Auto-claude-code-research-in-sleep/skills/* ~/.claude/skills/

npm install -g @openai/codex
codex setup
claude mcp add codex -s user -- codex mcp-server
```

The Codex-first fork path also pointed at the local `skills/skills-codex/` tree and the branch-specific docs:

- `docs/CODEX_PUA_STACK.md`
- `docs/AGENTDOC_BRIDGE.md`
- `docs/CODEX_CONTROL_PLANE.md`

## What The Legacy README Emphasized

- ARIS as the primary workflow identity.
- Catfish as a later architectural concept instead of the main repository label.
- Cross-model execution and review as the main productivity pattern.
- Human-in-the-loop checkpoints and safety gates for paper workflows.
- The Codex-native skill tree as an additive fork surface.

## Why This File Exists

The old README still contains useful context for people following the historical ARIS narrative, but it is no longer the best description of the current repository shape.

For the current baseline, start with:

- [`README.md`](../../README.md)
- [`docs/catfish/INDEX_20260325.md`](../catfish/INDEX_20260325.md)
- [`docs/catfish/CONTROL_CENTER_LIVE_20260325.md`](../catfish/CONTROL_CENTER_LIVE_20260325.md)
