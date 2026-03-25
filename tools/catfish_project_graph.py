from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

from catfish_runtime import ResourceBudget, ResourceUsage, utc_now


SCHEMA_VERSION = "catfish-scheduler-graph/v1"
STANDARD_STAGE_ORDER = (
    "idea",
    "planning",
    "implementation",
    "evaluation",
    "writing",
    "figure",
)

_STAGE_DEFAULTS: dict[str, dict[str, Any]] = {
    "idea": {
        "label": "Idea Competition",
        "routing_task_category": "research",
        "difficulty": "high",
        "competition_mode": "top-k",
        "target_frontier_width": 4,
        "min_competitors": 3,
        "max_survivors": 2,
        "replay_cap": 2,
        "prune_below_score": 0.30,
        "budget_share": 0.16,
        "agent_groups": ["divergent-lab", "skeptic-cell", "literature-scouts"],
        "styles": ["analytical", "contrarian", "systems"],
    },
    "planning": {
        "label": "Planning Competition",
        "routing_task_category": "research",
        "difficulty": "medium",
        "competition_mode": "top-k",
        "target_frontier_width": 3,
        "min_competitors": 2,
        "max_survivors": 2,
        "replay_cap": 2,
        "prune_below_score": 0.35,
        "budget_share": 0.14,
        "agent_groups": ["planner-critic", "resource-auditors", "ops-checkers"],
        "styles": ["outline-first", "risk-first", "evidence-first"],
    },
    "implementation": {
        "label": "Implementation Competition",
        "routing_task_category": "builder",
        "difficulty": "medium",
        "competition_mode": "top-k",
        "target_frontier_width": 3,
        "min_competitors": 2,
        "max_survivors": 2,
        "replay_cap": 3,
        "prune_below_score": 0.40,
        "budget_share": 0.28,
        "agent_groups": ["builder-pair", "patch-racer", "builder-reviewer"],
        "styles": ["minimal-diff", "refactor-first", "test-first"],
    },
    "evaluation": {
        "label": "Evaluation Competition",
        "routing_task_category": "review",
        "difficulty": "medium",
        "competition_mode": "top-k",
        "target_frontier_width": 3,
        "min_competitors": 2,
        "max_survivors": 2,
        "replay_cap": 2,
        "prune_below_score": 0.40,
        "budget_share": 0.16,
        "agent_groups": ["benchmark-panel", "repro-checkers", "error-analysis"],
        "styles": ["coverage-first", "skeptical", "quantitative"],
    },
    "writing": {
        "label": "Writing Competition",
        "routing_task_category": "summary",
        "difficulty": "medium",
        "competition_mode": "top-k",
        "target_frontier_width": 3,
        "min_competitors": 2,
        "max_survivors": 2,
        "replay_cap": 2,
        "prune_below_score": 0.35,
        "budget_share": 0.14,
        "agent_groups": ["drafting-pair", "structure-editor", "claim-auditor"],
        "styles": ["narrative", "dense-technical", "claim-led"],
    },
    "figure": {
        "label": "Figure Competition",
        "routing_task_category": "builder",
        "difficulty": "low",
        "competition_mode": "top-k",
        "target_frontier_width": 3,
        "min_competitors": 2,
        "max_survivors": 2,
        "replay_cap": 2,
        "prune_below_score": 0.35,
        "budget_share": 0.12,
        "agent_groups": ["chart-lab", "grayscale-review", "caption-crafter"],
        "styles": ["minimal", "annotation-heavy", "paper-ready"],
    },
}


def _copy_list(values: Sequence[str] | None) -> list[str]:
    return list(values or [])


def _copy_dict(values: dict[str, Any] | None) -> dict[str, Any]:
    return dict(values or {})


def _budget_from_share(project_budget: ResourceBudget, share: float) -> ResourceBudget:
    return ResourceBudget(
        token_budget=int(project_budget.token_budget * share),
        usd_budget=round(project_budget.usd_budget * share, 6),
        wall_time_budget_s=round(project_budget.wall_time_budget_s * share, 6),
        max_parallel_children=max(1, min(project_budget.max_parallel_children or 1, 3)),
    )


@dataclass(slots=True)
class DiversityTargets:
    provider_min_distinct: int = 2
    model_min_distinct: int = 2
    agent_group_min_distinct: int = 2
    style_min_distinct: int = 2
    max_stack_share: float = 0.6
    expand_bonus: float = 0.25
    replay_bonus: float = 0.18
    novel_stack_bonus: float = 0.12
    collapse_penalty: float = 0.20

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> DiversityTargets:
        payload = payload or {}
        return cls(
            provider_min_distinct=int(payload.get("provider_min_distinct", 2)),
            model_min_distinct=int(payload.get("model_min_distinct", 2)),
            agent_group_min_distinct=int(payload.get("agent_group_min_distinct", 2)),
            style_min_distinct=int(payload.get("style_min_distinct", 2)),
            max_stack_share=float(payload.get("max_stack_share", 0.6)),
            expand_bonus=float(payload.get("expand_bonus", 0.25)),
            replay_bonus=float(payload.get("replay_bonus", 0.18)),
            novel_stack_bonus=float(payload.get("novel_stack_bonus", 0.12)),
            collapse_penalty=float(payload.get("collapse_penalty", 0.20)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_min_distinct": self.provider_min_distinct,
            "model_min_distinct": self.model_min_distinct,
            "agent_group_min_distinct": self.agent_group_min_distinct,
            "style_min_distinct": self.style_min_distinct,
            "max_stack_share": self.max_stack_share,
            "expand_bonus": self.expand_bonus,
            "replay_bonus": self.replay_bonus,
            "novel_stack_bonus": self.novel_stack_bonus,
            "collapse_penalty": self.collapse_penalty,
        }


@dataclass(slots=True)
class Branch:
    branch_id: str
    stage_id: str
    label: str
    status: str = "ready"
    provider_id: str = ""
    model: str = ""
    tier_id: str = ""
    reasoning_effort: str = "medium"
    agent_group: str = ""
    style: str = ""
    capabilities: list[str] = field(default_factory=list)
    prior: float = 0.5
    visits: int = 0
    parent_scores: list[float] = field(default_factory=list)
    self_scores: list[float] = field(default_factory=list)
    replay_count: int = 0
    review_count: int = 0
    failure_count: int = 0
    projected_tokens: int = 0
    projected_cost_usd: float = 0.0
    projected_wall_time_s: float = 0.0
    resource_usage: ResourceUsage = field(default_factory=ResourceUsage)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Branch:
        return cls(
            branch_id=payload["branch_id"],
            stage_id=payload["stage_id"],
            label=payload.get("label", payload["branch_id"]),
            status=payload.get("status", "ready"),
            provider_id=payload.get("provider_id", ""),
            model=payload.get("model", ""),
            tier_id=payload.get("tier_id", ""),
            reasoning_effort=payload.get("reasoning_effort", "medium"),
            agent_group=payload.get("agent_group", ""),
            style=payload.get("style", ""),
            capabilities=_copy_list(payload.get("capabilities")),
            prior=float(payload.get("prior", 0.5)),
            visits=int(payload.get("visits", 0)),
            parent_scores=[float(value) for value in payload.get("parent_scores", [])],
            self_scores=[float(value) for value in payload.get("self_scores", [])],
            replay_count=int(payload.get("replay_count", 0)),
            review_count=int(payload.get("review_count", 0)),
            failure_count=int(payload.get("failure_count", 0)),
            projected_tokens=int(payload.get("projected_tokens", 0)),
            projected_cost_usd=float(payload.get("projected_cost_usd", 0.0)),
            projected_wall_time_s=float(payload.get("projected_wall_time_s", 0.0)),
            resource_usage=ResourceUsage.from_dict(payload.get("resource_usage")),
            metadata=_copy_dict(payload.get("metadata")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "branch_id": self.branch_id,
            "stage_id": self.stage_id,
            "label": self.label,
            "status": self.status,
            "provider_id": self.provider_id,
            "model": self.model,
            "tier_id": self.tier_id,
            "reasoning_effort": self.reasoning_effort,
            "agent_group": self.agent_group,
            "style": self.style,
            "capabilities": list(self.capabilities),
            "prior": self.prior,
            "visits": self.visits,
            "parent_scores": list(self.parent_scores),
            "self_scores": list(self.self_scores),
            "replay_count": self.replay_count,
            "review_count": self.review_count,
            "failure_count": self.failure_count,
            "projected_tokens": self.projected_tokens,
            "projected_cost_usd": self.projected_cost_usd,
            "projected_wall_time_s": self.projected_wall_time_s,
            "resource_usage": self.resource_usage.to_dict(),
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class StageCell:
    stage_id: str
    stage_kind: str
    label: str
    parent_node_id: str
    routing_task_category: str
    difficulty: str = "medium"
    status: str = "active"
    competition_mode: str = "top-k"
    target_frontier_width: int = 3
    min_competitors: int = 2
    max_survivors: int = 2
    replay_cap: int = 2
    prune_below_score: float = 0.35
    review_required: bool = True
    budget_ceiling: ResourceBudget = field(default_factory=ResourceBudget)
    diversity_targets: DiversityTargets = field(default_factory=DiversityTargets)
    agent_groups: list[str] = field(default_factory=list)
    styles: list[str] = field(default_factory=list)
    branch_ids: list[str] = field(default_factory=list)
    selected_branch_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> StageCell:
        return cls(
            stage_id=payload["stage_id"],
            stage_kind=payload["stage_kind"],
            label=payload.get("label", payload["stage_id"]),
            parent_node_id=payload["parent_node_id"],
            routing_task_category=payload.get("routing_task_category", "research"),
            difficulty=payload.get("difficulty", "medium"),
            status=payload.get("status", "active"),
            competition_mode=payload.get("competition_mode", "top-k"),
            target_frontier_width=int(payload.get("target_frontier_width", 3)),
            min_competitors=int(payload.get("min_competitors", 2)),
            max_survivors=int(payload.get("max_survivors", 2)),
            replay_cap=int(payload.get("replay_cap", 2)),
            prune_below_score=float(payload.get("prune_below_score", 0.35)),
            review_required=bool(payload.get("review_required", True)),
            budget_ceiling=ResourceBudget.from_dict(payload.get("budget_ceiling")),
            diversity_targets=DiversityTargets.from_dict(payload.get("diversity_targets")),
            agent_groups=_copy_list(payload.get("agent_groups")),
            styles=_copy_list(payload.get("styles")),
            branch_ids=_copy_list(payload.get("branch_ids")),
            selected_branch_ids=_copy_list(payload.get("selected_branch_ids")),
            metadata=_copy_dict(payload.get("metadata")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage_id": self.stage_id,
            "stage_kind": self.stage_kind,
            "label": self.label,
            "parent_node_id": self.parent_node_id,
            "routing_task_category": self.routing_task_category,
            "difficulty": self.difficulty,
            "status": self.status,
            "competition_mode": self.competition_mode,
            "target_frontier_width": self.target_frontier_width,
            "min_competitors": self.min_competitors,
            "max_survivors": self.max_survivors,
            "replay_cap": self.replay_cap,
            "prune_below_score": self.prune_below_score,
            "review_required": self.review_required,
            "budget_ceiling": self.budget_ceiling.to_dict(),
            "diversity_targets": self.diversity_targets.to_dict(),
            "agent_groups": list(self.agent_groups),
            "styles": list(self.styles),
            "branch_ids": list(self.branch_ids),
            "selected_branch_ids": list(self.selected_branch_ids),
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class ActionRecord:
    action_id: str
    action: str
    stage_id: str
    selection_value: float
    reason: str
    scheduled_at: str = field(default_factory=utc_now)
    branch_id: str | None = None
    created_branch_id: str | None = None
    route: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ActionRecord:
        return cls(
            action_id=payload["action_id"],
            action=payload["action"],
            stage_id=payload["stage_id"],
            selection_value=float(payload.get("selection_value", 0.0)),
            reason=payload.get("reason", ""),
            scheduled_at=payload.get("scheduled_at", utc_now()),
            branch_id=payload.get("branch_id"),
            created_branch_id=payload.get("created_branch_id"),
            route=_copy_dict(payload.get("route")),
            metadata=_copy_dict(payload.get("metadata")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action": self.action,
            "stage_id": self.stage_id,
            "selection_value": self.selection_value,
            "reason": self.reason,
            "scheduled_at": self.scheduled_at,
            "branch_id": self.branch_id,
            "created_branch_id": self.created_branch_id,
            "route": dict(self.route),
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class ProjectGraph:
    graph_id: str
    project_id: str
    root_node_id: str
    machine_id: str = "dev-intern-02"
    schema_version: str = SCHEMA_VERSION
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    project_budget: ResourceBudget = field(default_factory=ResourceBudget)
    project_usage: ResourceUsage = field(default_factory=ResourceUsage)
    stage_order: list[str] = field(default_factory=lambda: list(STANDARD_STAGE_ORDER))
    stages: dict[str, StageCell] = field(default_factory=dict)
    branches: dict[str, Branch] = field(default_factory=dict)
    action_log: list[ActionRecord] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ProjectGraph:
        return cls(
            graph_id=payload["graph_id"],
            project_id=payload["project_id"],
            root_node_id=payload["root_node_id"],
            machine_id=payload.get("machine_id", "dev-intern-02"),
            schema_version=payload.get("schema_version", SCHEMA_VERSION),
            created_at=payload.get("created_at", utc_now()),
            updated_at=payload.get("updated_at", utc_now()),
            project_budget=ResourceBudget.from_dict(payload.get("project_budget")),
            project_usage=ResourceUsage.from_dict(payload.get("project_usage")),
            stage_order=_copy_list(payload.get("stage_order")) or list(STANDARD_STAGE_ORDER),
            stages={
                stage_id: StageCell.from_dict(stage_payload)
                for stage_id, stage_payload in (payload.get("stages") or {}).items()
            },
            branches={
                branch_id: Branch.from_dict(branch_payload)
                for branch_id, branch_payload in (payload.get("branches") or {}).items()
            },
            action_log=[ActionRecord.from_dict(item) for item in payload.get("action_log", [])],
            metadata=_copy_dict(payload.get("metadata")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "graph_id": self.graph_id,
            "project_id": self.project_id,
            "root_node_id": self.root_node_id,
            "machine_id": self.machine_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "project_budget": self.project_budget.to_dict(),
            "project_usage": self.project_usage.to_dict(),
            "stage_order": list(self.stage_order),
            "stages": {stage_id: stage.to_dict() for stage_id, stage in sorted(self.stages.items())},
            "branches": {branch_id: branch.to_dict() for branch_id, branch in sorted(self.branches.items())},
            "action_log": [action.to_dict() for action in self.action_log],
            "metadata": dict(self.metadata),
        }


def default_stage_cell(
    *,
    stage_kind: str,
    parent_node_id: str,
    project_budget: ResourceBudget,
    diversity_targets: DiversityTargets | None = None,
) -> StageCell:
    defaults = dict(_STAGE_DEFAULTS[stage_kind])
    return StageCell(
        stage_id=stage_kind,
        stage_kind=stage_kind,
        label=defaults["label"],
        parent_node_id=parent_node_id,
        routing_task_category=defaults["routing_task_category"],
        difficulty=defaults["difficulty"],
        competition_mode=defaults["competition_mode"],
        target_frontier_width=defaults["target_frontier_width"],
        min_competitors=defaults["min_competitors"],
        max_survivors=defaults["max_survivors"],
        replay_cap=defaults["replay_cap"],
        prune_below_score=defaults["prune_below_score"],
        budget_ceiling=_budget_from_share(project_budget, defaults["budget_share"]),
        diversity_targets=diversity_targets or DiversityTargets(),
        agent_groups=list(defaults["agent_groups"]),
        styles=list(defaults["styles"]),
    )


def build_project_graph_from_runtime_snapshot(
    snapshot: dict[str, Any],
    *,
    project_id: str,
    graph_id: str | None = None,
    machine_id: str = "dev-intern-02",
    stage_order: Sequence[str] | None = None,
    diversity_targets: DiversityTargets | None = None,
) -> ProjectGraph:
    project_snapshot = snapshot["projects"][project_id]
    project = project_snapshot["project"]
    runtime_root_ids = list(project_snapshot.get("root_node_ids", []))
    root_node_id = f"project:{project_id}"
    runtime_parent_node_id = runtime_root_ids[0] if runtime_root_ids else root_node_id
    project_budget = ResourceBudget.from_dict(project.get("resource_budget"))
    graph = ProjectGraph(
        graph_id=graph_id or f"{project_id}.scheduler",
        project_id=project_id,
        root_node_id=root_node_id,
        machine_id=machine_id,
        project_budget=project_budget,
        metadata={
            "title": project.get("title", project_id),
            "objective": project.get("objective", ""),
            "runtime_root_node_ids": runtime_root_ids,
        },
    )
    for stage_kind in stage_order or STANDARD_STAGE_ORDER:
        stage = default_stage_cell(
            stage_kind=stage_kind,
            parent_node_id=runtime_parent_node_id,
            project_budget=project_budget,
            diversity_targets=diversity_targets,
        )
        graph.stages[stage.stage_id] = stage
    graph.stage_order = [stage_id for stage_id in (stage_order or STANDARD_STAGE_ORDER) if stage_id in graph.stages]
    return graph


def next_branch_id(graph: ProjectGraph, stage_id: str) -> str:
    prefix = f"{stage_id}-branch-"
    existing = [
        int(branch_id.removeprefix(prefix))
        for branch_id in graph.branches
        if branch_id.startswith(prefix) and branch_id.removeprefix(prefix).isdigit()
    ]
    next_index = max(existing, default=0) + 1
    return f"{prefix}{next_index}"


def graph_usage_for_stage(graph: ProjectGraph, stage_id: str) -> ResourceUsage:
    usage = ResourceUsage()
    stage = graph.stages[stage_id]
    for branch_id in stage.branch_ids:
        branch = graph.branches.get(branch_id)
        if branch is None:
            continue
        usage.prompt_tokens += branch.resource_usage.prompt_tokens + branch.projected_tokens
        usage.completion_tokens += branch.resource_usage.completion_tokens
        usage.cost_usd += branch.resource_usage.cost_usd + branch.projected_cost_usd
        usage.wall_time_s += branch.resource_usage.wall_time_s + branch.projected_wall_time_s
    return usage


def graph_total_usage(graph: ProjectGraph) -> ResourceUsage:
    usage = ResourceUsage()
    for branch in graph.branches.values():
        usage.prompt_tokens += branch.resource_usage.prompt_tokens + branch.projected_tokens
        usage.completion_tokens += branch.resource_usage.completion_tokens
        usage.cost_usd += branch.resource_usage.cost_usd + branch.projected_cost_usd
        usage.wall_time_s += branch.resource_usage.wall_time_s + branch.projected_wall_time_s
    return usage


def build_schema_snapshot(graph: ProjectGraph) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = [
        {
            "nodeId": graph.root_node_id,
            "nodeType": "project",
            "scope": "project",
            "state": "ready",
            "remainingBudget": round(max(graph.project_budget.usd_budget - graph_total_usage(graph).cost_usd, 0.0), 6),
            "visits": sum(branch.visits for branch in graph.branches.values()),
            "realizedReward": 0.0,
            "prior": 1.0,
            "frontierWidth": len(graph.stages),
        }
    ]
    edges: list[dict[str, Any]] = []
    for stage_id in graph.stage_order:
        stage = graph.stages[stage_id]
        stage_usage = graph_usage_for_stage(graph, stage_id)
        nodes.append(
            {
                "nodeId": stage.stage_id,
                "nodeType": "stage",
                "scope": "project",
                "state": "ready" if stage.status == "active" else "held",
                "remainingBudget": round(max(stage.budget_ceiling.usd_budget - stage_usage.cost_usd, 0.0), 6),
                "visits": sum(graph.branches[branch_id].visits for branch_id in stage.branch_ids if branch_id in graph.branches),
                "realizedReward": 0.0,
                "prior": 1.0,
                "frontierWidth": len(stage.branch_ids),
            }
        )
    for branch in graph.branches.values():
        nodes.append(
            {
                "nodeId": branch.branch_id,
                "nodeType": "candidate",
                "scope": "node",
                "state": "pruned" if branch.status == "pruned" else ("selected" if branch.status == "selected" else "ready"),
                "remainingBudget": round(max(branch.projected_cost_usd, 0.0), 6),
                "visits": branch.visits,
                "realizedReward": round(sum(branch.parent_scores) / len(branch.parent_scores), 6) if branch.parent_scores else 0.0,
                "prior": round(branch.prior, 6),
            }
        )
    for action in graph.action_log:
        target = action.created_branch_id or action.branch_id or action.stage_id
        edges.append(
            {
                "from": action.stage_id,
                "to": target,
                "action": action.action,
                "selectionValue": round(action.selection_value, 6),
                "decisionReason": action.reason,
            }
        )
    return {
        "graphId": graph.graph_id,
        "timestamp": graph.updated_at,
        "rootNodeId": graph.root_node_id,
        "nodes": nodes,
        "edges": edges,
    }


def load_project_graph(path: Path) -> ProjectGraph:
    return ProjectGraph.from_dict(json.loads(path.read_text(encoding="utf-8")))


def save_project_graph(path: Path, graph: ProjectGraph) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
