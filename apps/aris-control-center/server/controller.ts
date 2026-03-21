import fs from "node:fs";
import { spawn, spawnSync } from "node:child_process";
import type { WebSocket } from "ws";
import type {
  AgentRun,
  ControlPlaneConfig,
  LaunchRequest,
  LiveContext,
  MachineConfig,
  PersistentState,
  ProfileConfig,
  RoutedSelection,
  RuntimeTask,
  TaskTemplate,
  TimelineEvent,
  UsageSummary
} from "./shared.js";
import { buildLiveContext, loadProfiles } from "./context.js";
import { makeId, nowIso, readJsonFile, resolveCodexHome, runtimePath, slugify } from "./shared.js";
import { makeTaskRuntimeKey, selectRoute } from "./routing.js";

const DEFAULT_STATE: PersistentState = { agents: [], taskRuntime: {} };
const LIVE_CONTEXT_TTL_MS = 10 * 60_000;

export class ControlPlane {
  readonly config: ControlPlaneConfig;
  readonly statePath: string;
  readonly eventsPath: string;
  readonly sockets = new Set<WebSocket>();

  state: PersistentState;
  events: TimelineEvent[] = [];
  schedulerHandle?: NodeJS.Timeout;
  liveContext?: LiveContext;
  liveContextAt = 0;

  constructor(configPath: string) {
    this.config = readJsonFile<ControlPlaneConfig>(configPath, {} as ControlPlaneConfig);
    fs.mkdirSync(this.config.runtimeRoot, { recursive: true });
    fs.mkdirSync(runtimePath(this.config.runtimeRoot, "agents"), { recursive: true });
    fs.mkdirSync(runtimePath(this.config.runtimeRoot, "memory"), { recursive: true });
    this.statePath = runtimePath(this.config.runtimeRoot, "state.json");
    this.eventsPath = runtimePath(this.config.runtimeRoot, "events.jsonl");
    this.state = readJsonFile<PersistentState>(this.statePath, DEFAULT_STATE);
    this.state.taskRuntime ??= {};
    for (const agent of this.state.agents) {
      agent.taskId ||= slugify((agent as Partial<AgentRun>).taskLabel || agent.label);
      agent.taskLabel ||= agent.label;
      agent.browserMode ||= agent.search ? "codex-search" : "none";
      agent.routeRationale ||= [];
    }
    this.loadEvents();
    this.liveContext = buildLiveContext(this.config, this.scanRuntimeTasks(), this.getProfiles());
    this.liveContextAt = Date.now();
    this.persistState();
  }

  snapshot(forceRefresh = false) {
    return {
      config: {
        protocolVersion: this.config.protocolVersion,
        routing: this.config.routing,
        machines: this.config.machines,
        profiles: this.getProfiles().map((profile) => ({
          ...profile,
          authRoot: profile.authStrategy === "inherit-current" ? "inherit-current" : profile.authRoot
        })),
        tasks: this.config.tasks
      },
      liveContext: this.getLiveContext(forceRefresh),
      state: this.state,
      events: this.events.slice(-300)
    };
  }

  refreshContext() {
    this.liveContext = buildLiveContext(this.config, this.scanRuntimeTasks(), this.getProfiles());
    this.liveContextAt = Date.now();
    this.broadcast({ type: "snapshot", payload: this.snapshot(false) });
    return this.liveContext;
  }

  previewRoute(request: LaunchRequest) {
    const template = request.taskTemplateId ? this.config.tasks.find((item) => item.id === request.taskTemplateId) : undefined;
    const taskId = request.taskId || template?.id || slugify(request.label);
    const taskKey = makeTaskRuntimeKey(request.projectId, request.conversationId, taskId);
    return selectRoute({
      config: this.config,
      liveContext: this.getLiveContext(),
      profiles: this.getProfiles(),
      request,
      template,
      taskId,
      lockedProfileId: this.state.taskRuntime[taskKey]?.lockedProfileId
    });
  }

  connect(socket: WebSocket) {
    this.sockets.add(socket);
    socket.send(JSON.stringify({ type: "snapshot", payload: this.snapshot() }));
    socket.on("close", () => this.sockets.delete(socket));
  }

  startScheduler() {
    this.schedulerHandle = setInterval(() => {
      this.runScheduler();
      this.pollAgents();
    }, 5000);
  }

  stopScheduler() {
    if (this.schedulerHandle) {
      clearInterval(this.schedulerHandle);
    }
  }

  launch(request: LaunchRequest): AgentRun {
    const template = request.taskTemplateId ? this.config.tasks.find((item) => item.id === request.taskTemplateId) : undefined;
    const taskId = request.taskId || template?.id || slugify(request.label);
    const route = this.route(request, template, taskId);
    const machine = this.requireMachine(route.machineId);
    const agentId = makeId("agent");
    const runDir = runtimePath(this.config.runtimeRoot, "agents", agentId);
    fs.mkdirSync(runDir, { recursive: true });
    const promptPath = runtimePath(runDir, "prompt.md");
    const logPath = runtimePath(runDir, "stdout.log");
    const lastMessagePath = runtimePath(runDir, "last_message.txt");
    const prompt = request.prompt ?? template?.promptTemplate ?? "Reply with a concise update.";
    const taskLabel = request.taskLabel || template?.label || request.label;
    fs.writeFileSync(promptPath, `${prompt}\n`, "utf8");

    const agent: AgentRun = {
      id: agentId,
      label: request.label,
      projectId: request.projectId,
      conversationId: request.conversationId,
      taskId,
      taskLabel,
      taskTemplateId: request.taskTemplateId,
      taskKind: request.taskKind,
      difficulty: request.difficulty,
      state: "queued",
      machineId: machine.id,
      launcher: machine.launcher,
      profileId: route.profileId,
      model: route.model,
      reasoningEffort: route.reasoningEffort,
      search: route.search,
      browserMode: route.browserMode,
      prompt,
      cwd: machine.workspaceRoot,
      parentAgentId: request.parentAgentId,
      createdAt: nowIso(),
      logPath,
      lastMessagePath,
      routeRationale: route.rationale
    };

    this.state.agents.unshift(agent);
    this.touchTaskRuntime(request.projectId, request.conversationId, request.taskTemplateId || taskId, route.profileId);
    this.persistState();
    this.appendEvent("route.selected", agent, { route });

    if (machine.launcher === "local") {
      this.launchLocal(agent, machine, route, promptPath);
    } else {
      this.launchRemote(agent, machine, route, promptPath);
    }
    return agent;
  }

  launchDemo(projectId: string, conversationId: string, taskId: string) {
    const root = this.launch({
      label: "root-planner",
      prompt: "You are the root planner for a remote multi-machine subagent demo. Read the current workspace notes and produce a short execution plan with token ROOT_PLANNER_OK.",
      taskKind: "research",
      difficulty: "high",
      machineId: "dev-intern-02",
      projectId,
      conversationId,
      taskId,
      taskLabel: "Remote Complex Topology Demo",
      search: true
    });
    const uiWorker = this.launch({
      label: "ui-worker",
      prompt: "Review the subagent panel UI requirements and produce a concise implementation checklist with token UI_WORKER_OK.",
      taskKind: "builder",
      difficulty: "medium",
      machineId: "dev-intern-01",
      projectId,
      conversationId,
      taskId,
      taskLabel: "Remote Complex Topology Demo",
      parentAgentId: root.id,
      search: false
    });
    const routingWorker = this.launch({
      label: "routing-worker",
      prompt: "Review multi-account routing and same-account constraints and produce a concise policy note with token ROUTING_WORKER_OK.",
      taskKind: "review",
      difficulty: "medium",
      machineId: "dev-intern-02",
      projectId,
      conversationId,
      taskId,
      taskLabel: "Remote Complex Topology Demo",
      parentAgentId: root.id,
      search: true
    });
    const summaryWorker = this.launch({
      label: "summary-worker",
      prompt: "Read existing outputs and write a short integration summary with token SUMMARY_WORKER_OK.",
      taskKind: "summary",
      difficulty: "low",
      machineId: "dev-intern-01",
      projectId,
      conversationId,
      taskId,
      taskLabel: "Remote Complex Topology Demo",
      parentAgentId: routingWorker.id,
      search: false
    });
    return { root, uiWorker, routingWorker, summaryWorker };
  }

  stopAgent(agentId: string) {
    const agent = this.state.agents.find((item) => item.id === agentId);
    if (!agent || !agent.pid) {
      return agent;
    }
    if (agent.launcher === "local") {
      spawnSync("taskkill", ["/PID", String(agent.pid), "/T", "/F"], { windowsHide: true });
    } else if (agent.remote) {
      spawnSync("ssh", [agent.remote.host, `kill ${agent.pid} >/dev/null 2>&1 || true`], { windowsHide: true });
    }
    agent.state = "stopped";
    agent.endedAt = nowIso();
    agent.output = this.readLastMessage(agent.lastMessagePath) || agent.output;
    this.persistState();
    this.appendEvent("agent.stopped", agent, {});
    return agent;
  }

  tail(agentId: string, lines = 120) {
    const agent = this.state.agents.find((item) => item.id === agentId);
    if (!agent) {
      return "";
    }
    if (agent.launcher === "local") {
      return this.tailFile(agent.logPath, lines);
    }
    if (!agent.remote) {
      return "";
    }
    const result = spawnSync(
      "python",
      ["-X", "utf8", this.config.remoteLauncherScript, "tail", "--host", agent.remote.host, "--run-id", agent.remote.runId, "--agent-name", agent.remote.agentName, "--lines", String(lines)],
      { encoding: "utf8", windowsHide: true }
    );
    return result.stdout || result.stderr || "";
  }

  private route(request: LaunchRequest, template: TaskTemplate | undefined, taskId: string): RoutedSelection {
    const machineId = request.machineId || template?.machineId || "pc";
    const taskKey = makeTaskRuntimeKey(request.projectId, request.conversationId, taskId);
    return selectRoute({
      config: this.config,
      liveContext: this.getLiveContext(),
      profiles: this.getProfiles(),
      request,
      template,
      taskId,
      lockedProfileId: this.state.taskRuntime[taskKey]?.lockedProfileId
    });
  }

  private launchLocal(agent: AgentRun, machine: MachineConfig, route: RoutedSelection, promptPath: string) {
    const profile = this.requireProfile(route.profileId);
    const stdoutFd = fs.openSync(agent.logPath, "a");
    const stderrFd = fs.openSync(agent.logPath, "a");
    const args = ["exec", "--skip-git-repo-check", "--ephemeral", "--json", "-s", "read-only", "-C", machine.workspaceRoot, "-o", agent.lastMessagePath, "-m", route.model, "-c", `model_reasoning_effort="${route.reasoningEffort}"`, "-"];
    if (route.search || route.browserMode === "codex-search") {
      args.unshift("--search");
    }
    const child = spawn(this.config.codexBinaryPath, args, {
      cwd: machine.workspaceRoot,
      env: { ...process.env, CODEX_HOME: resolveCodexHome(machine, profile) },
      windowsHide: true,
      detached: true,
      stdio: ["pipe", stdoutFd, stderrFd]
    });
    if (!child.stdin) {
      throw new Error("Failed to open stdin for local Codex process");
    }
    child.stdin.end(fs.readFileSync(promptPath, "utf8"));
    child.unref();
    agent.state = "starting";
    agent.pid = child.pid ?? undefined;
    agent.startedAt = nowIso();
    this.persistState();
    this.appendEvent("agent.started", agent, { pid: agent.pid, launcher: "local" });
  }

  private launchRemote(agent: AgentRun, machine: MachineConfig, route: RoutedSelection, promptPath: string) {
    const profile = this.requireProfile(route.profileId);
    const runId = `${new Date().toISOString().slice(0, 10).replace(/-/g, "")}_${agent.id}`;
    const agentName = agent.id.slice(-12);
    const args = ["-X", "utf8", this.config.remoteLauncherScript, "launch", "--host", machine.host, "--run-id", runId, "--agent-name", agentName, "--cwd", machine.workspaceRoot, "--prompt-file", promptPath, "--skip-install", "--sandbox", "danger-full-access", "--approval", "never", "--model", route.model];
    args.push("--env", `CODEX_HOME=${resolveCodexHome(machine, profile)}`);
    if (route.search || route.browserMode === "codex-search") {
      args.push("--search");
    }
    const result = spawnSync("python", args, { encoding: "utf8", windowsHide: true });
    if (result.status !== 0) {
      agent.state = "failed";
      agent.error = result.stderr || result.stdout || "Remote launch failed";
      agent.endedAt = nowIso();
      this.persistState();
      this.appendEvent("agent.failed", agent, { error: agent.error });
      return;
    }
    const payload = JSON.parse(result.stdout) as { pid: string; host: string; run_id: string; agent_name: string };
    agent.state = "starting";
    agent.pid = Number(payload.pid);
    agent.startedAt = nowIso();
    agent.remote = { host: payload.host, runId: payload.run_id, agentName: payload.agent_name };
    this.persistState();
    this.appendEvent("agent.started", agent, { pid: agent.pid, launcher: "remote" });
  }

  private pollAgents() {
    for (const agent of this.state.agents.filter((item) => ["starting", "running"].includes(item.state))) {
      this.refreshFromLog(agent);
      if (agent.launcher === "local") {
        this.pollLocal(agent);
      } else {
        this.pollRemote(agent);
      }
    }
  }

  private pollLocal(agent: AgentRun) {
    const running = agent.pid ? this.isPidRunning(agent.pid) : false;
    if (!running && !["completed", "failed", "stopped"].includes(agent.state)) {
      agent.state = agent.output ? "completed" : "failed";
      agent.endedAt = nowIso();
      this.persistState();
      this.appendEvent(agent.state === "completed" ? "agent.completed" : "agent.failed", agent, { output: agent.output ?? "", usage: agent.usage ?? {} });
    }
  }

  private pollRemote(agent: AgentRun) {
    if (!agent.remote) {
      return;
    }
    const result = spawnSync("python", ["-X", "utf8", this.config.remoteLauncherScript, "status", "--host", agent.remote.host, "--run-id", agent.remote.runId], {
      encoding: "utf8",
      windowsHide: true
    });
    const record = result.stdout
      .split(/\r?\n/)
      .filter(Boolean)
      .map((line) => {
        try {
          return JSON.parse(line) as Record<string, unknown>;
        } catch {
          return null;
        }
      })
      .find((item) => item?.agent_name === agent.remote?.agentName);
    if (!record) {
      return;
    }
    const running = Boolean(record.running);
    agent.state = running ? "running" : Number(record.returncode ?? 0) === 0 ? "completed" : "failed";
    if (!running && !agent.endedAt) {
      agent.endedAt = nowIso();
      agent.output = this.readLastMessage(agent.lastMessagePath) || agent.output || this.tail(agent.id, 30);
      this.persistState();
      this.appendEvent(agent.state === "completed" ? "agent.completed" : "agent.failed", agent, { output: agent.output ?? "", usage: agent.usage ?? {} });
    } else {
      this.persistState();
      this.appendEvent("agent.heartbeat", agent, { running, usage: agent.usage ?? {} });
    }
  }

  private refreshFromLog(agent: AgentRun) {
    const lines = (agent.launcher === "local" ? this.tailFile(agent.logPath, 160) : this.tail(agent.id, 160))
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean);
    let usage: UsageSummary | undefined;
    for (const line of lines) {
      try {
        const payload = JSON.parse(line) as Record<string, unknown>;
        const type = String(payload.type ?? "unknown");
        if (type === "thread.started") {
          agent.threadId = String(payload.thread_id ?? agent.threadId ?? "");
          agent.state = "running";
        }
        if (type === "turn.started") {
          agent.state = "running";
        }
        if (type === "turn.completed" && typeof payload.usage === "object" && payload.usage) {
          const raw = payload.usage as Record<string, unknown>;
          usage = {
            inputTokens: Number(raw.input_tokens ?? 0),
            cachedInputTokens: Number(raw.cached_input_tokens ?? 0),
            outputTokens: Number(raw.output_tokens ?? 0)
          };
        }
        if (type === "item.completed" && typeof payload.item === "object" && payload.item) {
          const item = payload.item as Record<string, unknown>;
          if (item.type === "agent_message") {
            agent.output = String(item.text ?? agent.output ?? "");
          }
        }
      } catch {
        continue;
      }
    }
    const lastMessage = this.readLastMessage(agent.lastMessagePath);
    if (lastMessage) {
      agent.output = lastMessage;
    }
    if (usage) {
      agent.usage = usage;
    }
  }

  private runScheduler() {
    const now = Date.now();
    for (const task of this.config.tasks.filter((item) => item.trigger.mode === "interval" && item.trigger.intervalMinutes)) {
      const taskKey = makeTaskRuntimeKey(task.projectId, task.conversationId, task.id);
      const runtime = this.state.taskRuntime[taskKey];
      const last = runtime?.lastTriggeredAt ? Date.parse(runtime.lastTriggeredAt) : 0;
      if (!last || now - last >= Number(task.trigger.intervalMinutes) * 60 * 1000) {
        this.touchTaskRuntime(task.projectId, task.conversationId, task.id, runtime?.lockedProfileId, true);
        this.appendEvent(
          "trigger.timer.fired",
          {
            id: task.id,
            projectId: task.projectId,
            conversationId: task.conversationId,
            taskId: task.id,
            taskTemplateId: task.id,
            parentAgentId: undefined,
            machineId: task.machineId,
            profileId: this.config.routing.pinProfileId
          },
          { label: task.label, intervalMinutes: task.trigger.intervalMinutes }
        );
      }
    }
  }

  private appendEvent(type: string, agent: Pick<AgentRun, "projectId" | "conversationId" | "taskId" | "taskTemplateId" | "id" | "parentAgentId" | "machineId" | "profileId">, payload: Record<string, unknown>) {
    const event: TimelineEvent = {
      id: makeId("evt"),
      protocolVersion: this.config.protocolVersion,
      ts: nowIso(),
      projectId: agent.projectId,
      conversationId: agent.conversationId,
      taskId: agent.taskId,
      taskTemplateId: agent.taskTemplateId,
      agentId: agent.id || undefined,
      parentAgentId: agent.parentAgentId,
      machineId: agent.machineId,
      profileId: agent.profileId,
      kind: type.startsWith("trigger.") || type.startsWith("route.") || type.startsWith("agent.") ? "event" : "state",
      type,
      payload
    };
    this.events.push(event);
    fs.appendFileSync(this.eventsPath, `${JSON.stringify(event)}\n`, "utf8");
    this.broadcast({ type: "event", payload: event });
  }

  private getProfiles() {
    return loadProfiles(this.config);
  }

  private getLiveContext(forceRefresh = false): LiveContext {
    const stale = forceRefresh || !this.liveContext || Date.now() - this.liveContextAt > LIVE_CONTEXT_TTL_MS;
    if (stale) {
      this.liveContext = buildLiveContext(this.config, this.scanRuntimeTasks(), this.getProfiles());
      this.liveContextAt = Date.now();
    }
    return this.liveContext!;
  }

  private scanRuntimeTasks(): RuntimeTask[] {
    const map = new Map<string, RuntimeTask>();
    for (const agent of this.state.agents) {
      if (!map.has(agent.taskId)) {
        map.set(agent.taskId, { id: agent.taskId, label: agent.taskLabel, projectId: agent.projectId, conversationId: agent.conversationId });
      }
    }
    return [...map.values()];
  }

  private touchTaskRuntime(projectId: string, conversationId: string, taskId?: string, lockedProfileId?: string, triggered = false) {
    if (!taskId || !projectId || !conversationId) {
      return;
    }
    const key = makeTaskRuntimeKey(projectId, conversationId, taskId);
    const runtime = this.state.taskRuntime[key] ?? { launchCount: 0 };
    if (triggered) {
      runtime.lastTriggeredAt = nowIso();
    }
    runtime.lastLaunchedAt = nowIso();
    runtime.launchCount += 1;
    if (lockedProfileId) {
      runtime.lockedProfileId = lockedProfileId;
    }
    this.state.taskRuntime[key] = runtime;
  }

  private requireMachine(machineId: string): MachineConfig {
    const machine = this.config.machines.find((item) => item.id === machineId && item.enabled);
    if (!machine) {
      throw new Error(`Machine ${machineId} is unavailable`);
    }
    return machine;
  }

  private requireProfile(profileId: string): ProfileConfig {
    const profile = this.getProfiles().find((item) => item.id === profileId);
    if (!profile) {
      throw new Error(`Profile ${profileId} is unavailable`);
    }
    return profile;
  }

  private readLastMessage(filePath: string) {
    return fs.existsSync(filePath) ? fs.readFileSync(filePath, "utf8").trim() : "";
  }

  private loadEvents() {
    if (!fs.existsSync(this.eventsPath)) {
      return;
    }
    this.events = fs.readFileSync(this.eventsPath, "utf8").split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line) as TimelineEvent);
  }

  private persistState() {
    fs.writeFileSync(this.statePath, JSON.stringify(this.state, null, 2), "utf8");
    this.broadcast({ type: "snapshot", payload: this.snapshot(false) });
  }

  private broadcast(message: Record<string, unknown>) {
    const encoded = JSON.stringify(message);
    for (const socket of this.sockets) {
      if (socket.readyState === 1) {
        socket.send(encoded);
      }
    }
  }

  private isPidRunning(pid: number) {
    const result = spawnSync("tasklist", ["/FI", `PID eq ${pid}`], { encoding: "utf8", windowsHide: true });
    return result.stdout.includes(String(pid));
  }

  private tailFile(filePath: string, lines: number) {
    if (!fs.existsSync(filePath)) {
      return "";
    }
    return fs.readFileSync(filePath, "utf8").split(/\r?\n/).slice(-lines).join("\n");
  }
}
