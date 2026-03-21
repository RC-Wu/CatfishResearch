import path from "node:path";
import { fileURLToPath } from "node:url";
import { ControlPlane } from "../server/controller.js";
import { ArisOps } from "../server/aris.js";
import type { Difficulty, TaskKind } from "../server/shared.js";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(scriptDir, "..");
const configPath = process.env.ARIS_CONFIG || path.join(appRoot, "config", "aris-control-center.example.json");
const controlPlane = new ControlPlane(configPath);
const arisOps = new ArisOps(appRoot, controlPlane);

function arg(name: string, fallback = "") {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] || fallback : fallback;
}

function has(name: string) {
  return process.argv.includes(name);
}

function output(value: unknown) {
  console.log(JSON.stringify(value, null, 2));
}

async function run() {
  const command = process.argv[2] || "dashboard";
  if (command === "dashboard") {
    output(arisOps.dashboard());
    return;
  }

  if (command === "snapshot") {
    output(controlPlane.snapshot(true));
    return;
  }

  if (command === "refresh-context") {
    output(controlPlane.refreshContext());
    return;
  }

  if (command === "launch") {
    const agent = controlPlane.launch({
      label: arg("--label", "Ad hoc ARIS task"),
      prompt: arg("--prompt", "Reply with a concise update."),
      taskKind: arg("--task-kind", "research") as TaskKind,
      difficulty: arg("--difficulty", "medium") as Difficulty,
      machineId: arg("--machine", "dev-intern-02"),
      projectId: arg("--project", "pua_research"),
      conversationId: arg("--conversation", "aris-control-center"),
      profileId: arg("--profile", "") || undefined,
      taskId: arg("--task-id", ""),
      taskLabel: arg("--task-label", ""),
      parentAgentId: arg("--parent-agent-id", "") || undefined,
      search: has("--search") ? true : undefined
    });
    output(agent);
    return;
  }

  if (command === "route-preview") {
    output(
      controlPlane.previewRoute({
        label: arg("--label", "Ad hoc ARIS task"),
        prompt: arg("--prompt", ""),
        taskKind: arg("--task-kind", "research") as TaskKind,
        difficulty: arg("--difficulty", "medium") as Difficulty,
        machineId: arg("--machine", "dev-intern-02"),
        projectId: arg("--project", "pua_research"),
        conversationId: arg("--conversation", "aris-control-center"),
        profileId: arg("--profile", "") || undefined,
        taskId: arg("--task-id", ""),
        taskLabel: arg("--task-label", ""),
        parentAgentId: arg("--parent-agent-id", "") || undefined,
        search: has("--search") ? true : undefined
      })
    );
    return;
  }

  if (command === "tmux") {
    output(
      arisOps.createTmuxInstance({
        label: arg("--label", "ARIS Main"),
        machineId: arg("--machine", "dev-intern-02"),
        workspaceRoot: arg("--workspace", "") || undefined,
        entryCommand: arg("--command", "") || undefined,
        start: has("--start")
      })
    );
    return;
  }

  if (command === "reflect") {
    output(
      arisOps.recordReflection({
        title: arg("--title", "ARIS Reflection"),
        projectId: arg("--project", "") || undefined,
        scope: arg("--scope", "cross-project") as "project" | "cross-project",
        observation: arg("--observation", "Observation pending."),
        lesson: arg("--lesson", "Lesson pending."),
        upgradeProposal: arg("--upgrade", "Upgrade proposal pending.")
      })
    );
    return;
  }

  if (command === "deep-research-plan") {
    output(
      arisOps.generateDeepResearchPlan({
        topic: arg("--topic", "open research topic"),
        agentCount: Number(arg("--agents", "72")),
        machineId: arg("--machine", "dev-intern-02"),
        taskKind: arg("--task-kind", "research") as TaskKind,
        difficulty: arg("--difficulty", "high") as Difficulty
      })
    );
    return;
  }

  throw new Error(`Unknown command: ${command}`);
}

run().catch((error) => {
  console.error(String(error));
  process.exit(1);
});
