from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = REPO_ROOT / "apps" / "catfish-control-center"
TOOLS_ROOT = REPO_ROOT / "tools"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.catfish_production_smoke import build_smoke_report, materialize_smoke_state_root, verify_smoke_report


class CircleEditingProductionSmokeTest(unittest.TestCase):
    def test_materialized_smoke_state_root_verifies(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir) / "circleediting-smoke-state-root"
            materialize_smoke_state_root(dest)
            self.assertTrue((dest / "projects" / "circleediting-3d-edit" / "runtime_snapshot.json").exists())

            report = build_smoke_report(dest)
            verify_smoke_report(report)

            self.assertEqual(report["project_label"], "CircleEditing 3d Edit")
            self.assertEqual(report["resource_manager_id"], "circle3d-resource-manager")
            self.assertEqual(report["guardrail_overall_status"], "ok")
            self.assertEqual(report["supervisor_overall_status"], "healthy")
            self.assertGreaterEqual(report["agentdoc_receipts"], 5)
            self.assertGreaterEqual(report["resource_requests"], 3)

    def test_control_center_renders_the_smoke_state_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir) / "circleediting-smoke-state-root"
            materialize_smoke_state_root(dest)

            command = [
                sys.executable,
                str(APP_ROOT / "main.py"),
                "--state-root",
                str(dest),
                "--view",
                "dashboard",
                "--format",
                "json",
            ]
            result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
            payload = json.loads(result.stdout)

            self.assertIn("CircleEditing", result.stdout)
            self.assertIn("Circle3D Root Supervisor", result.stdout)
            self.assertTrue(any(item["project_id"] == "circleediting-3d-edit" for item in payload["projects"]))
            self.assertEqual(payload["guardrail_state"]["overall_status"], "ok")
            self.assertEqual(payload["supervisor_state"]["overall_status"], "healthy")


if __name__ == "__main__":
    unittest.main()
