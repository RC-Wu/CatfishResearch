from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
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


GRAPH_MODULE = load_module("catfish_project_graph", TOOLS_DIR / "catfish_project_graph.py")
SCHEDULER_MODULE = load_module("catfish_scheduler", TOOLS_DIR / "catfish_scheduler.py")


class CatfishSchedulerTest(unittest.TestCase):
    def build_graph(self):
        runtime_snapshot = {
            "projects": {
                "proj-scheduler": {
                    "project": {
                        "project_id": "proj-scheduler",
                        "title": "Scheduler Engine",
                        "objective": "Keep competition and diversity alive across all stages.",
                        "resource_budget": {
                            "token_budget": 30000,
                            "usd_budget": 12.0,
                            "wall_time_budget_s": 7200,
                            "max_parallel_children": 3,
                        },
                    },
                    "root_node_ids": ["root-parent"],
                }
            }
        }
        return GRAPH_MODULE.build_project_graph_from_runtime_snapshot(
            runtime_snapshot,
            project_id="proj-scheduler",
            graph_id="proj-scheduler.graph",
            machine_id="dev-intern-02",
        )

    def test_default_stage_plan_is_competitive_everywhere(self) -> None:
        graph = self.build_graph()
        self.assertEqual(graph.stage_order, list(GRAPH_MODULE.STANDARD_STAGE_ORDER))
        for stage_id in graph.stage_order:
            stage = graph.stages[stage_id]
            self.assertGreaterEqual(stage.min_competitors, 2)
            self.assertGreaterEqual(stage.target_frontier_width, stage.min_competitors)
            self.assertEqual(stage.competition_mode, "top-k")
            self.assertGreaterEqual(stage.diversity_targets.model_min_distinct, 2)
            self.assertGreaterEqual(stage.diversity_targets.agent_group_min_distinct, 2)
            self.assertGreaterEqual(stage.diversity_targets.style_min_distinct, 2)

    def test_scheduler_prefers_expand_for_diversity_before_deepen(self) -> None:
        graph = self.build_graph()
        stage = graph.stages["implementation"]
        branch = GRAPH_MODULE.Branch(
            branch_id="implementation-branch-1",
            stage_id="implementation",
            label="impl dominant",
            status="running",
            provider_id="ucloud-modelverse",
            model="gpt-5.4",
            tier_id="balanced",
            reasoning_effort="high",
            agent_group="builder-pair",
            style="minimal-diff",
            prior=0.72,
            visits=3,
            parent_scores=[0.84],
            projected_tokens=1000,
            projected_cost_usd=0.3,
            projected_wall_time_s=120.0,
        )
        graph.branches[branch.branch_id] = branch
        stage.branch_ids.append(branch.branch_id)

        scheduler = SCHEDULER_MODULE.CatfishScheduler()
        proposal = scheduler.recommend_next_action(graph)

        self.assertEqual(proposal.action, "expand")
        self.assertEqual(proposal.stage_id, "implementation")
        self.assertEqual(proposal.route["provider_id"], "ucloud-modelverse")
        self.assertNotEqual(proposal.route["agent_group"], "builder-pair")
        self.assertNotEqual(proposal.route["style"], "minimal-diff")
        self.assertIn("Expand implementation frontier", proposal.reason)

    def test_review_is_scheduled_for_parent_only_scoring(self) -> None:
        graph = self.build_graph()
        stage = graph.stages["evaluation"]
        branch = GRAPH_MODULE.Branch(
            branch_id="evaluation-branch-1",
            stage_id="evaluation",
            label="needs review",
            status="completed",
            provider_id="ucloud-modelverse",
            model="gpt-5.4",
            tier_id="balanced",
            reasoning_effort="high",
            agent_group="benchmark-panel",
            style="coverage-first",
            prior=0.66,
            visits=1,
        )
        graph.branches[branch.branch_id] = branch
        stage.branch_ids.append(branch.branch_id)

        scheduler = SCHEDULER_MODULE.CatfishScheduler()
        proposal = scheduler.recommend_next_action(graph)

        self.assertEqual(proposal.action, "review")
        self.assertEqual(proposal.branch_id, "evaluation-branch-1")
        self.assertIn("Parent-only scoring gate", proposal.reason)

    def test_prune_beats_further_investment_for_low_scored_branch(self) -> None:
        graph = self.build_graph()
        stage = graph.stages["writing"]
        branch = GRAPH_MODULE.Branch(
            branch_id="writing-branch-1",
            stage_id="writing",
            label="weak writer",
            status="running",
            provider_id="ucloud-modelverse",
            model="gpt-5.4",
            tier_id="balanced",
            reasoning_effort="high",
            agent_group="drafting-pair",
            style="narrative",
            prior=0.4,
            visits=2,
            parent_scores=[0.12],
            failure_count=2,
            projected_tokens=2400,
            projected_cost_usd=0.95,
            projected_wall_time_s=500.0,
        )
        graph.branches[branch.branch_id] = branch
        stage.branch_ids.append(branch.branch_id)

        scheduler = SCHEDULER_MODULE.CatfishScheduler()
        proposal = scheduler.recommend_next_action(graph)

        self.assertEqual(proposal.action, "prune")
        self.assertEqual(proposal.branch_id, "writing-branch-1")
        self.assertIn("Prune writing-branch-1", proposal.reason)

    def test_cli_bootstrap_and_apply_round_trip(self) -> None:
        scheduler = SCHEDULER_MODULE.CatfishScheduler()
        operations = [
            {
                "op": "register_project",
                "project": {
                    "project_id": "proj-cli",
                    "title": "CLI Scheduler",
                    "resource_budget": {
                        "token_budget": 20000,
                        "usd_budget": 8.0,
                        "wall_time_budget_s": 3600,
                        "max_parallel_children": 2,
                    },
                },
            },
            {
                "op": "upsert_agent_node",
                "project_id": "proj-cli",
                "node": {
                    "node_id": "root-parent",
                    "role": "supervisor",
                    "label": "Root Parent",
                },
            },
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            ops_path = tmp_path / "ops.json"
            graph_path = tmp_path / "graph.json"
            ops_path.write_text(json.dumps(operations), encoding="utf-8")

            with io.StringIO() as buffer, redirect_stdout(buffer):
                exit_code = SCHEDULER_MODULE.main(
                    [
                        "bootstrap",
                        "--ops",
                        str(ops_path),
                        "--project-id",
                        "proj-cli",
                        "--graph-out",
                        str(graph_path),
                    ]
                )
            self.assertEqual(exit_code, 0)
            graph = GRAPH_MODULE.load_project_graph(graph_path)
            self.assertEqual(graph.project_id, "proj-cli")

            proposal = scheduler.recommend_next_action(graph)
            self.assertEqual(proposal.action, "expand")
            scheduler.apply_action(graph, proposal)
            GRAPH_MODULE.save_project_graph(graph_path, graph)

            reloaded = GRAPH_MODULE.load_project_graph(graph_path)
            self.assertEqual(len(reloaded.action_log), 1)
            self.assertEqual(len(reloaded.stages["idea"].branch_ids), 1)
            schema_snapshot = GRAPH_MODULE.build_schema_snapshot(reloaded)
            self.assertEqual(schema_snapshot["graphId"], "proj-cli.scheduler")


if __name__ == "__main__":
    unittest.main()
