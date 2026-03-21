import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import type {
  CodexSession,
  ControlPlaneConfig,
  ConversationConfig,
  IdentitySnapshot,
  LiveContext,
  MachineConfig,
  ProfileConfig,
  ProjectConfig,
  RuntimeTask
} from "./shared.js";
import {
  decodeJwtPayload,
  fingerprintAccount,
  maskSecret,
  nowIso,
  parseFrontmatter,
  resolveCodexAuthFile,
  slugify
} from "./shared.js";

const SSH_CONNECT_TIMEOUT_SECONDS = 10;
const SSH_COMMAND_TIMEOUT_MS = 30_000;
const SSH_RETRY_ATTEMPTS = 3;

export function loadProfiles(config: ControlPlaneConfig): ProfileConfig[] {
  return config.profiles.map((profile) => {
    if (profile.credit.mode !== "file" || !profile.credit.sourcePath) {
      return profile;
    }
    try {
      const raw = JSON.parse(fs.readFileSync(profile.credit.sourcePath, "utf8")) as {
        remaining?: number;
        reserveFloor?: number;
      };
      return {
        ...profile,
        credit: {
          ...profile.credit,
          remaining: Number(raw.remaining ?? profile.credit.remaining),
          reserveFloor: Number(raw.reserveFloor ?? profile.credit.reserveFloor)
        }
      };
    } catch {
      return profile;
    }
  });
}

export function buildLiveContext(
  config: ControlPlaneConfig,
  runtimeTasks: RuntimeTask[],
  profiles: ProfileConfig[]
): LiveContext {
  const projects = scanProjects(config);
  const sessions = scanCodexSessions(config);
  const identities = scanIdentities(config, profiles);
  const conversationMap = new Map<string, ConversationConfig>();

  for (const session of sessions) {
    const projectId = pickProjectForSession(projects, session);
    conversationMap.set(session.id, {
      id: session.id,
      label: session.label,
      projectId,
      taskId: slugify(session.label),
      machineId: session.machineId
    });
  }

  for (const conversation of config.conversations) {
    if (!conversationMap.has(conversation.id)) {
      conversationMap.set(conversation.id, conversation);
    }
  }

  return {
    projects,
    conversations: [...conversationMap.values()].sort((left, right) => right.id.localeCompare(left.id)),
    runtimeTasks,
    codexSessions: sessions,
    identities,
    scannedAt: nowIso()
  };
}

function scanProjects(config: ControlPlaneConfig): ProjectConfig[] {
  const root = path.join(config.agentDocRoot, "PROJECTS");
  if (!fs.existsSync(root)) {
    return config.projects;
  }
  const result: ProjectConfig[] = [];
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    if (!entry.isDirectory()) {
      continue;
    }
    const projectDoc = path.join(root, entry.name, "PROJECT_DOCS.md");
    if (!fs.existsSync(projectDoc)) {
      continue;
    }
    const meta = parseFrontmatter(projectDoc);
    const configured = config.projects.find((item) => item.id === entry.name.replace(/_/g, "-"));
    result.push({
      id: entry.name.replace(/_/g, "-"),
      label: entry.name,
      folderName: entry.name,
      agentDocPath: projectDoc,
      workspaceRoot: configured?.workspaceRoot || "",
      summary: meta.summary || configured?.summary || "",
      title: meta.title || configured?.label || entry.name,
      panelHidden: meta.panel_hidden === "true"
    });
  }
  return result.sort((left, right) => left.id.localeCompare(right.id));
}

function scanCodexSessions(config: ControlPlaneConfig): CodexSession[] {
  const sessions: CodexSession[] = [];
  const localPath = path.join(process.env.USERPROFILE || "", ".codex", "session_index.jsonl");
  sessions.push(...readSessionIndex(localPath, "pc", "local"));
  for (const machine of config.machines.filter((item) => item.launcher === "remote" && item.enabled)) {
    const result = runRemoteSsh(machine.host, "tail -n 200 ~/.codex/session_index.jsonl");
    if (result.status === 0) {
      sessions.push(...readSessionLines(result.stdout, machine.id, "remote"));
    }
  }
  const deduped = new Map<string, CodexSession>();
  for (const session of sessions) {
    deduped.set(`${session.machineId}:${session.id}`, session);
  }
  return [...deduped.values()].sort((left, right) => right.updatedAt.localeCompare(left.updatedAt));
}

function readSessionIndex(filePath: string, machineId: string, source: "local" | "remote"): CodexSession[] {
  if (!fs.existsSync(filePath)) {
    return [];
  }
  return readSessionLines(fs.readFileSync(filePath, "utf8"), machineId, source);
}

function readSessionLines(raw: string, machineId: string, source: "local" | "remote"): CodexSession[] {
  return raw
    .split(/\r?\n/)
    .filter(Boolean)
    .slice(-200)
    .map((line) => {
      try {
        const payload = JSON.parse(line) as Record<string, unknown>;
        return {
          id: String(payload.id),
          label: String(payload.thread_name ?? payload.id),
          updatedAt: String(payload.updated_at ?? nowIso()),
          machineId,
          source
        } satisfies CodexSession;
      } catch {
        return null;
      }
    })
    .filter(Boolean) as CodexSession[];
}

function scanIdentities(config: ControlPlaneConfig, profiles: ProfileConfig[]): IdentitySnapshot[] {
  const machines = config.machines.filter((item) => item.enabled);
  const pinnedProfile = profiles.find((item) => item.id === config.routing.pinProfileId) ?? profiles[0];
  const pinnedMachine = machines.find((item) => item.id === "pc") ?? machines.find((item) => pinnedProfile?.machineIds.includes(item.id));
  const pinnedSnapshot = pinnedProfile && pinnedMachine ? readProfileIdentity(pinnedMachine, pinnedProfile, "") : undefined;
  const pinnedAccountKey = pinnedSnapshot?.accountKey ?? "";
  const snapshots: IdentitySnapshot[] = [];

  for (const machine of machines) {
    for (const profile of profiles.filter((item) => item.machineIds.includes(machine.id))) {
      snapshots.push(readProfileIdentity(machine, profile, pinnedAccountKey));
    }
  }

  const profileAccountKeys = new Map<string, Set<string>>();
  for (const snapshot of snapshots) {
    if (!snapshot.available || !snapshot.verified || !snapshot.accountKey) {
      continue;
    }
    const bucket = profileAccountKeys.get(snapshot.profileId) ?? new Set<string>();
    bucket.add(snapshot.accountKey);
    profileAccountKeys.set(snapshot.profileId, bucket);
  }

  for (const snapshot of snapshots) {
    if ((profileAccountKeys.get(snapshot.profileId)?.size ?? 0) > 1) {
      snapshot.issues = [...new Set([...snapshot.issues, "profile-account-mismatch"])];
    }
  }

  return snapshots.sort((left, right) => {
    const machineOrder = left.machineLabel.localeCompare(right.machineLabel);
    if (machineOrder !== 0) {
      return machineOrder;
    }
    return left.profileLabel.localeCompare(right.profileLabel);
  });
}

function readProfileIdentity(machine: MachineConfig, profile: ProfileConfig, pinnedAccountKey: string): IdentitySnapshot {
  const authPath = resolveCodexAuthFile(machine, profile);
  const base = emptyIdentity(machine, profile, authPath, pinnedAccountKey);
  const payload = machine.launcher === "remote" ? readRemoteAuth(machine.host, authPath) : readLocalAuth(authPath);

  if (payload.status !== "ok") {
    return { ...base, issues: [payload.status === "missing" ? "auth.json missing" : "auth.json unreadable"] };
  }

  return readIdentity(machine, profile, authPath, payload.raw, pinnedAccountKey) ?? {
    ...base,
    available: true,
    issues: ["auth payload unreadable"]
  };
}

function emptyIdentity(
  machine: MachineConfig,
  profile: ProfileConfig,
  authPath: string,
  pinnedAccountKey: string
): IdentitySnapshot {
  return {
    key: `${machine.id}:${profile.id}`,
    machineId: machine.id,
    machineLabel: machine.label,
    profileId: profile.id,
    profileLabel: profile.label,
    available: false,
    verified: false,
    sameAsPinned: false,
    accountKey: "",
    emailMasked: "",
    accountIdMasked: "",
    userIdMasked: "",
    planType: "",
    authPath,
    authStrategy: profile.authStrategy,
    issues: []
  };
}

function readLocalAuth(authPath: string): { status: "ok"; raw: string } | { status: "missing" | "unreadable" } {
  if (!fs.existsSync(authPath)) {
    return { status: "missing" };
  }
  try {
    return { status: "ok", raw: fs.readFileSync(authPath, "utf8") };
  } catch {
    return { status: "unreadable" };
  }
}

function readRemoteAuth(host: string, authPath: string): { status: "ok"; raw: string } | { status: "missing" | "unreadable" } {
  const quoted = shellQuotePosix(authPath);
  const result = runRemoteSsh(host, `if [ -f ${quoted} ]; then cat ${quoted}; else printf '__AUTH_MISSING__'; fi`);
  if (result.status !== 0) {
    return { status: "unreadable" };
  }
  if (result.stdout.trim() === "__AUTH_MISSING__") {
    return { status: "missing" };
  }
  return { status: "ok", raw: result.stdout };
}

function shellQuotePosix(value: string) {
  return `'${value.replace(/'/g, `'\"'\"'`)}'`;
}

function runRemoteSsh(host: string, command: string) {
  let last = spawnSync("ssh", ["-o", `ConnectTimeout=${SSH_CONNECT_TIMEOUT_SECONDS}`, host, command], {
    encoding: "utf8",
    windowsHide: true,
    timeout: SSH_COMMAND_TIMEOUT_MS
  });
  for (let attempt = 1; attempt < SSH_RETRY_ATTEMPTS && last.status !== 0; attempt += 1) {
    last = spawnSync("ssh", ["-o", `ConnectTimeout=${SSH_CONNECT_TIMEOUT_SECONDS}`, host, command], {
      encoding: "utf8",
      windowsHide: true,
      timeout: SSH_COMMAND_TIMEOUT_MS
    });
  }
  return last;
}

function readIdentity(
  machine: MachineConfig,
  profileConfig: ProfileConfig,
  authPath: string,
  raw: string,
  pinnedAccountKey: string
): IdentitySnapshot | null {
  try {
    const payload = JSON.parse(raw) as { tokens?: { id_token?: string; access_token?: string; account_id?: string } };
    const idToken = decodeJwtPayload(payload.tokens?.id_token);
    const accessToken = decodeJwtPayload(payload.tokens?.access_token);
    const auth = (idToken?.["https://api.openai.com/auth"] as Record<string, unknown>) || {};
    const profile = (accessToken?.["https://api.openai.com/profile"] as Record<string, unknown>) || {};
    const email = String(profile.email ?? idToken?.email ?? "");
    const accountId = String(auth.chatgpt_account_id ?? payload.tokens?.account_id ?? "");
    const userId = String(auth.chatgpt_user_id ?? auth.user_id ?? "");
    const accountKey = fingerprintAccount(email, accountId, userId);
    return {
      key: `${machine.id}:${profileConfig.id}`,
      machineId: machine.id,
      machineLabel: machine.label,
      profileId: profileConfig.id,
      profileLabel: profileConfig.label,
      available: true,
      verified: Boolean(email || accountId || userId),
      sameAsPinned: Boolean(accountKey && pinnedAccountKey && accountKey === pinnedAccountKey),
      accountKey,
      emailMasked: maskSecret(email, 3),
      accountIdMasked: maskSecret(accountId, 4),
      userIdMasked: maskSecret(userId, 4),
      planType: String(auth.chatgpt_plan_type ?? ""),
      authPath,
      authStrategy: profileConfig.authStrategy,
      issues: []
    };
  } catch {
    return null;
  }
}

function pickProjectForSession(projects: ProjectConfig[], session: CodexSession): string {
  const haystack = normalizeText(session.label);
  let bestProject: ProjectConfig | undefined;
  let bestScore = 0;

  for (const project of projects.filter((item) => !item.panelHidden)) {
    const keywords = buildProjectKeywords(project);
    let score = 0;
    for (const keyword of keywords) {
      if (!keyword) {
        continue;
      }
      if (haystack.includes(keyword)) {
        score += keyword.length >= 8 ? 6 : 3;
      }
    }
    if (score > bestScore) {
      bestScore = score;
      bestProject = project;
    }
  }

  return bestProject?.id || "other";
}

function buildProjectKeywords(project: ProjectConfig): string[] {
  const raw = [project.folderName, project.id, project.title || "", project.summary || ""].join(" ");
  const tokens = raw
    .toLowerCase()
    .split(/[^a-z0-9\u4e00-\u9fff]+/)
    .map((item) => item.trim())
    .filter((item) => item.length >= 3);
  return [...new Set([normalizeText(project.folderName), normalizeText(project.id), ...tokens.map((item) => normalizeText(item))])];
}

function normalizeText(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9\u4e00-\u9fff]+/g, "");
}
