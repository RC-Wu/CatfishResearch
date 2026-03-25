from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from catfish_control_center.dashboard import render_dashboard
from catfish_control_center.models import ControlEvent
from catfish_control_center.runtime import apply_route_preview, load_snapshot
from catfish_control_center.storage import InMemoryEventStore, JsonLinesEventStore, JsonSnapshotStore


class ControlCenterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot_path = APP_ROOT / "examples" / "sample_snapshot.json"
        self.route_config_path = Path(__file__).resolve().parents[3] / "tools" / "examples" / "control_plane.example.json"

    def test_dashboard_renders_route_preview_and_sections(self) -> None:
        snapshot = load_snapshot(self.snapshot_path)
        snapshot = apply_route_preview(
            snapshot,
            config_path=self.route_config_path,
            machine_id="dev-intern-02",
            task_kind="builder",
            difficulty="high",
        )

        rendered = render_dashboard(snapshot)
        self.assertIn("Catfish Control Center Snapshot", rendered)
        self.assertIn("Multi-Project Overview", rendered)
        self.assertIn("Agent Graph / Hierarchy", rendered)
        self.assertIn("Provider Health / Quota", rendered)
        self.assertIn("Branch Scoreboards", rendered)
        self.assertIn("Route Preview", rendered)
        self.assertIn("Current Session (current-session) SELECTED", rendered)
        self.assertIn("tier=deep", rendered)

    def test_snapshot_store_round_trip(self) -> None:
        snapshot = load_snapshot(self.snapshot_path)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshot.json"
            store = JsonSnapshotStore(path)
            store.save(snapshot)
            reloaded = store.load()

        self.assertEqual(reloaded.generated_at, snapshot.generated_at)
        self.assertEqual(len(reloaded.projects), 2)
        self.assertEqual(reloaded.projects[0].project_id, "catfish-core")

    def test_json_lines_event_store_appends_and_reads_recent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "events.jsonl"
            store = JsonLinesEventStore(path)
            store.append(
                ControlEvent(
                    event_id="evt-1",
                    timestamp="2026-03-25T10:00:00Z",
                    level="info",
                    kind="heartbeat",
                    message="first",
                )
            )
            store.append(
                ControlEvent(
                    event_id="evt-2",
                    timestamp="2026-03-25T10:05:00Z",
                    level="warning",
                    kind="quota",
                    message="second",
                )
            )

            recent = store.list_recent(limit=1)

        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0].event_id, "evt-2")

    def test_in_memory_event_store(self) -> None:
        store = InMemoryEventStore()
        store.append(
            ControlEvent(
                event_id="evt-memory",
                timestamp="2026-03-25T10:30:00Z",
                level="info",
                kind="memory",
                message="ok",
            )
        )
        payload = [event.to_dict() for event in store.list_recent()]
        self.assertEqual(payload, [json.loads(json.dumps(payload[0]))])


if __name__ == "__main__":
    unittest.main()
