import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

export type Difficulty = "low" | "medium" | "high";
export type TaskKind = "research" | "builder" | "monitor" | "summary" | "review";
export type TriggerMode = "manual" | "interval" | "event";
export type AgentState = "queued" | "starting" | "running" | "completed" | "failed" | "stopped";
export type LauncherKind = "local" | "remote";
export type BrowserMode = "none" | "codex-search" | "playwright-remote";

export interface RelayConfig {
  id: string;
  label: string;
  provider: string;
  baseUrl: string;
  apiKeyEnv: string;
  enabled: boolean;
  browserCapable?: boolean;
  tags?: string[];
}

export interface TmuxConfig {
  sessionPrefix: string;
  defaultCommand: string;
}

export interface ArisConfig {
  dashboardLabel: string;
  defaultResearchShardCount: number;
  minResearchShardCount: number;
  tmux: TmuxConfig;
  relays: RelayConfig[];
}

export interface CreditConfig {
  mode?: "manual" | "file";
  remaining: number;
  reserveFloor: number;
  sourcePath?: string;
}

export interface ModelTier {
  model: string;
  reasoningEffort: string;
  search: boolean;
  browserMode?: BrowserMode;
}

export interface ProfileConfig {
  id: string;
  label: string;
  authStrategy: "inherit-current" | "auth-root";
  authRoot: string;
  enabled: boolean;
  allowSelection: boolean;
  routingWeight: number;
  credit: CreditConfig;
  machineIds: string[];
  modelTiers: Record<string, ModelTier>;
}

export interface MachineConfig {
  id: string;
  label: string;
  launcher: LauncherKind;
  host: string;
  enabled: boolean;
  workspaceRoot: string;
  agentDocRoot: string;
  remoteRunRoot?: string;
}

export interface ProjectConfig {
  id: string;
  label: string;
  folderName: string;
  agentDocPath: string;
  workspaceRoot: string;
  summary?: string;
  title?: string;
  panelHidden?: boolean;
}

export interface ConversationConfig {
  id: string;
  label: string;
  projectId: string;
  taskId: string;
  machineId?: string;
}

export interface RuntimeTask {
  id: string;
  label: string;
  projectId: string;
  conversationId: string;
}

export interface CodexSession {
  id: string;
  label: string;
  updatedAt: string;
  machineId: string;
  source: "local" | "remote";
}

export interface IdentitySnapshot {
  key: string;
  machineId: string;
  machineLabel: string;
  profileId: string;
  profileLabel: string;
  available: boolean;
  verified: boolean;
  sameAsPinned: boolean;
  accountKey: string;
  emailMasked: string;
  accountIdMasked: string;
  userIdMasked: string;
  planType: string;
  authPath: string;
  authStrategy: ProfileConfig["authStrategy"];
  issues: string[];
}

export interface UsageSummary {
  inputTokens: number;
  cachedInputTokens: number;
  outputTokens: number;
}

export interface TaskTemplate {
  id: string;
  label: string;
  projectId: string;
  conversationId: string;
  taskKind: TaskKind;
  difficulty: Difficulty;
  machineId: string;
  trigger: {
    mode: TriggerMode;
    autoDispatch: boolean;
    intervalMinutes?: number;
    eventTypes?: string[];
  };
  search: boolean;
  browserMode?: BrowserMode;
  promptTemplate: string;
}

export interface RoutingConfig {
  mode: string;
  pinProfileId: string;
  allowMultiAccount: boolean;
  difficultyTierMap: Record<Difficulty, string>;
  taskKindTierMap: Record<TaskKind, string>;
}

export interface ControlPlaneConfig {
  protocolVersion: string;
  workspaceRoot: string;
  agentDocRoot: string;
  runtimeRoot: string;
  codexBinaryPath: string;
  remoteLauncherScript: string;
  routing: RoutingConfig;
  profiles: ProfileConfig[];
  machines: MachineConfig[];
  projects: ProjectConfig[];
  conversations: ConversationConfig[];
  tasks: TaskTemplate[];
  aris?: ArisConfig;
}

export interface RoutedSelection {
  profileId: string;
  machineId: string;
  tierId: string;
  model: string;
  reasoningEffort: string;
  search: boolean;
  browserMode: BrowserMode;
  rationale: string[];
}

export interface AgentRun {
  id: string;
  label: string;
  projectId: string;
  conversationId: string;
  taskId: string;
  taskLabel: string;
  taskTemplateId?: string;
  taskKind: TaskKind;
  difficulty: Difficulty;
  state: AgentState;
  machineId: string;
  launcher: LauncherKind;
  profileId: string;
  model: string;
  reasoningEffort: string;
  search: boolean;
  browserMode: BrowserMode;
  prompt: string;
  cwd: string;
  parentAgentId?: string;
  startedAt?: string;
  endedAt?: string;
  createdAt: string;
  pid?: number;
  threadId?: string;
  remote?: {
    host: string;
    runId: string;
    agentName: string;
  };
  logPath: string;
  lastMessagePath: string;
  output?: string;
  error?: string;
  usage?: UsageSummary;
  routeRationale: string[];
}

export interface TimelineEvent {
  id: string;
  protocolVersion: string;
  ts: string;
  projectId: string;
  conversationId: string;
  taskId?: string;
  taskTemplateId?: string;
  agentId?: string;
  parentAgentId?: string;
  machineId?: string;
  profileId?: string;
  kind: "event" | "state";
  type: string;
  payload: Record<string, unknown>;
}

export interface PersistentState {
  agents: AgentRun[];
  taskRuntime: Record<
    string,
    {
      lastTriggeredAt?: string;
      lastLaunchedAt?: string;
      launchCount: number;
      lockedProfileId?: string;
    }
  >;
}

export interface LiveContext {
  projects: ProjectConfig[];
  conversations: ConversationConfig[];
  runtimeTasks: RuntimeTask[];
  codexSessions: CodexSession[];
  identities: IdentitySnapshot[];
  scannedAt: string;
}

export interface LaunchRequest {
  taskTemplateId?: string;
  label: string;
  prompt?: string;
  taskKind: TaskKind;
  difficulty: Difficulty;
  machineId: string;
  projectId: string;
  conversationId: string;
  profileId?: string;
  taskId?: string;
  taskLabel?: string;
  parentAgentId?: string;
  search?: boolean;
  browserMode?: BrowserMode;
}

export function nowIso(): string {
  return new Date().toISOString();
}

export function makeId(prefix: string): string {
  return `${prefix}-${crypto.randomUUID()}`;
}

export function readJsonFile<T>(filePath: string, fallback: T): T {
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8")) as T;
  } catch {
    return fallback;
  }
}

export function runtimePath(root: string, ...parts: string[]): string {
  return path.join(root, ...parts);
}

export function slugify(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "") || "task";
}

export function maskSecret(value: string, visible = 4): string {
  if (!value) {
    return "";
  }
  if (value.length <= visible * 2) {
    return `${value.slice(0, visible)}...`;
  }
  return `${value.slice(0, visible)}...${value.slice(-visible)}`;
}

export function decodeJwtPayload(token?: string): Record<string, unknown> | null {
  if (!token || !token.includes(".")) {
    return null;
  }
  try {
    const payload = token.split(".")[1];
    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=");
    return JSON.parse(Buffer.from(padded, "base64").toString("utf8")) as Record<string, unknown>;
  } catch {
    return null;
  }
}

export function parseFrontmatter(filePath: string): Record<string, string> {
  try {
    const raw = fs.readFileSync(filePath, "utf8");
    const match = raw.match(/^---\r?\n([\s\S]*?)\r?\n---/);
    if (!match) {
      return {};
    }
    const result: Record<string, string> = {};
    for (const line of match[1].split(/\r?\n/)) {
      const entry = line.match(/^([A-Za-z0-9_]+):\s*(.*)$/);
      if (entry) {
        result[entry[1]] = entry[2].replace(/^"|"$/g, "");
      }
    }
    return result;
  } catch {
    return {};
  }
}

export function fingerprintAccount(...parts: string[]): string {
  const filtered = parts.map((item) => item.trim()).filter(Boolean);
  if (!filtered.length) {
    return "";
  }
  return crypto.createHash("sha1").update(filtered.join("::")).digest("hex");
}

export function resolveCodexHome(
  machine: Pick<MachineConfig, "launcher" | "workspaceRoot">,
  profile: ProfileConfig
): string {
  if (profile.authStrategy === "inherit-current") {
    if (machine.launcher === "remote") {
      return path.posix.join(machine.workspaceRoot, ".codex");
    }
    return profile.authRoot || path.win32.join(process.env.USERPROFILE || "", ".codex");
  }
  return profile.authRoot;
}

export function resolveCodexAuthFile(
  machine: Pick<MachineConfig, "launcher" | "workspaceRoot">,
  profile: ProfileConfig
): string {
  const home = resolveCodexHome(machine, profile);
  return machine.launcher === "remote" ? path.posix.join(home, "auth.json") : path.win32.join(home, "auth.json");
}
