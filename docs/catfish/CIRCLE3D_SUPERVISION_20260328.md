# CircleEditing 3D Edit Production Supervision

## Parent Authority

Catfish is the only planner and allocator for CircleEditing 3d-edit work in production. The parent controls:

- project intake
- child launch width
- resource allocation
- safety gating
- branch scoring
- promotion and handoff

The parent does not directly edit CircleEditing from outside the Catfish pipeline. All external-repo mutations flow through approved child worktrees.

## Resource Governance

The resource manager contract in `assets/catfish_policy/circleediting_resource_manager_contract.example.json` should be treated as mandatory runtime input, not optional reference material.

Operational rules:

- every child must request GPU, vePFS, CPU, and CircleEditing write access before use
- every approval must include a lease TTL, approved write targets, and release requirements
- every denial must include explicit reasons and a retry policy
- aggregate active approvals must stay within 4 GPUs and 50 GB vePFS
- aggregate CPU allocations must preserve SSH responsiveness on the host
- any write target outside an approved root is an immediate denial

## AgentDoc Cadence

The AgentDoc policy in `assets/catfish_policy/circleediting_agentdoc_check_policy.example.json` exists because 3d-edit work is long-running, resource-heavy, and operationally easy to drift.

Required cadence:

- check AgentDoc before the first task in each stage
- check AgentDoc before each resource request
- force a recheck after any denial, escalation, or workspace-root change
- run a heartbeat check at least every 45 minutes while work is active
- refresh before handoff, merge, or production review

The supervision failure mode to avoid is stale procedure knowledge attached to a valid-looking child run.

## Safety Events That Must Be Visible

The control center should expose these events for every active 3d-edit wave:

- manifest loaded
- resource request approved
- resource request denied
- AgentDoc receipt refreshed
- heartbeat check completed
- aggregate safety window still within GPU, storage, and CPU limits

If a denial happens for root-dir spillover, Catfish should preserve the denial as reviewable evidence instead of silently masking it with a reroute.

## Deny Conditions

Catfish should deny or halt work immediately when any of these conditions are true:

| Condition | Required action |
| --- | --- |
| GPU request would exceed 4 total active GPUs | deny the request and require narrower scope or lease release |
| vePFS request would exceed 50 GB | deny the request and require smaller scratch usage or cleanup |
| CPU allocation would threaten SSH responsiveness | deny or reduce the request and preserve host headroom |
| write target leaves approved roots | deny the request and require an approved worktree path |
| AgentDoc receipt is missing or stale | deny the request until a fresh receipt exists |
| parent attempts to bypass the child pipeline | stop and re-route through Catfish supervision |

## Production Checklist

Before starting a 3d-edit wave:

- confirm the onboarding manifest has a resolved CircleEditing root
- confirm the resource manager node and AgentDoc monitor node are active
- confirm the control center is receiving approval, denial, and heartbeat events
- confirm the approved-root list matches the actual worktree layout

Before approving a child handoff:

- confirm the child has an active or recently released approval record
- confirm the latest AgentDoc receipt is within policy age
- confirm no root-dir spillover or vePFS overrun was observed
- confirm the parent review is based on Catfish-visible evidence, not shell memory
