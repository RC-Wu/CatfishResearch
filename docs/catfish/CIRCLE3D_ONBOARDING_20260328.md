# CircleEditing 3D Edit Onboarding

## Scope

This onboarding package is for the CircleEditing 3d-edit project only. Catfish supervises the project as the parent control plane, but Catfish does not directly modify CircleEditing from outside the Catfish pipeline.

The parent-side contract is simple:

1. Catfish owns planning, resource approval, and supervision.
2. Child agents may touch CircleEditing only after explicit Catfish approval.
3. AgentDoc remains an external source of truth and must be checked repeatedly during active 3d-edit work.

## Production Invariants

| Invariant | Required behavior | Enforcement surface |
| --- | --- | --- |
| Parent-owned planning | Catfish root supervisor defines stages, candidate width, and handoff points. | `assets/catfish_dispatch_examples/circleediting_3d_edit_onboarding_state.json` |
| Parent-owned resources | Every child asks the resource manager for GPU, vePFS, CPU, and CircleEditing write access. | `assets/catfish_policy/circleediting_resource_manager_contract.example.json` |
| Frequent AgentDoc checks | Every child refreshes AgentDoc before stage start, before resource requests, after denials, and at heartbeat cadence. | `assets/catfish_policy/circleediting_agentdoc_check_policy.example.json` |
| Safe workspace boundaries | No writes outside approved roots and no root-dir spillover. | dispatch manifest, resource contract, and control-center review |
| Host safety | Aggregate CPU usage must preserve SSH responsiveness. | resource manager approvals and runtime monitoring |

## Onboarding Package

| File | Purpose |
| --- | --- |
| `assets/catfish_dispatch_examples/circleediting_3d_edit_onboarding_state.json` | concrete dispatch-state manifest for project intake and the first supervised builder wave |
| `assets/catfish_policy/circleediting_resource_manager_contract.example.json` | request, approval, denial, and release contracts for child-agent resource governance |
| `assets/catfish_policy/circleediting_agentdoc_check_policy.example.json` | AgentDoc check cadence, receipt fields, and trigger points |
| `apps/catfish-control-center/examples/circleediting_3d_edit_snapshot.json` | control-center snapshot showing safe production supervision state |

## Manifest Structure

The onboarding manifest carries enough context for Catfish to supervise CircleEditing without turning the parent into an out-of-band editor.

| Manifest area | Why it exists | Required interpretation |
| --- | --- | --- |
| `project` | identifies the Catfish-owned project, default launch behavior, and candidate group shapes | Catfish remains the launch and scoring authority |
| `projectContext.supervisedProject` | describes the external CircleEditing target and the child-only mutation path | resolve `<CIRCLE_EDITING_ROOT>` explicitly before launch |
| `projectContext.pathGuards` | constrains approved write roots and forbidden roots | deny launches that would spill into root-adjacent or unapproved paths |
| `resourceGovernance` | encodes hard limits and the policy files that govern approval | no subordinate agent can override these values |
| `runtime.operations` | bootstraps the root supervisor, resource manager, and AgentDoc monitor | these nodes exist before builder waves begin |
| `stages` | defines intake and the first builder competition wave | every builder stage requires both resource approval and AgentDoc recency |

## Safety Envelope For 3D Edit

The production-first envelope used by the example assets is:

- maximum 4 total GPUs across active child leases
- maximum 50 GB vePFS allocation across active child leases
- maximum 24 logical CPU cores allocated, with at least 4 reserved for SSH and supervisory traffic
- no writes outside approved roots under `/dev_vepfs/rc_wu/repos`, `/dev_vepfs/rc_wu/codex_subagents`, or `/dev_vepfs/rc_wu/tmp`
- no direct parent-side CircleEditing edits

These values are duplicated across the manifest, the resource contract, and the control-center snapshot on purpose. The duplication makes drift visible during review.

## Dispatch Flow

1. Catfish resolves `<CIRCLE_EDITING_ROOT>` explicitly and records it in the launch context.
2. Catfish root supervisor reads the project manifest and creates a builder wave.
3. Each child performs an AgentDoc check and records a receipt.
4. Each child submits a structured resource request to `circle3d-resource-manager`.
5. The resource manager approves or denies the request using shared GPU, vePFS, CPU, and path budgets.
6. Only approved children receive CircleEditing worktree access.
7. Catfish reviews outputs, scores branches, and decides advancement without bypassing the pipeline.

## Control-Center Expectations

The example snapshot shows the minimum production-visible state Catfish should maintain:

- project stage, active branch family, active agent count, and review pressure
- root supervisor, resource manager, AgentDoc monitor, and child-builder nodes
- provider health and launch pressure
- stage competition diversity and run counts
- explicit resource approval and denial events
- explicit AgentDoc receipt and heartbeat events

If those signals are missing, Catfish is supervising 3d-edit work blindly.
