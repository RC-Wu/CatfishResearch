# ARIS Control Center

`apps/aris-control-center` upgrades `pua_research` from a documentation-and-skill fork into a real ARIS application shell.

## What It Adds

- a web dashboard for fleet, route health, tmux instances, reflections, upgrade proposals, and deep-research plans
- file-backed control-plane reuse from `codex-subagent-control-plane`
- explicit relay inventory for multi-account and multi-endpoint routing
- reflection and upgrade-proposal stores for self-improvement
- one-tmux-per-instance lifecycle descriptors
- a `60+` shard deep-research planner

## Entry Commands

```powershell
cd F:\InformationAndCourses\Code\pua_research\apps\aris-control-center
npm install
npm run dev
```

Server:

- `http://127.0.0.1:47951`

Web:

- `http://127.0.0.1:41851`

CLI:

```powershell
npx tsx scripts\control_plane_cli.ts dashboard
npx tsx scripts\control_plane_cli.ts route-preview --machine dev-intern-02 --task-kind research --difficulty high
npx tsx scripts\control_plane_cli.ts tmux --label "ARIS main" --machine dev-intern-02
npx tsx scripts\control_plane_cli.ts deep-research-plan --topic "mesh token compression" --agents 72
```
