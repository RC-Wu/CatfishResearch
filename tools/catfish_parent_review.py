from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


SCHEMA_VERSION = "catfish.parent-review.v1"

DIMENSIONS = (
    "idea",
    "model",
    "provider",
    "agent_group",
    "diversity_contribution",
    "resource_usage",
    "outcome_quality",
    "risk",
)
POSITIVE_DIMENSIONS = tuple(dimension for dimension in DIMENSIONS if dimension != "risk")

LEGACY_DIMENSION_NAMES = {
    "idea": "idea",
    "model": "model",
    "provider": "provider",
    "agent_group": "agentGroup",
    "resource_usage": "resourceUsage",
    "outcome_quality": "outcomeQuality",
    "risk": "risk",
}

DIMENSION_ALIASES = {
    "idea": "idea",
    "model": "model",
    "provider": "provider",
    "agent_group": "agent_group",
    "agentGroup": "agent_group",
    "diversity_contribution": "diversity_contribution",
    "diversityContribution": "diversity_contribution",
    "resource_usage": "resource_usage",
    "resourceUsage": "resource_usage",
    "outcome_quality": "outcome_quality",
    "outcomeQuality": "outcome_quality",
    "risk": "risk",
}

DEFAULT_STAGE_WEIGHTS: dict[str, dict[str, float]] = {
    "ideation": {
        "idea": 0.24,
        "model": 0.08,
        "provider": 0.05,
        "agent_group": 0.10,
        "diversity_contribution": 0.18,
        "resource_usage": 0.08,
        "outcome_quality": 0.19,
        "risk": 0.08,
    },
    "planning": {
        "idea": 0.18,
        "model": 0.08,
        "provider": 0.05,
        "agent_group": 0.10,
        "diversity_contribution": 0.10,
        "resource_usage": 0.09,
        "outcome_quality": 0.24,
        "risk": 0.16,
    },
    "implementation": {
        "idea": 0.05,
        "model": 0.09,
        "provider": 0.10,
        "agent_group": 0.11,
        "diversity_contribution": 0.08,
        "resource_usage": 0.14,
        "outcome_quality": 0.28,
        "risk": 0.15,
    },
    "review": {
        "idea": 0.05,
        "model": 0.10,
        "provider": 0.10,
        "agent_group": 0.10,
        "diversity_contribution": 0.05,
        "resource_usage": 0.10,
        "outcome_quality": 0.26,
        "risk": 0.24,
    },
    "default": {
        "idea": 0.10,
        "model": 0.10,
        "provider": 0.10,
        "agent_group": 0.10,
        "diversity_contribution": 0.10,
        "resource_usage": 0.10,
        "outcome_quality": 0.25,
        "risk": 0.15,
    },
}

REASONING_LENGTH_BY_TIER = {
    "quick": "short",
    "balanced": "medium",
    "deep": "long",
}

ALLOWED_DECISIONS = {
    "selected",
    "survive",
    "merge",
    "replay",
    "hold",
    "pruned",
    "archived",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def clamp(value: object, lower: float = 0.0, upper: float = 1.0) -> float:
    numeric = float(value)
    if numeric < lower:
        return lower
    if numeric > upper:
        return upper
    return numeric


def round_map(values: dict[str, float], digits: int = 6) -> dict[str, float]:
    return {key: round(float(value), digits) for key, value in values.items()}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def canonical_dimension_name(name: str) -> str:
    canonical = DIMENSION_ALIASES.get(name)
    if canonical is None:
        raise ValueError(f"Unsupported dimension {name}")
    return canonical


def normalize_dimension_map(values: dict[str, Any], *, label: str) -> dict[str, float]:
    normalized: dict[str, float] = {}
    for raw_name, raw_value in values.items():
        canonical = canonical_dimension_name(str(raw_name))
        if canonical in normalized:
            raise ValueError(f"{label} contains duplicate values for {canonical}")
        normalized[canonical] = clamp(raw_value)
    missing = [dimension for dimension in DIMENSIONS if dimension not in normalized]
    if missing:
        raise ValueError(f"{label} is missing required dimensions: {', '.join(missing)}")
    return {dimension: round(normalized[dimension], 6) for dimension in DIMENSIONS}


def normalize_weights(values: dict[str, Any] | None, *, stage_kind: str) -> dict[str, float]:
    merged = dict(DEFAULT_STAGE_WEIGHTS.get(stage_kind, DEFAULT_STAGE_WEIGHTS["default"]))
    if values:
        for raw_name, raw_value in values.items():
            canonical = canonical_dimension_name(str(raw_name))
            numeric = float(raw_value)
            if numeric < 0.0:
                raise ValueError(f"Weight for {canonical} cannot be negative")
            merged[canonical] = numeric
    total = sum(merged.values())
    if total <= 0.0:
        raise ValueError("Weight total must be positive")
    return {dimension: round(merged[dimension] / total, 6) for dimension in DIMENSIONS}


def legacy_dimension_projection(values: dict[str, float]) -> dict[str, float]:
    return {
        legacy_name: round(float(values[dimension]), 6)
        for dimension, legacy_name in LEGACY_DIMENSION_NAMES.items()
    }


def normalize_confidence(value: object | None) -> float:
    if value is None:
        return 1.0
    return round(clamp(value), 6)


def normalize_portfolio_policy(policy: dict[str, Any] | None) -> dict[str, Any]:
    payload = dict(policy or {})
    return {
        "max_survivors": max(int(payload.get("max_survivors", 2)), 1),
        "min_survivors": max(int(payload.get("min_survivors", 1)), 1),
        "composite_floor": clamp(payload.get("composite_floor", 0.55)),
        "max_score_gap": clamp(payload.get("max_score_gap", 0.12)),
        "diversity_floor": clamp(payload.get("diversity_floor", 0.70)),
        "confidence_penalty_weight": clamp(payload.get("confidence_penalty_weight", 0.05)),
        "emit_stack_capabilities": bool(payload.get("emit_stack_capabilities", True)),
    }


def infer_stage_kind(payload: dict[str, Any]) -> str:
    explicit = str(payload.get("stage_kind") or payload.get("task_category") or "").strip().lower()
    if explicit:
        return explicit
    stage_id = str(payload.get("stage_id") or payload.get("competition_id") or "").strip().lower()
    for key in DEFAULT_STAGE_WEIGHTS:
        if key != "default" and key in stage_id:
            return key
    return "default"


def infer_reasoning_tier(child: dict[str, Any], payload: dict[str, Any]) -> str:
    provider_assignment = dict(child.get("provider_assignment") or {})
    metadata = dict(provider_assignment.get("metadata") or {})
    for key in ("routing_tier", "tier", "reasoning_tier"):
        value = metadata.get(key)
        if value:
            return str(value)
    top_level = payload.get("reasoning_tier")
    if top_level:
        return str(top_level)
    reasoning_effort = str(provider_assignment.get("reasoning_effort") or "").strip().lower()
    if reasoning_effort in {"high", "xhigh"}:
        return "deep"
    if reasoning_effort in {"low", "quick"}:
        return "quick"
    return "balanced"


def infer_reasoning_length(reasoning_tier: str, child: dict[str, Any], payload: dict[str, Any]) -> str:
    provider_assignment = dict(child.get("provider_assignment") or {})
    metadata = dict(provider_assignment.get("metadata") or {})
    value = metadata.get("reasoning_length") or payload.get("reasoning_length")
    if value:
        return str(value)
    return REASONING_LENGTH_BY_TIER.get(reasoning_tier, "medium")


def resource_snapshot(child: dict[str, Any]) -> dict[str, Any]:
    usage = dict(child.get("resource_usage") or {})
    provider_assignment = dict(child.get("provider_assignment") or {})
    metadata = dict(child.get("metadata") or {})
    return {
        "cost_usd": round(float(usage.get("cost_usd", 0.0)), 6),
        "wall_time_s": round(float(usage.get("wall_time_s", 0.0)), 6),
        "prompt_tokens": int(usage.get("prompt_tokens", 0)),
        "completion_tokens": int(usage.get("completion_tokens", 0)),
        "provider": str(provider_assignment.get("provider") or ""),
        "model": str(provider_assignment.get("model") or ""),
        "agent_group": str(
            metadata.get("agent_group")
            or metadata.get("agent_group_id")
            or child.get("agent_group")
            or child.get("node_id")
            or ""
        ),
    }


def legacy_resource_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "cost": round(float(snapshot["cost_usd"]), 6),
        "wallTimeSeconds": round(float(snapshot["wall_time_s"]), 6),
        "provider": snapshot["provider"],
        "model": snapshot["model"],
        "agentGroup": snapshot["agent_group"],
    }


def stack_signature(child: dict[str, Any]) -> str:
    snapshot = resource_snapshot(child)
    return "|".join([snapshot["provider"] or "-", snapshot["model"] or "-", snapshot["agent_group"] or "-"])


def normalize_decision_hint(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    aliases = {
        "keep": "survive",
        "keep_for_diversity": "survive",
        "wildcard": "survive",
    }
    text = aliases.get(text, text)
    if text not in ALLOWED_DECISIONS:
        raise ValueError(f"Unsupported decision hint {value}")
    return text


def compute_composite(
    scores: dict[str, float],
    weights: dict[str, float],
    *,
    confidence: float,
    confidence_penalty_weight: float,
) -> tuple[float, float, float]:
    weighted_positive = sum(float(weights[dimension]) * float(scores[dimension]) for dimension in POSITIVE_DIMENSIONS)
    risk_penalty = float(weights["risk"]) * float(scores["risk"])
    confidence_penalty = (1.0 - confidence) * confidence_penalty_weight
    raw = weighted_positive - risk_penalty - confidence_penalty
    normalized = clamp(raw)
    return round(raw, 6), round(confidence_penalty, 6), round(normalized, 6)


def review_sort_key(scorecard: dict[str, Any]) -> tuple[float, float, float, float, float]:
    snapshot = scorecard["resource_snapshot"]
    scores = scorecard["scores"]
    return (
        float(scorecard["composite_normalized"]),
        float(scores["outcome_quality"]),
        float(scores["diversity_contribution"]),
        -float(scores["risk"]),
        -float(snapshot["cost_usd"]),
    )


def derive_routing_effect(scorecard: dict[str, Any]) -> str:
    decision = str(scorecard["decision"])
    scores = scorecard["scores"]
    provider_score = float(scores["provider"])
    risk_score = float(scores["risk"])
    normalized_composite = float(scorecard["composite_normalized"])
    if decision in {"selected", "survive"} and provider_score >= 0.65 and risk_score <= 0.45:
        return "prefer"
    if provider_score <= 0.20 or (decision in {"pruned", "replay"} and risk_score >= 0.80):
        return "block"
    if normalized_composite < 0.45 or decision in {"pruned", "replay"}:
        return "penalize"
    return "neutral"


def derive_score_delta(scorecard: dict[str, Any]) -> float:
    scores = scorecard["scores"]
    positive_signal = (
        float(scores["provider"]) + float(scores["outcome_quality"]) + float(scores["resource_usage"])
    ) / 3.0
    raw = positive_signal - float(scores["risk"])
    if scorecard["decision"] in {"selected", "survive"}:
        raw += 0.10
    elif scorecard["decision"] in {"pruned", "replay"}:
        raw -= 0.10
    return round(clamp(raw, lower=-1.0, upper=1.0), 6)


def decision_reason(
    scorecard: dict[str, Any],
    *,
    decision: str,
    mode: str,
    kept_for_diversity: bool,
    winner_run_id: str,
) -> str:
    run_id = str(scorecard["run_id"])
    scores = scorecard["scores"]
    if run_id == winner_run_id:
        return (
            f"Parent selected {run_id} as the official winner with composite "
            f"{scorecard['composite_normalized']:.3f} and outcome_quality {scores['outcome_quality']:.3f}."
        )
    if decision == "survive":
        return (
            f"Parent kept {run_id} in the portfolio because it preserves stack diversity "
            f"({scorecard['stack_signature']}) with diversity_contribution {scores['diversity_contribution']:.3f}."
        )
    if decision == "merge":
        return f"Parent marked {run_id} for merge because it contains non-overlapping value."
    if decision == "replay":
        return f"Parent marked {run_id} for replay because the concept is useful but the current stack underperformed."
    if decision == "hold":
        return f"Parent placed {run_id} on hold pending new evidence or budget."
    if mode == "portfolio_keep" and kept_for_diversity:
        return f"Parent preserved {run_id} for diversity coverage."
    return f"Parent pruned {run_id} after comparing normalized scorecards under {mode}."


def choose_decisions(
    scorecards: list[dict[str, Any]],
    *,
    decision_mode: str,
    policy: dict[str, Any],
) -> dict[str, Any]:
    ordered = sorted(scorecards, key=review_sort_key, reverse=True)
    winner = ordered[0]
    retained_run_ids: list[str] = [str(winner["run_id"])]
    retained_signatures = {str(winner["stack_signature"])}
    kept_for_diversity: set[str] = set()

    if decision_mode == "portfolio_keep":
        max_survivors = int(policy["max_survivors"])
        min_survivors = int(policy["min_survivors"])
        composite_floor = float(policy["composite_floor"])
        max_score_gap = float(policy["max_score_gap"])
        diversity_floor = float(policy["diversity_floor"])
        winner_score = float(winner["composite_normalized"])

        for scorecard in ordered[1:]:
            if len(retained_run_ids) >= max_survivors:
                break
            decision_hint = scorecard["decision_hint"]
            explicit_keep = decision_hint == "survive"
            gap = max(winner_score - float(scorecard["composite_normalized"]), 0.0)
            signature = str(scorecard["stack_signature"])
            signature_is_new = signature not in retained_signatures
            diverse_enough = float(scorecard["scores"]["diversity_contribution"]) >= diversity_floor
            strong_enough = float(scorecard["composite_normalized"]) >= composite_floor
            if explicit_keep or (strong_enough and gap <= max_score_gap) or (signature_is_new and diverse_enough):
                retained_run_ids.append(str(scorecard["run_id"]))
                retained_signatures.add(signature)
                if signature_is_new and diverse_enough:
                    kept_for_diversity.add(str(scorecard["run_id"]))

        if len(retained_run_ids) < min_survivors:
            for scorecard in ordered[1:]:
                run_id = str(scorecard["run_id"])
                if run_id in retained_run_ids:
                    continue
                retained_run_ids.append(run_id)
                if len(retained_run_ids) >= min_survivors:
                    break

    decision_by_run_id: dict[str, str] = {}
    reason_by_run_id: dict[str, str] = {}
    pruned_run_ids: list[str] = []

    for scorecard in ordered:
        run_id = str(scorecard["run_id"])
        hint = scorecard["decision_hint"]
        if run_id == str(winner["run_id"]):
            decision = "selected"
        elif run_id in retained_run_ids:
            decision = "survive"
        elif hint in {"merge", "replay", "hold", "archived"}:
            decision = hint
        else:
            decision = "pruned"
            pruned_run_ids.append(run_id)
        decision_by_run_id[run_id] = decision
        reason_by_run_id[run_id] = decision_reason(
            scorecard,
            decision=decision,
            mode=decision_mode,
            kept_for_diversity=run_id in kept_for_diversity,
            winner_run_id=str(winner["run_id"]),
        )

    return {
        "winner_run_id": str(winner["run_id"]),
        "retained_run_ids": retained_run_ids,
        "pruned_run_ids": pruned_run_ids,
        "kept_for_diversity_run_ids": sorted(kept_for_diversity),
        "decision_by_run_id": decision_by_run_id,
        "reason_by_run_id": reason_by_run_id,
        "ordered_run_ids": [str(scorecard["run_id"]) for scorecard in ordered],
    }


def build_declared_capability_updates(
    *,
    child: dict[str, Any],
    scorecard: dict[str, Any],
    parent_node_id: str,
    emit_stack_capabilities: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    evaluator_note = dict(child.get("evaluator_note") or {})
    confidence = float(scorecard["confidence"])
    runtime_updates: list[dict[str, Any]] = []
    audit_records: list[dict[str, Any]] = []
    seen_capabilities: set[str] = set()

    for item in evaluator_note.get("capabilities", []):
        capability = str(item["capability"]).strip()
        if not capability:
            raise ValueError(f"Capability update for {child['run_id']} is missing capability")
        score = round(clamp(item.get("score", scorecard["composite_normalized"])), 6)
        update = {
            "node_id": child["node_id"],
            "capability": capability,
            "score": score,
            "summary": str(
                item.get("summary")
                or f"Parent review {scorecard['scorecard_id']} recorded {capability} at {score:.3f}."
            ),
            "confidence": round(clamp(item.get("confidence", confidence)), 6),
        }
        runtime_updates.append(update)
        audit_records.append(
            {
                "update_id": f"{scorecard['scorecard_id']}:{capability}",
                "source": "declared",
                "source_scorecard_id": scorecard["scorecard_id"],
                "parent_node_id": parent_node_id,
                "run_id": child["run_id"],
                **update,
            }
        )
        seen_capabilities.add(capability)

    if emit_stack_capabilities:
        snapshot = scorecard["resource_snapshot"]
        derived = [
            ("provider", snapshot["provider"], scorecard["scores"]["provider"]),
            ("model", snapshot["model"], scorecard["scores"]["model"]),
            ("agent_group", snapshot["agent_group"], scorecard["scores"]["agent_group"]),
        ]
        for prefix, value, score in derived:
            if not value:
                continue
            capability = f"{prefix}:{value}"
            if capability in seen_capabilities:
                continue
            update = {
                "node_id": child["node_id"],
                "capability": capability,
                "score": round(float(score), 6),
                "summary": (
                    f"Parent review {scorecard['scorecard_id']} audited {prefix} stack quality "
                    f"for {value}."
                ),
                "confidence": confidence,
            }
            runtime_updates.append(update)
            audit_records.append(
                {
                    "update_id": f"{scorecard['scorecard_id']}:{capability}",
                    "source": "derived",
                    "source_scorecard_id": scorecard["scorecard_id"],
                    "parent_node_id": parent_node_id,
                    "run_id": child["run_id"],
                    **update,
                }
            )

    return runtime_updates, audit_records


def build_router_entry(
    *,
    review_id: str,
    verdict_id: str,
    parent_node_id: str,
    timestamp: str,
    parent_score: float,
    task_category: str,
    difficulty: str,
    payload: dict[str, Any],
    child: dict[str, Any],
    scorecard: dict[str, Any],
) -> dict[str, Any] | None:
    provider_assignment = dict(child.get("provider_assignment") or {})
    provider_id = str(provider_assignment.get("provider") or "").strip()
    if not provider_id:
        return None
    reasoning_tier = infer_reasoning_tier(child, payload)
    reasoning_length = infer_reasoning_length(reasoning_tier, child, payload)
    return {
        "id": f"{review_id}:{child['run_id']}:{provider_id}",
        "providerId": provider_id,
        "taskCategory": task_category,
        "difficulty": difficulty,
        "reasoningTier": reasoning_tier,
        "reasoningLength": reasoning_length,
        "parentScore": round(parent_score, 6),
        "recency": timestamp,
        "confidence": round(float(scorecard["confidence"]), 6),
        "routingEffect": derive_routing_effect(scorecard),
        "scoreDelta": derive_score_delta(scorecard),
        "notes": (
            f"Parent {parent_node_id} reviewed run {child['run_id']} with decision "
            f"{scorecard['decision']} and composite {scorecard['composite_normalized']:.3f}."
        ),
        "sourceReviewId": review_id,
        "sourceVerdictId": verdict_id,
        "sourceScorecardId": scorecard["scorecard_id"],
        "parentNodeId": parent_node_id,
        "runId": child["run_id"],
        "decision": scorecard["decision"],
        "modelId": scorecard["resource_snapshot"]["model"],
        "agentGroupId": scorecard["resource_snapshot"]["agent_group"],
        "dimensionScores": round_map(scorecard["scores"]),
        "evidenceRefs": list(scorecard["evidence_refs"]),
    }


def build_parent_review(payload: dict[str, Any]) -> dict[str, Any]:
    project_id = str(payload.get("project_id") or payload.get("projectId") or "")
    competition_id = str(payload["competition_id"])
    parent_node_id = str(payload["parent_node_id"])
    official_writer_node_id = str(payload.get("official_writer_node_id") or parent_node_id)
    if official_writer_node_id != parent_node_id:
        raise ValueError("Official scorecards/verdicts must be authored by the competition parent")

    children = list(payload.get("children") or [])
    if not children:
        raise ValueError("Parent review requires at least one child run")

    stage_kind = infer_stage_kind(payload)
    stage_id = str(payload.get("stage_id") or stage_kind or competition_id)
    review_id = str(payload.get("review_id") or f"{competition_id}.parent-review")
    timestamp = str(payload.get("timestamp") or utc_now())
    decision_mode = str(payload.get("decision_mode") or "winner_pick").strip().lower()
    if decision_mode not in {"winner_pick", "portfolio_keep"}:
        raise ValueError(f"Unsupported decision_mode {decision_mode}")
    task_category = str(payload.get("task_category") or stage_kind or "general")
    difficulty = str(payload.get("difficulty") or "medium")
    weights = normalize_weights(payload.get("weights"), stage_kind=stage_kind)
    policy = normalize_portfolio_policy(payload.get("portfolio_policy"))
    parent_score = round(clamp(payload.get("parent_score", 0.5)), 6)
    verdict_id = str(payload.get("verdict_id") or f"{review_id}.verdict")

    scorecards: list[dict[str, Any]] = []
    runtime_capability_updates: list[dict[str, Any]] = []
    capability_update_log: list[dict[str, Any]] = []
    router_entries: list[dict[str, Any]] = []
    children_by_run_id: dict[str, dict[str, Any]] = {}

    for child in children:
        run_id = str(child["run_id"])
        if run_id in children_by_run_id:
            raise ValueError(f"Duplicate run_id {run_id}")
        children_by_run_id[run_id] = child
        evaluator_note = dict(child.get("evaluator_note") or {})
        author_node_id = str(evaluator_note.get("author_node_id") or parent_node_id)
        if author_node_id != parent_node_id:
            raise ValueError(
                f"Official evaluator note for run {run_id} must be authored by parent {parent_node_id}"
            )
        scores = normalize_dimension_map(
            dict(evaluator_note.get("dimension_scores") or evaluator_note.get("scores") or {}),
            label=f"evaluator note for {run_id}",
        )
        confidence = normalize_confidence(evaluator_note.get("confidence"))
        raw_composite, confidence_penalty, normalized_composite = compute_composite(
            scores,
            weights,
            confidence=confidence,
            confidence_penalty_weight=float(policy["confidence_penalty_weight"]),
        )
        snapshot = resource_snapshot(child)
        scorecard = {
            "scorecard_id": str(evaluator_note.get("scorecard_id") or f"{review_id}.{run_id}"),
            "review_id": review_id,
            "competition_id": competition_id,
            "parent_node_id": parent_node_id,
            "official_writer_node_id": official_writer_node_id,
            "child_node_id": str(child["node_id"]),
            "run_id": run_id,
            "stage_id": stage_id,
            "stage_kind": stage_kind,
            "timestamp": timestamp,
            "weights": dict(weights),
            "scores": dict(scores),
            "confidence": confidence,
            "confidence_penalty": confidence_penalty,
            "composite_raw": raw_composite,
            "composite_normalized": normalized_composite,
            "decision_hint": normalize_decision_hint(evaluator_note.get("decision_hint")),
            "decision": "pending",
            "decision_reason": "",
            "evidence_refs": list(evaluator_note.get("evidence_refs") or []),
            "resource_snapshot": snapshot,
            "stack_signature": stack_signature(child),
            "notes": str(evaluator_note.get("notes") or ""),
            "advisory_inputs": {
                "self_assessment": child.get("self_assessment"),
                "child_notes": str(child.get("notes") or ""),
            },
        }
        scorecards.append(scorecard)

    decisions = choose_decisions(scorecards, decision_mode=decision_mode, policy=policy)

    for scorecard in scorecards:
        run_id = str(scorecard["run_id"])
        child = children_by_run_id[run_id]
        scorecard["decision"] = decisions["decision_by_run_id"][run_id]
        scorecard["decision_reason"] = decisions["reason_by_run_id"][run_id]
        scorecard["legacy_projection"] = {
            "scorecardId": scorecard["scorecard_id"],
            "parentNodeId": scorecard["parent_node_id"],
            "childNodeId": scorecard["child_node_id"],
            "stageId": scorecard["stage_id"],
            "timestamp": scorecard["timestamp"],
            "weights": legacy_dimension_projection(scorecard["weights"]),
            "scores": legacy_dimension_projection(scorecard["scores"]),
            "composite": round(float(scorecard["composite_normalized"]), 6),
            "decision": scorecard["decision"],
            "decisionReason": scorecard["decision_reason"],
            "evidenceRefs": list(scorecard["evidence_refs"]),
            "resourceSnapshot": legacy_resource_snapshot(scorecard["resource_snapshot"]),
            "supersedes": evaluator_note_id(child),
        }

        updates, audit_records = build_declared_capability_updates(
            child=child,
            scorecard=scorecard,
            parent_node_id=parent_node_id,
            emit_stack_capabilities=bool(policy["emit_stack_capabilities"]),
        )
        runtime_capability_updates.extend(updates)
        capability_update_log.extend(audit_records)
        router_entry = build_router_entry(
            review_id=review_id,
            verdict_id=verdict_id,
            parent_node_id=parent_node_id,
            timestamp=timestamp,
            parent_score=parent_score,
            task_category=task_category,
            difficulty=difficulty,
            payload=payload,
            child=child,
            scorecard=scorecard,
        )
        if router_entry is not None:
            router_entries.append(router_entry)

    score_by_run_id = {
        str(scorecard["run_id"]): round(float(scorecard["composite_normalized"]), 6)
        for scorecard in scorecards
    }
    ordered_scorecards = sorted(scorecards, key=review_sort_key, reverse=True)
    rationale = (
        f"Parent {parent_node_id} reviewed {len(scorecards)} child runs under {decision_mode}; "
        f"winner={decisions['winner_run_id']}; retained={','.join(decisions['retained_run_ids'])}."
    )

    runtime_verdict = {
        "verdict_id": verdict_id,
        "competition_id": competition_id,
        "parent_node_id": parent_node_id,
        "score_by_run_id": score_by_run_id,
        "capability_updates": runtime_capability_updates,
        "winner_run_id": decisions["winner_run_id"],
        "rationale": rationale,
        "submitted_at": timestamp,
        "metadata": {
            "schemaVersion": SCHEMA_VERSION,
            "review_id": review_id,
            "stage_id": stage_id,
            "stage_kind": stage_kind,
            "decision_mode": decision_mode,
            "retained_run_ids": decisions["retained_run_ids"],
            "pruned_run_ids": decisions["pruned_run_ids"],
            "kept_for_diversity_run_ids": decisions["kept_for_diversity_run_ids"],
            "scorecard_ids_by_run_id": {
                str(scorecard["run_id"]): str(scorecard["scorecard_id"])
                for scorecard in ordered_scorecards
            },
            "capability_update_log": capability_update_log,
            "router_ledger_entry_ids": [entry["id"] for entry in router_entries],
        },
    }

    return {
        "schemaVersion": SCHEMA_VERSION,
        "reviewId": review_id,
        "projectId": project_id,
        "generatedAt": timestamp,
        "competitionId": competition_id,
        "stageId": stage_id,
        "stageKind": stage_kind,
        "taskCategory": task_category,
        "difficulty": difficulty,
        "parentNodeId": parent_node_id,
        "officialWriterNodeId": official_writer_node_id,
        "decisionMode": decision_mode,
        "weights": weights,
        "portfolio": {
            "winnerRunId": decisions["winner_run_id"],
            "retainedRunIds": decisions["retained_run_ids"],
            "prunedRunIds": decisions["pruned_run_ids"],
            "keptForDiversityRunIds": decisions["kept_for_diversity_run_ids"],
            "orderedRunIds": decisions["ordered_run_ids"],
        },
        "scorecards": ordered_scorecards,
        "runtime_verdict": runtime_verdict,
        "router_capability_updates": {
            "append_only": True,
            "entries": router_entries,
        },
    }


def evaluator_note_id(child: dict[str, Any]) -> str | None:
    evaluator_note = dict(child.get("evaluator_note") or {})
    supersedes = evaluator_note.get("supersedes")
    if supersedes is None:
        return None
    return str(supersedes)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Normalize parent-authored Catfish scorecards and emit runtime/router updates."
    )
    parser.add_argument("--input", type=Path, required=True, help="JSON file describing the parent review")
    parser.add_argument("--output", type=Path, help="Optional output path for the generated review artifact")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    payload = load_json(args.input)
    review = build_parent_review(payload)
    if args.output:
        write_json(args.output, review)
    else:
        print(json.dumps(review, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
