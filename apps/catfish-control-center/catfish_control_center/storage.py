from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from .models import ControlEvent, ControlSnapshot


class SnapshotStore(Protocol):
    def load(self) -> ControlSnapshot:
        ...

    def save(self, snapshot: ControlSnapshot) -> None:
        ...


class EventStore(Protocol):
    def append(self, event: ControlEvent) -> None:
        ...

    def list_recent(self, limit: int = 20) -> list[ControlEvent]:
        ...


class JsonSnapshotStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> ControlSnapshot:
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return ControlSnapshot.from_dict(payload)

    def save(self, snapshot: ControlSnapshot) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(snapshot.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


class JsonLinesEventStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def append(self, event: ControlEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")

    def list_recent(self, limit: int = 20) -> list[ControlEvent]:
        if not self.path.exists():
            return []
        lines = [line for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
        payloads = [json.loads(line) for line in lines[-limit:]]
        return [ControlEvent.from_dict(payload) for payload in payloads]


class InMemoryEventStore:
    def __init__(self, events: list[ControlEvent] | None = None) -> None:
        self._events = list(events or [])

    def append(self, event: ControlEvent) -> None:
        self._events.append(event)

    def list_recent(self, limit: int = 20) -> list[ControlEvent]:
        return list(self._events[-limit:])
