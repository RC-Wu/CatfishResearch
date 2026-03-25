from __future__ import annotations

from collections import defaultdict

from .models import AgentNode, BranchScore, ControlEvent, ControlSnapshot


def _section(title: str, lines: list[str]) -> str:
    body = lines or ["- no data"]
    return "\n".join([title, *body])


def render_multi_project_overview(snapshot: ControlSnapshot) -> list[str]:
    lines: list[str] = []
    for project in sorted(snapshot.projects, key=lambda item: item.project_id):
        lines.append(
            "- "
            f"{project.label} [{project.status}] "
            f"branch={project.active_branch or 'n/a'} "
            f"agents={project.active_agents} "
            f"pending_reviews={project.pending_reviews} "
            f"owner={project.owner or 'unassigned'} "
            f"last_event={project.last_event_at or 'n/a'}"
        )
        if project.summary:
            lines.append(f"  summary: {project.summary}")
    return lines


def render_agent_graph(snapshot: ControlSnapshot) -> list[str]:
    agents_by_parent: dict[str, list[AgentNode]] = defaultdict(list)
    roots: list[AgentNode] = []
    for agent in sorted(snapshot.agents, key=lambda item: (item.project_id, item.parent_id, item.agent_id)):
        if agent.parent_id:
            agents_by_parent[agent.parent_id].append(agent)
        else:
            roots.append(agent)

    lines: list[str] = []

    def walk(node: AgentNode, depth: int) -> None:
        indent = "  " * depth
        lines.append(
            f"{indent}- {node.label} [{node.role}/{node.status}] "
            f"project={node.project_id or 'n/a'} "
            f"branch={node.branch or 'n/a'} "
            f"provider={node.provider_profile or 'n/a'} "
            f"task={node.task_kind}"
        )
        if node.summary:
            lines.append(f"{indent}  summary: {node.summary}")
        for child in sorted(agents_by_parent.get(node.agent_id, []), key=lambda item: item.agent_id):
            walk(child, depth + 1)

    for root in roots:
        walk(root, 0)

    return lines


def render_provider_health(snapshot: ControlSnapshot) -> list[str]:
    lines: list[str] = []
    for provider in sorted(snapshot.providers, key=lambda item: item.profile_id):
        selected = " SELECTED" if provider.selected else ""
        tiers = ",".join(sorted(provider.route_tiers)) or "n/a"
        issues = ", ".join(provider.issues) if provider.issues else "none"
        machines = ",".join(provider.machine_ids) or "n/a"
        lines.append(
            "- "
            f"{provider.label} ({provider.profile_id}){selected} "
            f"machines={machines} "
            f"health={provider.health_summary} "
            f"quota={provider.remaining_credit:.2f} ({provider.quota_summary}) "
            f"weight={provider.routing_weight:.2f} "
            f"tiers={tiers} "
            f"issues={issues}"
        )
    return lines


def render_branch_scoreboards(snapshot: ControlSnapshot) -> list[str]:
    grouped: dict[str, list[BranchScore]] = defaultdict(list)
    for branch in snapshot.branches:
        grouped[branch.project_id or "unassigned"].append(branch)

    lines: list[str] = []
    for project_id in sorted(grouped):
        lines.append(f"- project={project_id}")
        for branch in sorted(grouped[project_id], key=lambda item: (-item.score, item.branch)):
            lines.append(
                "  "
                f"* {branch.branch} score={branch.score:.1f} "
                f"record={branch.wins}-{branch.losses} "
                f"state={branch.state} "
                f"head={branch.head_commit or 'n/a'}"
            )
            if branch.summary:
                lines.append(f"    summary: {branch.summary}")
    return lines


def render_recent_events(snapshot: ControlSnapshot, limit: int = 8) -> list[str]:
    lines: list[str] = []
    recent: list[ControlEvent] = sorted(snapshot.events, key=lambda item: item.timestamp)[-limit:]
    for event in recent:
        target = "/".join(part for part in [event.project_id, event.branch, event.agent_id] if part) or "global"
        lines.append(
            "- "
            f"{event.timestamp} [{event.level}/{event.kind}] "
            f"target={target} "
            f"{event.message}"
        )
    return lines


def render_route_preview(snapshot: ControlSnapshot) -> list[str]:
    if not snapshot.route_preview:
        return ["- no live route preview"]
    preview = snapshot.route_preview
    rationale = "; ".join(preview.get("rationale", []))
    return [
        "- "
        f"profile={preview.get('profileId', 'n/a')} "
        f"machine={preview.get('machineId', 'n/a')} "
        f"tier={preview.get('tierId', 'n/a')} "
        f"model={preview.get('model', 'n/a')} "
        f"reasoning={preview.get('reasoningEffort', 'n/a')} "
        f"search={preview.get('search', False)} "
        f"browser={preview.get('browserMode', 'none')}",
        f"  rationale: {rationale}",
    ]


def render_dashboard(snapshot: ControlSnapshot, event_limit: int = 8) -> str:
    sections = [
        f"Catfish Control Center Snapshot @ {snapshot.generated_at or 'unknown'}",
        _section("Route Preview", render_route_preview(snapshot)),
        _section("Multi-Project Overview", render_multi_project_overview(snapshot)),
        _section("Agent Graph / Hierarchy", render_agent_graph(snapshot)),
        _section("Provider Health / Quota", render_provider_health(snapshot)),
        _section("Branch Scoreboards", render_branch_scoreboards(snapshot)),
        _section("Recent Events", render_recent_events(snapshot, limit=event_limit)),
    ]
    return "\n\n".join(sections)
