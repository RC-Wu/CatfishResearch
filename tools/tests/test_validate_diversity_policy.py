from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "tools" / "validate_diversity_policy.py"
SPEC = importlib.util.spec_from_file_location("validate_diversity_policy", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ValidateDiversityPolicyTest(unittest.TestCase):
    def load_example_policy(self) -> dict:
        with MODULE.DEFAULT_POLICY_PATH.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def test_example_policy_validates(self) -> None:
        payload = self.load_example_policy()
        self.assertEqual(MODULE.validate_payload(payload), [])

    def test_missing_stage_is_reported(self) -> None:
        payload = self.load_example_policy()
        payload = json.loads(json.dumps(payload))
        payload["stages"].pop("figures")

        errors = MODULE.validate_payload(payload)

        self.assertTrue(any("missing required stages: figures" in error for error in errors))

    def test_axis_floor_guard_is_reported(self) -> None:
        payload = self.load_example_policy()
        payload = json.loads(json.dumps(payload))
        payload["stages"]["idea"]["explorationPolicy"]["axisCoverage"]["provider"]["targetDistinct"] = 1
        payload["stages"]["idea"]["explorationPolicy"]["axisCoverage"]["provider"]["minDistinct"] = 2

        errors = MODULE.validate_payload(payload)

        self.assertTrue(
            any(
                "idea.explorationPolicy.axisCoverage.provider.targetDistinct must be >= minDistinct" in error
                for error in errors
            )
        )

    def test_cli_returns_zero_for_example_policy(self) -> None:
        payload = self.load_example_policy()
        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "policy.json"
            policy_path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(MODULE.main([str(policy_path)]), 0)


if __name__ == "__main__":
    unittest.main()
