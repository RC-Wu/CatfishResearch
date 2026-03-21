import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { ControlPlane } from "./controller.js";
import type { ControlPlaneConfig, Difficulty, MachineConfig, TaskKind } from "./shared.js";
import { makeId, nowIso, runtimePath, slugify } from "./shared.js";

interface TmuxInstanceRequest {
  label: string;
  machineId: string;
  workspaceRoot?: string;
  entryCommand?: string;
  start?: boolean;
}

interface ReflectionRequest {
  title: string;
  projectId?: string;
  scope: "project" | "cross-project";
  observation: string;
  lesson: string;
  upgradeProposal: string;
}

interface DeepResearchRequest {
  topic: string;
  agentCount?: number;
  machineId?: string;
  taskKind?: TaskKind;
  difficulty?: Difficulty;
}

export class ArisOps {
  readonly config: ControlPlaneConfig;
  readonly runtimeRoot: string;
  readonly knowledgeRoot: string;
  readonly reflectionRoot: string;
  readonly proposalRoot: string;
  readonly tmuxRoot: string;
  readonly researchRoot: string;

  constructor(
    readonly appRoot: string,
    readonly controlPlane: ControlPlane
  ) {
    this.config = controlPlane.config;
    this.runtimeRoot = runtimePath(this.config.runtimeRoot, "aris");
    this.knowledgeRoot = runtimePath(this.runtimeRoot, "knowledge");
    this.reflectionRoot = runtimePath(this.runtimeRoot, "reflections");
    this.proposalRoot = runtimePath(this.runtimeRoot, "upgrade-proposals");
    this.tmuxRoot = runtimePath(this.runtimeRoot, "tmux");
    this.researchRoot = runtimePath(this.runtimeRoot, "deep-research");
    this.ensureScaffold();
  }

  dashboard() {
    const snapshot = this.controlPlane.snapshot(true);
    return {
      generatedAt: nowIso(),
      label: this.config.aris?.dashboardLabel ?? "ARIS Control Center",
      snapshot,
      tmuxInstances: this.listJsonDirectory(this.tmuxRoot),
      reflections: this.listMarkdownDirectory(this.reflectionRoot, 12),
      proposals: this.listMarkdownDirectory(this.proposalRoot, 12),
      researchPlans: this.listJsonDirectory(this.researchRoot).slice(0, 8),
      routeMatrix: this.buildRouteMatrix(),
      relays: this.buildRelayHealth(),
      knowledgeSpaces: this.describeKnowledgeSpaces(),
      runtimeProtocol: {
        nodeControllerRuntime: "jobs/queue|running|done|failed + control/queue + state/controller_state.json",
        arisRuntime: this.runtimeRoot
      }
    };
  }

  createTmuxInstance(request: TmuxInstanceRequest) {
    const machine = this.requireMachine(request.machineId);
    const sessionPrefix = this.config.aris?.tmux.sessionPrefix ?? "aris";
    const entryCommand = request.entryCommand || this.config.aris?.tmux.defaultCommand || "python -m http.server 8765";
    const workspaceRoot = request.workspaceRoot || machine.workspaceRoot;
    const sessionName = `${sessionPrefix}-${slugify(request.label)}`;
    const descriptor: Record<string, unknown> = {
      id: makeId("tmux"),
      label: request.label,
      machineId: machine.id,
      machineLabel: machine.label,
      sessionName,
      workspaceRoot,
      entryCommand,
      createdAt: nowIso(),
      attachCommand:
        machine.launcher === "remote"
          ? `ssh ${machine.host} "tmux attach -t ${sessionName}"`
          : `tmux attach -t ${sessionName}`,
      launchCommand:
        machine.launcher === "remote"
          ? `ssh ${machine.host} "tmux new-session -d -s ${sessionName} 'cd ${workspaceRoot} && ${entryCommand}'"`
          : `tmux new-session -d -s ${sessionName} "cd ${workspaceRoot} && ${entryCommand}"`,
      launched: false
    };

    if (request.start) {
      if (machine.launcher === "remote") {
        const result = spawnSync("ssh", [machine.host, `tmux new-session -d -s ${sessionName} 'cd ${workspaceRoot} && ${entryCommand}'`], {
          encoding: "utf8",
          windowsHide: true
        });
        descriptor.launched = result.status === 0;
        descriptor.stdout = result.stdout?.trim();
        descriptor.stderr = result.stderr?.trim();
        descriptor.exitCode = result.status ?? -1;
      } else {
        descriptor.stderr = "Local tmux start is not attempted on Windows; use the generated command on a tmux-capable host.";
      }
    }

    this.writeJson(path.join(this.tmuxRoot, `${sessionName}.json`), descriptor);
    return descriptor;
  }

  recordReflection(request: ReflectionRequest) {
    const stamp = new Date().toISOString().replace(/[:.]/g, "-");
    const slug = slugify(request.title);
    const reflectionPath = path.join(this.reflectionRoot, `${stamp}_${slug}.md`);
    const proposalPath = path.join(this.proposalRoot, `${stamp}_${slug}.md`);
    const header = [
      "---",
      `title: ${request.title}`,
      `scope: ${request.scope}`,
      `project: ${request.projectId || "cross-project"}`,
      `created_at: ${nowIso()}`,
      "---",
      ""
    ].join("\n");
    const reflectionBody = [
      header,
      "# Observation",
      "",
      request.observation,
      "",
      "# Lesson",
      "",
      request.lesson,
      "",
      "# Upgrade Proposal",
      "",
      request.upgradeProposal,
      ""
    ].join("\n");
    const proposalBody = [
      header,
      "# Proposed Upgrade",
      "",
      request.upgradeProposal,
      "",
      "# Triggering Lesson",
      "",
      request.lesson,
      ""
    ].join("\n");
    fs.writeFileSync(reflectionPath, reflectionBody, "utf8");
    fs.writeFileSync(proposalPath, proposalBody, "utf8");
    return { reflectionPath, proposalPath };
  }

  generateDeepResearchPlan(request: DeepResearchRequest) {
    const count = Math.max(
      request.agentCount ?? this.config.aris?.defaultResearchShardCount ?? 72,
      this.config.aris?.minResearchShardCount ?? 60
    );
    const topic = request.topic.trim();
    const machineId =
      request.machineId ||
      this.config.machines.find((machine) => machine.launcher === "remote" && machine.enabled)?.id ||
      "pc";
    const taskKind = request.taskKind || "research";
    const difficulty = request.difficulty || "high";
    const axes = [
      "baseline scan",
      "negative evidence",
      "reproduction hints",
      "data sources",
      "evaluation protocol",
      "failure modes",
      "system bottlenecks",
      "tooling landscape",
      "competing pipelines",
      "open questions",
      "commercial products",
      "deployment constraints"
    ];

    const plan = {
      id: makeId("swarm"),
      topic,
      createdAt: nowIso(),
      targetMachine: machineId,
      targetAgents: count,
      strategy: "wide multi-point deep research",
      shards: Array.from({ length: count }, (_, index) => {
        const axis = axes[index % axes.length];
        const point = `${axis} / angle ${Math.floor(index / axes.length) + 1}`;
        let route: unknown;
        try {
          route = this.controlPlane.previewRoute({
            label: `${topic} shard ${index + 1}`,
            prompt: `Research ${topic} from the perspective of ${point}.`,
            taskKind,
            difficulty,
            machineId,
            projectId: "pua_research",
            conversationId: "aris-deep-research",
            taskId: `swarm-${slugify(topic)}-${index + 1}`,
            taskLabel: `${topic} / ${point}`,
            search: true
          });
        } catch (error) {
          route = { error: error instanceof Error ? error.message : String(error) };
        }
        return {
          shardId: `shard-${String(index + 1).padStart(3, "0")}`,
          objective: topic,
          point,
          recommendedDifficulty: difficulty,
          route
        };
      })
    };
    this.writeJson(path.join(this.researchRoot, `${slugify(topic)}_${plan.id}.json`), plan);
    return plan;
  }

  private buildRouteMatrix() {
    const machineIds = this.config.machines.filter((machine) => machine.enabled).map((machine) => machine.id);
    const taskKinds: TaskKind[] = ["research", "builder", "monitor"];
    const difficulties: Difficulty[] = ["low", "medium", "high"];
    return machineIds.map((machineId) => ({
      machineId,
      entries: taskKinds.flatMap((taskKind) =>
        difficulties.map((difficulty) => {
          try {
            return {
              taskKind,
              difficulty,
              route: this.controlPlane.previewRoute({
                label: `route-matrix-${taskKind}-${difficulty}`,
                prompt: "",
                taskKind,
                difficulty,
                machineId,
                projectId: "pua_research",
                conversationId: "aris-control-center"
              })
            };
          } catch (error) {
            return {
              taskKind,
              difficulty,
              route: { error: error instanceof Error ? error.message : String(error) }
            };
          }
        })
      )
    }));
  }

  private buildRelayHealth() {
    return (this.config.aris?.relays ?? []).map((relay) => ({
      ...relay,
      envPresent: Boolean(process.env[relay.apiKeyEnv]),
      status: relay.enabled && process.env[relay.apiKeyEnv] ? "ready" : relay.enabled ? "missing-key" : "disabled"
    }));
  }

  private describeKnowledgeSpaces() {
    const spaces = [
      { label: "global", path: path.join(this.knowledgeRoot, "global") },
      { label: "cross-project", path: path.join(this.knowledgeRoot, "cross-project") },
      ...this.config.projects.map((project) => ({
        label: `project:${project.id}`,
        path: path.join(this.knowledgeRoot, "projects", project.id)
      }))
    ];
    return spaces.map((space) => ({
      label: space.label,
      count: fs.existsSync(space.path) ? [...this.walkFiles(space.path, ".md")].length : 0,
      path: space.path
    }));
  }

  private ensureScaffold() {
    const folders = [
      this.runtimeRoot,
      this.knowledgeRoot,
      this.reflectionRoot,
      this.proposalRoot,
      this.tmuxRoot,
      this.researchRoot,
      path.join(this.knowledgeRoot, "global"),
      path.join(this.knowledgeRoot, "cross-project"),
      path.join(this.knowledgeRoot, "projects")
    ];
    folders.forEach((folder) => fs.mkdirSync(folder, { recursive: true }));
    for (const project of this.config.projects) {
      fs.mkdirSync(path.join(this.knowledgeRoot, "projects", project.id), { recursive: true });
    }
    this.seedReadme(path.join(this.knowledgeRoot, "global", "README.md"), "# Global Knowledge\n");
    this.seedReadme(path.join(this.knowledgeRoot, "cross-project", "README.md"), "# Cross-Project Knowledge\n");
  }

  private seedReadme(filePath: string, content: string) {
    if (!fs.existsSync(filePath)) {
      fs.writeFileSync(filePath, content, "utf8");
    }
  }

  private requireMachine(machineId: string): MachineConfig {
    const machine = this.config.machines.find((item) => item.id === machineId);
    if (!machine) {
      throw new Error(`Unknown machine: ${machineId}`);
    }
    return machine;
  }

  private listJsonDirectory(root: string) {
    if (!fs.existsSync(root)) {
      return [];
    }
    return [...this.walkFiles(root, ".json")]
      .map((filePath) => JSON.parse(fs.readFileSync(filePath, "utf8")) as Record<string, unknown>)
      .sort((left, right) =>
        String(right.createdAt ?? right.generatedAt ?? "").localeCompare(String(left.createdAt ?? left.generatedAt ?? ""))
      );
  }

  private listMarkdownDirectory(root: string, limit: number) {
    if (!fs.existsSync(root)) {
      return [];
    }
    return [...this.walkFiles(root, ".md")]
      .sort((left, right) => right.localeCompare(left))
      .slice(0, limit)
      .map((filePath) => ({
        filePath,
        title: path.basename(filePath, ".md"),
        preview: fs.readFileSync(filePath, "utf8").split(/\r?\n/).slice(0, 10).join("\n")
      }));
  }

  private *walkFiles(root: string, extension: string): Generator<string> {
    for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
      const fullPath = path.join(root, entry.name);
      if (entry.isDirectory()) {
        yield* this.walkFiles(fullPath, extension);
        continue;
      }
      if (entry.isFile() && fullPath.endsWith(extension)) {
        yield fullPath;
      }
    }
  }

  private writeJson(filePath: string, payload: unknown) {
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    fs.writeFileSync(filePath, JSON.stringify(payload, null, 2), "utf8");
  }
}
