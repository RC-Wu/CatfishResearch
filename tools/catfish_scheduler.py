from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

from catfish_project_graph import (
    Branch,
    ProjectGraph,
    ResourceBudget,
    ResourceUsage,
    StageCell,
    build_project_graph_from_runtime_snapshot,
    build_schema_snapshot,
    graph_total_usage,
    graph_usage_for_stage,
    load_project_graph,
    next_branch_id,
    save_project_graph,
)
from catfish_route_core import (
    DEFAULT_HEALTH_PATH,
    DEFAULT_LEDGER_PATH,
    DEFAULT_REGISTRY_PATH,
    evaluate_provider,
    load_router_inputs,
    parse_date_like,
    reasoning_length_for_tier,
)
from catfish_runtime import CatfishRuntime, load_operations, utc_now


_ACTION_SET = {"expand", "deepen", "replay", "review", "prune"}
_BASE_ESTIMATES = {
    "low": {"tokens": 1200, "cost_usd": 0.25, "wall_time_s": 180.0},
    "medium": {"tokens": 2400, "cost_usd": 0.75, "wall_time_s": 600.0},
    "high": {"tokens": 3000, "cost_usd": 0.95, "wall_time_s": 900.0},
}
_ACTION_MULTIPLIERS = {
    "expand": 1.0,
    "deepen": 1.2,
    "replay": 1.1,
    "review": 0.6,
    "prune": 0.05,
}
_ACTION_BIAS = {
    "expand": 0.08,
    "deepen": 0.06,
    "replay": 0.07,
    "review": 0.18,
    "prune": 0.10,
}


@dataclass(slots=True)
class ActionProposal:
    action: str
    stage_id: str
    selection_value: float
    reason: str
    branch_id: str | None = None
    created_branch_id: str | None = None
    route: dict[str, Any] = field(default_factory=dict)
    estimated_usage: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "stage_id": self.stage_id,
            "selection_value": round(self.selection_value, 6),
            "reason": self.reason,
            "branch_id": self.branch_id,
            "created_branch_id": self.created_branch_id,
            "route": dict(self.route),
            "estimated_usage": dict(self.estimated_usage),
            "metadata": dict(self.metadata),
        }


class CatfishScheduler:
    def __init__(
        self,
        *,
        registry_path: Path = DEFAULT_REGISTRY_PATH,
        health_path: Path = DEFAULT_HEALTH_PATH,
        ledger_path: Path = DEFAULT_LEDGER_PATH,
        c_puct: float = 1.15,
    ) -> None:
        self.registry, self.health_snapshot, self.ledger = load_router_inputs(
            registry_path=registry_path,
            health_path=health_path,
            ledger_path=ledger_path,
        )
        self.health_by_provider = {
            str(entry.get("providerId")): dict(entry)
            for entry in self.health_snapshot.get("providers", [])
            if entry.get("providerId")
        }
        self.reference_date = parse_date_like(self.health_snapshot.get("observedAt", utc_now()))
        self.routing = self.registry.get("routing", {})
        self.c_puct = c_puct

    def bootstrap_graph_from_runtime_ops(
        self,
        *,
        ops_path: Path,
        project_id: str,
        graph_id: str | None = None,
        machine_id: str = "dev-intern-02",
    ) -> ProjectGraph:
        runtime = CatfishRuntime()
        runtime.apply_operations(load_operations(ops_path))
        snapshot = runtime.snapshot(project_id=project_id)
        return build_project_graph_from_runtime_snapshot(
            snapshot,
            project_id=project_id,
            graph_id=graph_id,
            machine_id=machine_id,
        )

    def recommend_next_action(self, graph: ProjectGraph) -> ActionProposal:
        proposals: list[ActionProposal] = []
        for stage_id in graph.stage_order:
            stage = graph.stages.get(stage_id)
            if stage is None or stage.status != "active":
                continue
            proposals.extend(self._proposals_for_stage(graph, stage))
        if not proposals:
            raise ValueError("No schedulable Catfish action for the current graph state")
        if not graph.branches:
            first_stage_id = graph.stage_order[0]
            first_stage = [proposal for proposal in proposals if proposal.stage_id == first_stage_id]
            if first_stage:
                first_stage.sort(key=lambda item: (item.selection_value, item.action), reverse=True)
                return first_stage[0]
        review_proposals = [proposal for proposal in proposals if proposal.action == "review"]
        if review_proposals:
            review_proposals.sort(key=lambda item: item.selection_value, reverse=True)
            return review_proposals[0]
        prune_proposals = [proposal for proposal in proposals if proposal.action == "prune"]
        if prune_proposals:
            prune_proposals.sort(key=lambda item: item.selection_value, reverse=True)
            if prune_proposals[0].selection_value >= 0.65:
                return prune_proposals[0]
        proposals.sort(key=lambda item: (item.selection_value, item.action), reverse=True)
        return proposals[0]

    def apply_action(self, graph: ProjectGraph, proposal: ActionProposal) -> ProjectGraph:
        if proposal.action not in _ACTION_SET:
            raise ValueError(f"Unsupported action {proposal.action}")
        stage = graph.stages[proposal.stage_id]
        timestamp = utc_now()
        if proposal.action == "expand":
            branch = Branch(
                branch_id=proposal.created_branch_id or next_branch_id(graph, stage.stage_id),
                stage_id=stage.stage_id,
                label=proposal.metadata.get("label", proposal.created_branch_id or stage.stage_id),
                status="ready",
                provider_id=str(proposal.route.get("provider_id", "")),
                model=str(proposal.route.get("model", "")),
                tier_id=str(proposal.route.get("tierId", "")),
                reasoning_effort=str(proposal.route.get("reasoningEffort", "medium")),
                agent_group=str(proposal.route.get("agent_group", "")),
                style=str(proposal.route.get("style", "")),
                capabilities=list(proposal.metadata.get("capabilities", [])),
                prior=float(proposal.metadata.get("prior", 0.5)),
                projected_tokens=int(proposal.estimated_usage.get("tokens", 0.0)),
                projected_cost_usd=float(proposal.estimated_usage.get("cost_usd", 0.0)),
                projected_wall_time_s=float(proposal.estimated_usage.get("wall_time_s", 0.0)),
                metadata={
                    "route_score": proposal.route.get("score"),
                    "rationale": proposal.route.get("rationale", []),
                },
            )
            graph.branches[branch.branch_id] = branch
            if branch.branch_id not in stage.branch_ids:
                stage.branch_ids.append(branch.branch_id)
        elif proposal.action == "deepen":
            branch = graph.branches[proposal.branch_id or ""]
            branch.visits += 1
            branch.status = "running"
            branch.projected_tokens += int(proposal.estimated_usage.get("tokens", 0.0))
            branch.projected_cost_usd += float(proposal.estimated_usage.get("cost_usd", 0.0))
            branch.projected_wall_time_s += float(proposal.estimated_usage.get("wall_time_s", 0.0))
        elif proposal.action == "replay":
            source = graph.branches[proposal.branch_id or ""]
            replay_branch_id = proposal.created_branch_id or next_branch_id(graph, stage.stage_id)
            branch = Branch(
                branch_id=replay_branch_id,
                stage_id=stage.stage_id,
                label=proposal.metadata.get("label", f"{source.label} replay"),
                status="ready",
                provider_id=str(proposal.route.get("provider_id", source.provider_id)),
                model=str(proposal.route.get("model", source.model)),
                tier_id=str(proposal.route.get("tierId", source.tier_id)),
                reasoning_effort=str(proposal.route.get("reasoningEffort", source.reasoning_effort)),
                agent_group=str(proposal.route.get("agent_group", source.agent_group)),
                style=str(proposal.route.get("style", source.style)),
                capabilities=list(source.capabilities),
                prior=float(proposal.metadata.get("prior", max(source.prior, self._official_mean(source)))),
                replay_count=source.replay_count + 1,
                projected_tokens=int(proposal.estimated_usage.get("tokens", 0.0)),
                projected_cost_usd=float(proposal.estimated_usage.get("cost_usd", 0.0)),
                projected_wall_time_s=float(proposal.estimated_usage.get("wall_time_s", 0.0)),
                metadata={
                    **source.metadata,
                    "replay_of": source.branch_id,
                    "route_score": proposal.route.get("score"),
                    "rationale": proposal.route.get("rationale", []),
                },
            )
            graph.branches[branch.branch_id] = branch
            if branch.branch_id not in stage.branch_ids:
                stage.branch_ids.append(branch.branch_id)
        elif proposal.action == "review":
            branch = graph.branches[proposal.branch_id or ""]
            branch.review_count += 1
            branch.visits += 1
            branch.status = "review-needed"
        else:
            branch = graph.branches[proposal.branch_id or ""]
            branch.status = "pruned"
        graph.project_usage = graph_total_usage(graph)
        graph.updated_at = timestamp
        graph.action_log.append(
            self._action_record(graph, proposal, timestamp)
        )
        return graph

    def _action_record(self, graph: ProjectGraph, proposal: ActionProposal, timestamp: str) -> Any:
        from catfish_project_graph import ActionRecord

        return ActionRecord(
            action_id=f"{proposal.stage_id}:{proposal.action}:{len(graph.action_log) + 1}",
            action=proposal.action,
            stage_id=proposal.stage_id,
            selection_value=proposal.selection_value,
            reason=proposal.reason,
            scheduled_at=timestamp,
            branch_id=proposal.branch_id,
            created_branch_id=proposal.created_branch_id,
            route={
                "provider_id": proposal.route.get("provider_id"),
                "model": proposal.route.get("model"),
                "tierId": proposal.route.get("tierId"),
                "reasoningEffort": proposal.route.get("reasoningEffort"),
                "agent_group": proposal.route.get("agent_group"),
                "style": proposal.route.get("style"),
                "score": proposal.route.get("score"),
            },
            metadata=proposal.metadata,
        )

    def _proposals_for_stage(self, graph: ProjectGraph, stage: StageCell) -> list[ActionProposal]:
        branches = [graph.branches[branch_id] for branch_id in stage.branch_ids if branch_id in graph.branches]
        live_branches = [branch for branch in branches if branch.status not in {"pruned", "archived"}]
        proposals: list[ActionProposal] = []
        diversity_context = self._diversity_context(stage, live_branches)
        pending_reviews = [
            branch for branch in live_branches if branch.status in {"completed", "review-needed"} and not branch.parent_scores
        ]
        if pending_reviews and stage.review_required:
            for branch in pending_reviews:
                proposals.append(self._review_proposal(graph, stage, branch))
        if len(live_branches) < max(stage.min_competitors, 1) or self._has_diversity_shortfall(diversity_context):
            expand = self._expand_proposal(graph, stage, diversity_context)
            if expand is not None:
                proposals.append(expand)
        for branch in live_branches:
            if branch.status in {"selected", "pruned", "archived"}:
                continue
            if branch.parent_scores:
                proposals.append(self._deepen_proposal(graph, stage, branch, diversity_context))
                replay = self._replay_proposal(graph, stage, branch, diversity_context)
                if replay is not None:
                    proposals.append(replay)
            prune = self._prune_proposal(graph, stage, branch, diversity_context)
            if prune is not None:
                proposals.append(prune)
        return proposals

    def _review_proposal(self, graph: ProjectGraph, stage: StageCell, branch: Branch) -> ActionProposal:
        usage = self._estimate_usage(stage.difficulty, "review")
        frontier_pressure = max(0, stage.min_competitors - len(stage.branch_ids))
        selection_value = (
            1.05
            + _ACTION_BIAS["review"]
            + (0.05 * frontier_pressure)
            + self._stage_priority(graph, stage.stage_id)
            + (0.03 * branch.review_count)
            - self._cost_penalty(graph, stage, usage)
        )
        reason = (
            "Parent-only scoring gate is blocking advancement; schedule a parent review before deepen/replay."
        )
        return ActionProposal(
            action="review",
            stage_id=stage.stage_id,
            branch_id=branch.branch_id,
            selection_value=selection_value,
            reason=reason,
            estimated_usage=usage,
            metadata={"parent_only": True},
        )

    def _expand_proposal(
        self,
        graph: ProjectGraph,
        stage: StageCell,
        diversity_context: dict[str, Any],
    ) -> ActionProposal | None:
        variants = self._candidate_variants(stage, anchor_score=diversity_context["anchor_parent_score"])
        if not variants:
            return None
        best: ActionProposal | None = None
        frontier_shortfall = max(stage.target_frontier_width - diversity_context["live_count"], 0)
        for variant in variants:
            usage = self._estimate_usage(stage.difficulty, "expand", tier_id=variant["tierId"])
            if not self._within_budget(graph, stage, usage):
                continue
            diversity_bonus, diversity_reason = self._diversity_bonus(
                stage,
                diversity_context,
                provider_id=str(variant["provider_id"]),
                model=str(variant["model"]),
                agent_group=str(variant["agent_group"]),
                style=str(variant["style"]),
                action="expand",
            )
            route_prior = self._route_prior(variant)
            selection_value = (
                route_prior
                + (self.c_puct * route_prior * math.sqrt(max(diversity_context["parent_visits"], 1.0)))
                + (0.08 * frontier_shortfall)
                + _ACTION_BIAS["expand"]
                + self._stage_priority(graph, stage.stage_id)
                + diversity_bonus
                - self._cost_penalty(graph, stage, usage)
            )
            reason = (
                f"Expand {stage.stage_kind} frontier with {variant['provider_id']}:{variant['model']} / "
                f"{variant['agent_group']} / {variant['style']}; {diversity_reason}"
            )
            proposal = ActionProposal(
                action="expand",
                stage_id=stage.stage_id,
                selection_value=selection_value,
                reason=reason,
                created_branch_id=next_branch_id(graph, stage.stage_id),
                route=variant,
                estimated_usage=usage,
                metadata={
                    "label": f"{stage.stage_kind} candidate {variant['agent_group']} {variant['style']}",
                    "prior": route_prior,
                    "capabilities": [stage.stage_kind, stage.routing_task_category],
                },
            )
            if best is None or proposal.selection_value > best.selection_value:
                best = proposal
        return best

    def _deepen_proposal(
        self,
        graph: ProjectGraph,
        stage: StageCell,
        branch: Branch,
        diversity_context: dict[str, Any],
    ) -> ActionProposal:
        usage = self._estimate_usage(stage.difficulty, "deepen", tier_id=branch.tier_id or None)
        score = self._official_mean(branch)
        explore = self.c_puct * max(branch.prior, 0.01) * math.sqrt(max(diversity_context["parent_visits"], 1.0))
        explore = explore / (1.0 + branch.visits)
        diversity_bonus, diversity_reason = self._diversity_bonus(
            stage,
            diversity_context,
            provider_id=branch.provider_id,
            model=branch.model,
            agent_group=branch.agent_group,
            style=branch.style,
            action="deepen",
        )
        selection_value = score + explore + _ACTION_BIAS["deepen"] + diversity_bonus - self._cost_penalty(graph, stage, usage)
        selection_value += self._stage_priority(graph, stage.stage_id)
        reason = (
            f"Deepen {branch.branch_id} from official parent score {score:.2f}; {diversity_reason}"
        )
        return ActionProposal(
            action="deepen",
            stage_id=stage.stage_id,
            branch_id=branch.branch_id,
            selection_value=selection_value,
            reason=reason,
            route={
                "provider_id": branch.provider_id,
                "model": branch.model,
                "tierId": branch.tier_id,
                "reasoningEffort": branch.reasoning_effort,
                "agent_group": branch.agent_group,
                "style": branch.style,
            },
            estimated_usage=usage,
            metadata={"prior": branch.prior},
        )

    def _replay_proposal(
        self,
        graph: ProjectGraph,
        stage: StageCell,
        branch: Branch,
        diversity_context: dict[str, Any],
    ) -> ActionProposal | None:
        if branch.replay_count >= stage.replay_cap:
            return None
        variants = self._candidate_variants(
            stage,
            anchor_score=max(self._official_mean(branch), diversity_context["anchor_parent_score"]),
            exclude_stack={
                "provider_id": branch.provider_id,
                "model": branch.model,
                "agent_group": branch.agent_group,
                "style": branch.style,
            },
        )
        if not variants:
            return None
        best: ActionProposal | None = None
        for variant in variants:
            usage = self._estimate_usage(stage.difficulty, "replay", tier_id=variant["tierId"])
            if not self._within_budget(graph, stage, usage):
                continue
            diversity_bonus, diversity_reason = self._diversity_bonus(
                stage,
                diversity_context,
                provider_id=str(variant["provider_id"]),
                model=str(variant["model"]),
                agent_group=str(variant["agent_group"]),
                style=str(variant["style"]),
                action="replay",
            )
            route_prior = max(self._route_prior(variant), self._official_mean(branch))
            selection_value = (
                (0.65 * self._official_mean(branch))
                + (0.35 * route_prior)
                + _ACTION_BIAS["replay"]
                + self._stage_priority(graph, stage.stage_id)
                + diversity_bonus
                - self._cost_penalty(graph, stage, usage)
                - (0.05 * branch.replay_count)
            )
            reason = (
                f"Replay {branch.branch_id} under a shifted stack to preserve competition; {diversity_reason}"
            )
            proposal = ActionProposal(
                action="replay",
                stage_id=stage.stage_id,
                branch_id=branch.branch_id,
                selection_value=selection_value,
                reason=reason,
                created_branch_id=next_branch_id(graph, stage.stage_id),
                route=variant,
                estimated_usage=usage,
                metadata={
                    "label": f"{branch.label} replay",
                    "prior": route_prior,
                },
            )
            if best is None or proposal.selection_value > best.selection_value:
                best = proposal
        return best

    def _prune_proposal(
        self,
        graph: ProjectGraph,
        stage: StageCell,
        branch: Branch,
        diversity_context: dict[str, Any],
    ) -> ActionProposal | None:
        score = self._official_mean(branch)
        over_budget = branch.projected_cost_usd > max(stage.budget_ceiling.usd_budget * 0.45, 0.01)
        too_many_failures = branch.failure_count >= 2
        weak = bool(branch.parent_scores) and score < stage.prune_below_score
        if not (over_budget or too_many_failures or weak):
            return None
        savings = max(branch.projected_cost_usd, 0.05)
        diversity_bonus, diversity_reason = self._diversity_bonus(
            stage,
            diversity_context,
            provider_id=branch.provider_id,
            model=branch.model,
            agent_group=branch.agent_group,
            style=branch.style,
            action="prune",
        )
        selection_value = (
            (0.55 * (1.0 - score))
            + (0.08 * branch.failure_count)
            + (0.05 if over_budget else 0.0)
            + _ACTION_BIAS["prune"]
            + self._stage_priority(graph, stage.stage_id)
            + max(0.0, -diversity_bonus)
            + min(savings, 0.25)
        )
        reason = (
            f"Prune {branch.branch_id} because official parent score={score:.2f}, "
            f"failure_count={branch.failure_count}, projected_cost={branch.projected_cost_usd:.2f}; {diversity_reason}"
        )
        return ActionProposal(
            action="prune",
            stage_id=stage.stage_id,
            branch_id=branch.branch_id,
            selection_value=selection_value,
            reason=reason,
            route={
                "provider_id": branch.provider_id,
                "model": branch.model,
                "tierId": branch.tier_id,
                "agent_group": branch.agent_group,
                "style": branch.style,
            },
            estimated_usage=self._estimate_usage(stage.difficulty, "prune"),
        )

    def _candidate_variants(
        self,
        stage: StageCell,
        *,
        anchor_score: float,
        exclude_stack: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        variants: list[dict[str, Any]] = []
        for provider in self.registry.get("providers", []):
            for tier_id in provider.get("modelTiers", {}):
                payload = evaluate_provider(
                    dict(provider),
                    self.health_by_provider.get(str(provider.get("id"))),
                    self.ledger,
                    machine_id=self.routing.get("defaultMachineId", "dev-intern-02"),
                    task_category=stage.routing_task_category,
                    difficulty=stage.difficulty,
                    tier_id=str(tier_id),
                    reasoning_length=reasoning_length_for_tier(self.routing, str(tier_id)),
                    parent_score=anchor_score,
                    requested_model=None,
                    reference_date=self.reference_date,
                )
                if payload["blockers"]:
                    continue
                for agent_group in stage.agent_groups:
                    for style in stage.styles:
                        variant = {
                            **payload,
                            "agent_group": agent_group,
                            "style": style,
                        }
                        if exclude_stack and all(
                            str(variant.get(key, "")) == str(exclude_stack.get(key, ""))
                            for key in ("provider_id", "model", "agent_group", "style")
                        ):
                            continue
                        variants.append(variant)
        variants.sort(key=lambda item: float(item.get("score", 0.0)), reverse=True)
        return variants

    def _diversity_context(self, stage: StageCell, branches: Sequence[Branch]) -> dict[str, Any]:
        counts = {
            "provider": Counter(branch.provider_id for branch in branches if branch.provider_id),
            "model": Counter(branch.model for branch in branches if branch.model),
            "agent_group": Counter(branch.agent_group for branch in branches if branch.agent_group),
            "style": Counter(branch.style for branch in branches if branch.style),
            "stack": Counter(
                f"{branch.provider_id}|{branch.model}|{branch.agent_group}|{branch.style}"
                for branch in branches
                if any((branch.provider_id, branch.model, branch.agent_group, branch.style))
            ),
        }
        parent_visits = sum(max(branch.visits, 1) for branch in branches) or 1
        anchor_parent_score = max((self._official_mean(branch) for branch in branches if branch.parent_scores), default=0.5)
        eligible_provider_ids: set[str] = set()
        for provider in self.registry.get("providers", []):
            for tier_id in provider.get("modelTiers", {}):
                payload = evaluate_provider(
                    dict(provider),
                    self.health_by_provider.get(str(provider.get("id"))),
                    self.ledger,
                    machine_id=self.routing.get("defaultMachineId", "dev-intern-02"),
                    task_category=stage.routing_task_category,
                    difficulty=stage.difficulty,
                    tier_id=str(tier_id),
                    reasoning_length=reasoning_length_for_tier(self.routing, str(tier_id)),
                    parent_score=anchor_parent_score,
                    requested_model=None,
                    reference_date=self.reference_date,
                )
                if not payload["blockers"]:
                    eligible_provider_ids.add(str(provider.get("id")))
                    break
        feasible = {
            "provider": len(eligible_provider_ids),
            "model": len({provider["model"] for provider in self._candidate_variants(stage, anchor_score=anchor_parent_score)}),
            "agent_group": len(stage.agent_groups),
            "style": len(stage.styles),
        }
        return {
            "counts": counts,
            "parent_visits": parent_visits,
            "anchor_parent_score": anchor_parent_score,
            "live_count": len(branches),
            "feasible": feasible,
        }

    def _has_diversity_shortfall(self, diversity_context: dict[str, Any]) -> bool:
        counts = diversity_context["counts"]
        feasible = diversity_context["feasible"]
        return any(
            len(counts[dimension]) < feasible_target
            for dimension, feasible_target in (
                ("provider", min(2, feasible["provider"])),
                ("model", min(2, feasible["model"])),
                ("agent_group", min(2, feasible["agent_group"])),
                ("style", min(2, feasible["style"])),
            )
        )

    def _diversity_bonus(
        self,
        stage: StageCell,
        diversity_context: dict[str, Any],
        *,
        provider_id: str,
        model: str,
        agent_group: str,
        style: str,
        action: str,
    ) -> tuple[float, str]:
        counts = diversity_context["counts"]
        feasible = diversity_context["feasible"]
        targets = stage.diversity_targets
        value_map = {
            "provider": provider_id,
            "model": model,
            "agent_group": agent_group,
            "style": style,
        }
        configured_targets = {
            "provider": targets.provider_min_distinct,
            "model": targets.model_min_distinct,
            "agent_group": targets.agent_group_min_distinct,
            "style": targets.style_min_distinct,
        }
        bonus = 0.0
        reasons: list[str] = []
        for dimension, value in value_map.items():
            current_count = len(counts[dimension])
            effective_target = min(configured_targets[dimension], feasible[dimension] or configured_targets[dimension])
            if effective_target <= 0:
                continue
            if current_count < effective_target and value and value not in counts[dimension]:
                gain = targets.expand_bonus / effective_target
                bonus += gain
                reasons.append(f"adds new {dimension}={value}")
        stack_key = f"{provider_id}|{model}|{agent_group}|{style}"
        stack_count = counts["stack"].get(stack_key, 0)
        total = max(sum(counts["stack"].values()), 1)
        share = stack_count / total
        if stack_count == 0:
            bonus += targets.novel_stack_bonus
            reasons.append("new full stack")
        elif share >= targets.max_stack_share:
            penalty = targets.collapse_penalty * share
            bonus -= penalty
            reasons.append(f"stack share {share:.2f} exceeds anti-collapse threshold")
        if action == "replay" and bonus > 0.0:
            bonus += targets.replay_bonus
        if not reasons:
            reasons.append("no diversity gain")
        return bonus, ", ".join(reasons)

    def _estimate_usage(self, difficulty: str, action: str, *, tier_id: str | None = None) -> dict[str, float]:
        base = dict(_BASE_ESTIMATES.get(difficulty, _BASE_ESTIMATES["medium"]))
        multiplier = _ACTION_MULTIPLIERS[action]
        tier_multiplier = 1.0
        if tier_id == "quick":
            tier_multiplier = 0.65
        elif tier_id == "deep":
            tier_multiplier = 1.4
        return {
            "tokens": round(base["tokens"] * multiplier * tier_multiplier, 3),
            "cost_usd": round(base["cost_usd"] * multiplier * tier_multiplier, 6),
            "wall_time_s": round(base["wall_time_s"] * multiplier * tier_multiplier, 3),
        }

    def _within_budget(self, graph: ProjectGraph, stage: StageCell, usage: dict[str, float]) -> bool:
        total_usage = graph_total_usage(graph)
        stage_usage = graph_usage_for_stage(graph, stage.stage_id)
        return (
            (total_usage.cost_usd + usage["cost_usd"] <= graph.project_budget.usd_budget + 1e-9)
            and (stage_usage.cost_usd + usage["cost_usd"] <= stage.budget_ceiling.usd_budget + 1e-9)
            and (total_usage.prompt_tokens + usage["tokens"] <= graph.project_budget.token_budget + 1e-9)
            and (stage_usage.prompt_tokens + usage["tokens"] <= stage.budget_ceiling.token_budget + 1e-9)
        )

    def _cost_penalty(self, graph: ProjectGraph, stage: StageCell, usage: dict[str, float]) -> float:
        total_usage = graph_total_usage(graph)
        stage_usage = graph_usage_for_stage(graph, stage.stage_id)
        project_remaining = max(graph.project_budget.usd_budget - total_usage.cost_usd, 0.01)
        stage_remaining = max(stage.budget_ceiling.usd_budget - stage_usage.cost_usd, 0.01)
        project_ratio = usage["cost_usd"] / project_remaining
        stage_ratio = usage["cost_usd"] / stage_remaining
        return 0.22 * max(project_ratio, stage_ratio)

    def _route_prior(self, route: dict[str, Any]) -> float:
        score = float(route.get("score", 0.0))
        return max(0.05, min(score / 1.6, 1.0))

    def _official_mean(self, branch: Branch) -> float:
        if not branch.parent_scores:
            return 0.0
        return sum(branch.parent_scores) / len(branch.parent_scores)

    def _stage_priority(self, graph: ProjectGraph, stage_id: str) -> float:
        try:
            index = graph.stage_order.index(stage_id)
        except ValueError:
            return 0.0
        remaining = len(graph.stage_order) - index
        return 0.03 * remaining


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Catfish file-backed scheduler and orchestration engine.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    bootstrap = subparsers.add_parser("bootstrap", help="Bootstrap a scheduler graph from runtime operations.")
    bootstrap.add_argument("--ops", type=Path, required=True, help="Runtime operations JSON for catfish_runtime.")
    bootstrap.add_argument("--project-id", required=True)
    bootstrap.add_argument("--graph-out", type=Path, required=True)
    bootstrap.add_argument("--graph-id", default="")
    bootstrap.add_argument("--machine", default="dev-intern-02")

    next_action = subparsers.add_parser("next-action", help="Recommend the next scheduler action.")
    next_action.add_argument("--graph", type=Path, required=True)
    next_action.add_argument("--apply", action="store_true", help="Apply the chosen action back into the graph.")
    next_action.add_argument("--emit-schema-snapshot", action="store_true")

    snapshot = subparsers.add_parser("snapshot", help="Render the current graph JSON.")
    snapshot.add_argument("--graph", type=Path, required=True)
    snapshot.add_argument("--schema", action="store_true", help="Render scheduling_graph-style snapshot.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    scheduler = CatfishScheduler()

    if args.command == "bootstrap":
        graph = scheduler.bootstrap_graph_from_runtime_ops(
            ops_path=args.ops,
            project_id=args.project_id,
            graph_id=args.graph_id or None,
            machine_id=args.machine,
        )
        save_project_graph(args.graph_out, graph)
        print(json.dumps(graph.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    graph = load_project_graph(args.graph)
    if args.command == "snapshot":
        payload = build_schema_snapshot(graph) if args.schema else graph.to_dict()
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    proposal = scheduler.recommend_next_action(graph)
    if args.apply:
        scheduler.apply_action(graph, proposal)
        save_project_graph(args.graph, graph)
        payload = {
            "selected_action": proposal.to_dict(),
            "graph": build_schema_snapshot(graph) if args.emit_schema_snapshot else graph.to_dict(),
        }
    else:
        payload = proposal.to_dict()
        if args.emit_schema_snapshot:
            payload = {
                "selected_action": payload,
                "graph": build_schema_snapshot(graph),
            }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
