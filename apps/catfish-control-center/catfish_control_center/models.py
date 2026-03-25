from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def _str_list(value: Any) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(str(item) for item in value)


def _float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    return float(value)


def _int(value: Any, default: int = 0) -> int:
    if value in (None, ""):
        return default
    return int(value)


@dataclass(frozen=True)
class ProjectState:
    project_id: str
    label: str
    status: str
    active_branch: str
    owner: str = ""
    active_agents: int = 0
    pending_reviews: int = 0
    last_event_at: str = ""
    summary: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectState":
        return cls(
            project_id=str(data["project_id"]),
            label=str(data.get("label", data["project_id"])),
            status=str(data.get("status", "unknown")),
            active_branch=str(data.get("active_branch", "")),
            owner=str(data.get("owner", "")),
            active_agents=_int(data.get("active_agents")),
            pending_reviews=_int(data.get("pending_reviews")),
            last_event_at=str(data.get("last_event_at", "")),
            summary=str(data.get("summary", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AgentNode:
    agent_id: str
    label: str
    role: str
    status: str
    project_id: str
    provider_profile: str
    task_kind: str
    branch: str = ""
    parent_id: str = ""
    machine_id: str = ""
    summary: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentNode":
        return cls(
            agent_id=str(data["agent_id"]),
            label=str(data.get("label", data["agent_id"])),
            role=str(data.get("role", "worker")),
            status=str(data.get("status", "unknown")),
            project_id=str(data.get("project_id", "")),
            provider_profile=str(data.get("provider_profile", "")),
            task_kind=str(data.get("task_kind", "builder")),
            branch=str(data.get("branch", "")),
            parent_id=str(data.get("parent_id", "")),
            machine_id=str(data.get("machine_id", "")),
            summary=str(data.get("summary", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProviderState:
    profile_id: str
    label: str
    machine_ids: tuple[str, ...]
    available: bool
    verified: bool
    remaining_credit: float
    reserve_floor: float
    routing_weight: float = 1.0
    issues: tuple[str, ...] = field(default_factory=tuple)
    route_tiers: dict[str, Any] = field(default_factory=dict)
    selected: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProviderState":
        return cls(
            profile_id=str(data["profile_id"]),
            label=str(data.get("label", data["profile_id"])),
            machine_ids=_str_list(data.get("machine_ids")),
            available=bool(data.get("available", True)),
            verified=bool(data.get("verified", True)),
            remaining_credit=_float(data.get("remaining_credit")),
            reserve_floor=_float(data.get("reserve_floor")),
            routing_weight=_float(data.get("routing_weight"), default=1.0),
            issues=_str_list(data.get("issues")),
            route_tiers=dict(data.get("route_tiers", {})),
            selected=bool(data.get("selected", False)),
        )

    @property
    def health_summary(self) -> str:
        if not self.available:
            return "offline"
        if not self.verified:
            return "unverified"
        return "healthy"

    @property
    def quota_summary(self) -> str:
        delta = self.remaining_credit - self.reserve_floor
        if delta <= 0:
            return f"below reserve by {abs(delta):.2f}"
        return f"{delta:.2f} above reserve"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["machine_ids"] = list(self.machine_ids)
        payload["issues"] = list(self.issues)
        return payload


@dataclass(frozen=True)
class BranchScore:
    branch: str
    project_id: str
    score: float
    wins: int
    losses: int
    state: str
    head_commit: str = ""
    summary: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BranchScore":
        return cls(
            branch=str(data["branch"]),
            project_id=str(data.get("project_id", "")),
            score=_float(data.get("score")),
            wins=_int(data.get("wins")),
            losses=_int(data.get("losses")),
            state=str(data.get("state", "unknown")),
            head_commit=str(data.get("head_commit", "")),
            summary=str(data.get("summary", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ControlEvent:
    event_id: str
    timestamp: str
    level: str
    kind: str
    message: str
    project_id: str = ""
    agent_id: str = ""
    branch: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ControlEvent":
        return cls(
            event_id=str(data["event_id"]),
            timestamp=str(data.get("timestamp", "")),
            level=str(data.get("level", "info")),
            kind=str(data.get("kind", "event")),
            message=str(data.get("message", "")),
            project_id=str(data.get("project_id", "")),
            agent_id=str(data.get("agent_id", "")),
            branch=str(data.get("branch", "")),
            payload=dict(data.get("payload", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ControlSnapshot:
    generated_at: str
    projects: tuple[ProjectState, ...]
    agents: tuple[AgentNode, ...]
    providers: tuple[ProviderState, ...]
    branches: tuple[BranchScore, ...]
    events: tuple[ControlEvent, ...]
    route_preview: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ControlSnapshot":
        return cls(
            generated_at=str(data.get("generated_at", "")),
            projects=tuple(ProjectState.from_dict(item) for item in data.get("projects", [])),
            agents=tuple(AgentNode.from_dict(item) for item in data.get("agents", [])),
            providers=tuple(ProviderState.from_dict(item) for item in data.get("providers", [])),
            branches=tuple(BranchScore.from_dict(item) for item in data.get("branches", [])),
            events=tuple(ControlEvent.from_dict(item) for item in data.get("events", [])),
            route_preview=dict(data["route_preview"]) if data.get("route_preview") else None,
            metadata=dict(data.get("metadata", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "projects": [item.to_dict() for item in self.projects],
            "agents": [item.to_dict() for item in self.agents],
            "providers": [item.to_dict() for item in self.providers],
            "branches": [item.to_dict() for item in self.branches],
            "events": [item.to_dict() for item in self.events],
            "route_preview": self.route_preview,
            "metadata": self.metadata,
        }
