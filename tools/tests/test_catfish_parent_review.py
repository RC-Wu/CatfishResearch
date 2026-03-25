from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PARENT_REVIEW = load_module("catfish_parent_review", TOOLS_DIR / "catfish_parent_review.py")
CAPABILITY_APPLY = load_module("catfish_capability_apply", TOOLS_DIR / "catfish_capability_apply.py")
CATFISH_RUNTIME = load_module("catfish_runtime_for_parent_review_tests", TOOLS_DIR / "catfish_runtime.py")


class CatfishParentReviewTest(unittest.TestCase):
    def build_runtime(self) -> object:
        runtime = CATFISH_RUNTIME.CatfishRuntime()
        runtime.register_project(
            {
                "project_id": "proj-parent-review",
                "title": "Parent Review Integration",
            }
        )
        runtime.upsert_agent_node(
            "proj-parent-review",
            {
                "node_id": "parent-root",
                "role": "supervisor",
                "label": "Parent Root",
            },
        )
        runtime.upsert_agent_node(
            "proj-parent-review",
            {
                "node_id": "child-a",
                "role": "builder",
                "label": "Child A",
                "parent_node_id": "parent-root",
            },
        )
        runtime.upsert_agent_node(
            "proj-parent-review",
            {
                "node_id": "child-b",
                "role": "critic",
                "label": "Child B",
                "parent_node_id": "parent-root",
            },
        )
        runtime.upsert_agent_node(
            "proj-parent-review",
            {
                "node_id": "child-c",
                "role": "explorer",
                "label": "Child C",
                "parent_node_id": "parent-root",
            },
        )
        runtime.define_competition(
            "proj-parent-review",
            {
                "competition_id": "comp-parent-review",
                "parent_node_id": "parent-root",
                "candidate_node_ids": ["child-a", "child-b", "child-c"],
            },
        )
        return runtime

    def build_winner_pick_payload(self) -> dict[str, object]:
        return {
            "review_id": "parent-review-winner",
            "project_id": "proj-parent-review",
            "competition_id": "comp-parent-review",
            "stage_id": "implementation",
            "stage_kind": "implementation",
            "task_category": "builder",
            "difficulty": "high",
            "decision_mode": "winner_pick",
            "parent_node_id": "parent-root",
            "official_writer_node_id": "parent-root",
            "parent_score": 0.82,
            "timestamp": "2026-03-25T12:00:00Z",
            "children": [
                {
                    "run_id": "run-a1",
                    "node_id": "child-a",
                    "metadata": {"agent_group": "builder+critic"},
                    "provider_assignment": {
                        "provider": "ucloud-modelverse",
                        "model": "gpt-5.4",
                        "reasoning_effort": "high",
                        "metadata": {"routing_tier": "deep"},
                    },
                    "resource_usage": {
                        "prompt_tokens": 2400,
                        "completion_tokens": 900,
                        "cost_usd": 2.2,
                        "wall_time_s": 205,
                    },
                    "self_assessment": {"composite": 0.97},
                    "evaluator_note": {
                        "author_node_id": "parent-root",
                        "dimension_scores": {
                            "idea": 0.76,
                            "model": 0.86,
                            "provider": 0.82,
                            "agent_group": 0.84,
                            "diversity_contribution": 0.55,
                            "resource_usage": 0.72,
                            "outcome_quality": 0.93,
                            "risk": 0.18,
                        },
                        "confidence": 0.92,
                        "evidence_refs": ["artifacts/run-a1.patch", "logs/run-a1.txt"],
                        "capabilities": [
                            {
                                "capability": "coding",
                                "score": 0.93,
                                "summary": "Parent verified the strongest patch quality.",
                            }
                        ],
                    },
                },
                {
                    "run_id": "run-b1",
                    "node_id": "child-b",
                    "metadata": {"agent_group": "critic-only"},
                    "provider_assignment": {
                        "provider": "anthropic",
                        "model": "claude-sonnet",
                        "reasoning_effort": "medium",
                    },
                    "resource_usage": {
                        "prompt_tokens": 1800,
                        "completion_tokens": 500,
                        "cost_usd": 1.6,
                        "wall_time_s": 160,
                    },
                    "evaluator_note": {
                        "author_node_id": "parent-root",
                        "dimension_scores": {
                            "idea": 0.45,
                            "model": 0.74,
                            "provider": 0.70,
                            "agent_group": 0.69,
                            "diversity_contribution": 0.42,
                            "resource_usage": 0.78,
                            "outcome_quality": 0.70,
                            "risk": 0.28,
                        },
                        "confidence": 0.88,
                        "decision_hint": "replay",
                        "evidence_refs": ["reviews/run-b1.md"],
                        "capabilities": [
                            {
                                "capability": "critique",
                                "score": 0.74,
                                "summary": "Good review depth, weaker direct patch execution.",
                            }
                        ],
                    },
                },
            ],
        }

    def build_portfolio_payload(self) -> dict[str, object]:
        return {
            "review_id": "parent-review-portfolio",
            "project_id": "proj-parent-review",
            "competition_id": "comp-parent-review",
            "stage_id": "ideation",
            "stage_kind": "ideation",
            "task_category": "research",
            "difficulty": "high",
            "decision_mode": "portfolio_keep",
            "parent_node_id": "parent-root",
            "official_writer_node_id": "parent-root",
            "parent_score": 0.88,
            "timestamp": "2026-03-25T13:00:00Z",
            "portfolio_policy": {
                "max_survivors": 2,
                "diversity_floor": 0.80,
                "max_score_gap": 0.08,
            },
            "children": [
                {
                    "run_id": "run-a2",
                    "node_id": "child-a",
                    "metadata": {"agent_group": "builder+critic"},
                    "provider_assignment": {
                        "provider": "ucloud-modelverse",
                        "model": "gpt-5.4",
                        "reasoning_effort": "high",
                        "metadata": {"routing_tier": "deep"},
                    },
                    "resource_usage": {
                        "prompt_tokens": 3000,
                        "completion_tokens": 1000,
                        "cost_usd": 2.8,
                        "wall_time_s": 240,
                    },
                    "evaluator_note": {
                        "author_node_id": "parent-root",
                        "dimension_scores": {
                            "idea": 0.86,
                            "model": 0.84,
                            "provider": 0.82,
                            "agent_group": 0.80,
                            "diversity_contribution": 0.40,
                            "resource_usage": 0.65,
                            "outcome_quality": 0.88,
                            "risk": 0.20,
                        },
                        "confidence": 0.90,
                        "evidence_refs": ["ideas/run-a2.md"],
                    },
                },
                {
                    "run_id": "run-b2",
                    "node_id": "child-b",
                    "metadata": {"agent_group": "explorer+critic"},
                    "provider_assignment": {
                        "provider": "anthropic",
                        "model": "claude-sonnet",
                        "reasoning_effort": "medium",
                    },
                    "resource_usage": {
                        "prompt_tokens": 2600,
                        "completion_tokens": 900,
                        "cost_usd": 2.1,
                        "wall_time_s": 210,
                    },
                    "evaluator_note": {
                        "author_node_id": "parent-root",
                        "dimension_scores": {
                            "idea": 0.75,
                            "model": 0.68,
                            "provider": 0.62,
                            "agent_group": 0.70,
                            "diversity_contribution": 0.95,
                            "resource_usage": 0.55,
                            "outcome_quality": 0.75,
                            "risk": 0.35,
                        },
                        "confidence": 0.91,
                        "evidence_refs": ["ideas/run-b2.md"],
                    },
                },
                {
                    "run_id": "run-c2",
                    "node_id": "child-c",
                    "metadata": {"agent_group": "critic-only"},
                    "provider_assignment": {
                        "provider": "openrouter",
                        "model": "qwen-plus",
                        "reasoning_effort": "medium",
                    },
                    "resource_usage": {
                        "prompt_tokens": 2200,
                        "completion_tokens": 700,
                        "cost_usd": 1.4,
                        "wall_time_s": 190,
                    },
                    "evaluator_note": {
                        "author_node_id": "parent-root",
                        "dimension_scores": {
                            "idea": 0.54,
                            "model": 0.58,
                            "provider": 0.52,
                            "agent_group": 0.60,
                            "diversity_contribution": 0.35,
                            "resource_usage": 0.82,
                            "outcome_quality": 0.57,
                            "risk": 0.48,
                        },
                        "confidence": 0.84,
                        "evidence_refs": ["ideas/run-c2.md"],
                    },
                },
            ],
        }

    def test_winner_pick_emits_runtime_compatible_verdict(self) -> None:
        review = PARENT_REVIEW.build_parent_review(self.build_winner_pick_payload())

        self.assertEqual(review["parentNodeId"], "parent-root")
        self.assertEqual(review["portfolio"]["winnerRunId"], "run-a1")
        self.assertEqual(review["scorecards"][0]["decision"], "selected")
        self.assertEqual(review["scorecards"][1]["decision"], "replay")
        self.assertIn("diversity_contribution", review["scorecards"][0]["scores"])
        self.assertNotIn("diversityContribution", review["scorecards"][0]["legacy_projection"]["scores"])
        self.assertEqual(review["runtime_verdict"]["winner_run_id"], "run-a1")
        self.assertGreater(len(review["runtime_verdict"]["capability_updates"]), 2)

        runtime = self.build_runtime()
        runtime.record_candidate_run(
            "proj-parent-review",
            {
                "run_id": "run-a1",
                "competition_id": "comp-parent-review",
                "node_id": "child-a",
                "submitted_at": "2026-03-25T11:58:00Z",
            },
        )
        runtime.record_candidate_run(
            "proj-parent-review",
            {
                "run_id": "run-b1",
                "competition_id": "comp-parent-review",
                "node_id": "child-b",
                "submitted_at": "2026-03-25T11:59:00Z",
            },
        )
        runtime.apply_parent_verdict("proj-parent-review", review["runtime_verdict"])
        snapshot = runtime.snapshot(project_id="proj-parent-review")

        self.assertEqual(
            snapshot["projects"]["proj-parent-review"]["competitions"]["comp-parent-review"]["winner_run_id"],
            "run-a1",
        )
        self.assertAlmostEqual(
            snapshot["projects"]["proj-parent-review"]["runs"]["run-a1"]["parent_score"],
            review["runtime_verdict"]["score_by_run_id"]["run-a1"],
        )
        self.assertIn(
            "coding",
            snapshot["projects"]["proj-parent-review"]["nodes"]["child-a"]["capability_summaries"],
        )

    def test_portfolio_keep_retains_diverse_secondary_candidate(self) -> None:
        review = PARENT_REVIEW.build_parent_review(self.build_portfolio_payload())

        self.assertEqual(review["portfolio"]["winnerRunId"], "run-a2")
        self.assertEqual(review["portfolio"]["retainedRunIds"], ["run-a2", "run-b2"])
        self.assertEqual(review["portfolio"]["keptForDiversityRunIds"], ["run-b2"])
        decisions = {scorecard["run_id"]: scorecard["decision"] for scorecard in review["scorecards"]}
        self.assertEqual(decisions["run-b2"], "survive")
        self.assertEqual(decisions["run-c2"], "pruned")
        self.assertIn(
            "preserves stack diversity",
            next(scorecard for scorecard in review["scorecards"] if scorecard["run_id"] == "run-b2")[
                "decision_reason"
            ],
        )
        self.assertEqual(
            review["runtime_verdict"]["metadata"]["retained_run_ids"],
            ["run-a2", "run-b2"],
        )

    def test_rejects_non_parent_official_writer(self) -> None:
        payload = self.build_winner_pick_payload()
        payload["official_writer_node_id"] = "child-a"
        with self.assertRaisesRegex(ValueError, "competition parent"):
            PARENT_REVIEW.build_parent_review(payload)

        payload = self.build_winner_pick_payload()
        payload["children"][0]["evaluator_note"]["author_node_id"] = "child-a"
        with self.assertRaisesRegex(ValueError, "must be authored by parent"):
            PARENT_REVIEW.build_parent_review(payload)

    def test_capability_apply_appends_incrementally(self) -> None:
        review = PARENT_REVIEW.build_parent_review(self.build_portfolio_payload())
        ledger = {
            "schemaVersion": "catfish.capability-ledger.v1",
            "updatedAt": "2026-03-24T00:00:00Z",
            "entries": [
                {
                    "id": "baseline-entry",
                    "providerId": "ucloud-modelverse",
                    "taskCategory": "research",
                    "difficulty": "medium",
                    "reasoningTier": "balanced",
                    "reasoningLength": "medium",
                    "parentScore": 0.50,
                    "recency": "2026-03-24",
                    "confidence": 0.80,
                    "routingEffect": "neutral",
                    "scoreDelta": 0.00,
                    "notes": "Existing baseline memory.",
                }
            ],
        }
        operations_payload = {
            "operations": [
                {
                    "op": "register_project",
                    "project": {
                        "project_id": "proj-parent-review",
                        "title": "Parent Review Integration",
                    },
                }
            ]
        }

        applied = CAPABILITY_APPLY.apply_review_output(
            review,
            ledger=copy.deepcopy(ledger),
            operations_payload=copy.deepcopy(operations_payload),
            project_id="proj-parent-review",
            applied_at="2026-03-25T14:00:00Z",
        )

        added_entry_ids = applied["router"]["addedEntryIds"]
        self.assertEqual(len(added_entry_ids), len(review["router_capability_updates"]["entries"]))
        self.assertEqual(applied["router"]["ledger"]["entries"][0]["id"], "baseline-entry")
        self.assertEqual(applied["router"]["ledger"]["auditLog"][0]["reviewId"], review["reviewId"])
        self.assertTrue(applied["runtime"]["operationAdded"])
        self.assertEqual(
            applied["runtime"]["operations"]["operations"][-1]["op"],
            "apply_parent_verdict",
        )
        self.assertEqual(
            applied["runtime"]["operations"]["operations"][-1]["verdict"]["winner_run_id"],
            review["portfolio"]["winnerRunId"],
        )

        updated_ledger, audit_record = CAPABILITY_APPLY.append_router_entries(
            applied["router"]["ledger"],
            review["router_capability_updates"]["entries"],
            review_id=review["reviewId"],
            applied_at="2026-03-25T14:05:00Z",
        )
        self.assertEqual(audit_record["addedEntryIds"], [])
        self.assertEqual(
            sorted(audit_record["skippedEntryIds"]),
            sorted(entry["id"] for entry in review["router_capability_updates"]["entries"]),
        )
        self.assertEqual(len(updated_ledger["entries"]), len(applied["router"]["ledger"]["entries"]))


if __name__ == "__main__":
    unittest.main()
