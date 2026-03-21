import test from "node:test";
import assert from "node:assert/strict";
import { selectRoute } from "../server/routing.js";
import type {
  ControlPlaneConfig,
  IdentitySnapshot,
  LaunchRequest,
  LiveContext,
  MachineConfig,
  ProfileConfig
} from "../server/shared.js";

function makeMachine(id: string, launcher: MachineConfig["launcher"]): MachineConfig {
  return {
    id,
    label: id,
    launcher,
    host: id,
    enabled: true,
    workspaceRoot: launcher === "remote" ? "/dev_vepfs/rc_wu" : "F:\\InformationAndCourses\\Code\\codex-subagent-control-plane",
    agentDocRoot: launcher === "remote" ? "/dev_vepfs/rc_wu/AgentDoc" : "F:\\InformationAndCourses\\Code\\AgentDoc"
  };
}

function makeProfile(
  id: string,
  options: Partial<ProfileConfig> = {}
): ProfileConfig {
  return {
    id,
    label: id,
    authStrategy: "auth-root",
    authRoot: options.authRoot ?? `/auth/${id}`,
    enabled: options.enabled ?? true,
    allowSelection: options.allowSelection ?? true,
    routingWeight: options.routingWeight ?? 1,
    credit: {
      mode: "manual",
      remaining: options.credit?.remaining ?? 1,
      reserveFloor: options.credit?.reserveFloor ?? 0.1,
      sourcePath: ""
    },
    machineIds: options.machineIds ?? ["dev-intern-02"],
    modelTiers: {
      quick: {
        model: "gpt-5.4",
        reasoningEffort: "medium",
        search: false,
        browserMode: "none"
      },
      balanced: {
        model: "gpt-5.4",
        reasoningEffort: "high",
        search: true,
        browserMode: "codex-search"
      },
      deep: {
        model: "gpt-5.4",
        reasoningEffort: "xhigh",
        search: true,
        browserMode: "codex-search"
      }
    }
  };
}

function makeIdentity(
  machineId: string,
  profileId: string,
  accountKey: string,
  options: Partial<IdentitySnapshot> = {}
): IdentitySnapshot {
  return {
    key: `${machineId}:${profileId}`,
    machineId,
    machineLabel: machineId,
    profileId,
    profileLabel: profileId,
    available: options.available ?? true,
    verified: options.verified ?? true,
    sameAsPinned: options.sameAsPinned ?? profileId === "current-session",
    accountKey,
    emailMasked: options.emailMasked ?? "abc...xyz",
    accountIdMasked: options.accountIdMasked ?? "acct...1234",
    userIdMasked: options.userIdMasked ?? "user...1234",
    planType: options.planType ?? "pro",
    authPath: options.authPath ?? `/auth/${profileId}/auth.json`,
    authStrategy: options.authStrategy ?? "auth-root",
    issues: options.issues ?? []
  };
}

function makeConfig(profiles: ProfileConfig[], allowMultiAccount = true): ControlPlaneConfig {
  return {
    protocolVersion: "scp.v1",
    workspaceRoot: "F:\\InformationAndCourses\\Code\\codex-subagent-control-plane",
    agentDocRoot: "F:\\InformationAndCourses\\Code\\AgentDoc",
    runtimeRoot: "F:\\InformationAndCourses\\Code\\codex-subagent-control-plane\\runtime",
    codexBinaryPath: "codex.exe",
    remoteLauncherScript: "remote.py",
    routing: {
      mode: "current-task-locked",
      pinProfileId: "current-session",
      allowMultiAccount,
      difficultyTierMap: {
        low: "quick",
        medium: "balanced",
        high: "deep"
      },
      taskKindTierMap: {
        research: "deep",
        builder: "deep",
        monitor: "balanced",
        summary: "quick",
        review: "balanced"
      }
    },
    profiles,
    machines: [makeMachine("pc", "local"), makeMachine("dev-intern-02", "remote"), makeMachine("dev-intern-01", "remote")],
    projects: [],
    conversations: [],
    tasks: []
  };
}

function makeLiveContext(identities: IdentitySnapshot[]): LiveContext {
  return {
    projects: [],
    conversations: [],
    runtimeTasks: [],
    codexSessions: [],
    identities,
    scannedAt: new Date().toISOString()
  };
}

function makeRequest(overrides: Partial<LaunchRequest> = {}): LaunchRequest {
  return {
    label: "Routing test",
    taskKind: "research",
    difficulty: "medium",
    machineId: "dev-intern-02",
    projectId: "codex-subagent-control-plane",
    conversationId: "pc-subagent-system-20260317",
    taskId: "route-smoke",
    ...overrides
  };
}

test("weighted multi-account selection chooses the strongest healthy profile", () => {
  const profiles = [
    makeProfile("current-session", { allowSelection: false, credit: { remaining: 1, reserveFloor: 0.1 } }),
    makeProfile("slot-2", { credit: { remaining: 4, reserveFloor: 0.1 }, routingWeight: 2 })
  ];
  const route = selectRoute({
    config: makeConfig(profiles, true),
    profiles,
    liveContext: makeLiveContext([
      makeIdentity("dev-intern-02", "current-session", "acct-1", { sameAsPinned: true }),
      makeIdentity("dev-intern-02", "slot-2", "acct-2", { sameAsPinned: false })
    ]),
    request: makeRequest(),
    taskId: "route-smoke"
  });

  assert.equal(route.profileId, "slot-2");
  assert.match(route.rationale.join(" "), /selection=weighted/);
});

test("explicit selection works even when automatic multi-account is off", () => {
  const profiles = [
    makeProfile("current-session", { allowSelection: false }),
    makeProfile("slot-2", { allowSelection: true, credit: { remaining: 2, reserveFloor: 0.1 } })
  ];
  const route = selectRoute({
    config: makeConfig(profiles, false),
    profiles,
    liveContext: makeLiveContext([
      makeIdentity("dev-intern-02", "current-session", "acct-1", { sameAsPinned: true }),
      makeIdentity("dev-intern-02", "slot-2", "acct-2", { sameAsPinned: false })
    ]),
    request: makeRequest({ profileId: "slot-2" }),
    taskId: "route-smoke"
  });

  assert.equal(route.profileId, "slot-2");
  assert.match(route.rationale.join(" "), /selection=explicit:slot-2/);
});

test("task lock overrides weighted routing for follow-up launches", () => {
  const profiles = [
    makeProfile("current-session", { allowSelection: false, credit: { remaining: 1, reserveFloor: 0.1 } }),
    makeProfile("slot-2", { credit: { remaining: 8, reserveFloor: 0.1 }, routingWeight: 3 })
  ];
  const route = selectRoute({
    config: makeConfig(profiles, true),
    profiles,
    liveContext: makeLiveContext([
      makeIdentity("dev-intern-02", "current-session", "acct-1", { sameAsPinned: true }),
      makeIdentity("dev-intern-02", "slot-2", "acct-2", { sameAsPinned: false })
    ]),
    request: makeRequest(),
    taskId: "route-smoke",
    lockedProfileId: "current-session"
  });

  assert.equal(route.profileId, "current-session");
  assert.match(route.rationale.join(" "), /selection=task-lock:current-session/);
});

test("unavailable slots are skipped instead of breaking routing", () => {
  const profiles = [
    makeProfile("current-session", { allowSelection: false, credit: { remaining: 1, reserveFloor: 0.1 } }),
    makeProfile("slot-2", { credit: { remaining: 10, reserveFloor: 0.1 } })
  ];
  const route = selectRoute({
    config: makeConfig(profiles, true),
    profiles,
    liveContext: makeLiveContext([
      makeIdentity("dev-intern-02", "current-session", "acct-1", { sameAsPinned: true }),
      makeIdentity("dev-intern-02", "slot-2", "", {
        available: false,
        verified: false,
        sameAsPinned: false,
        issues: ["auth.json missing"]
      })
    ]),
    request: makeRequest(),
    taskId: "route-smoke"
  });

  assert.equal(route.profileId, "current-session");
});

test("profiles with cross-machine account drift are rejected", () => {
  const profiles = [makeProfile("slot-2", { credit: { remaining: 4, reserveFloor: 0.1 } })];
  assert.throws(
    () =>
      selectRoute({
        config: makeConfig(profiles, true),
        profiles,
        liveContext: makeLiveContext([
          makeIdentity("dev-intern-02", "slot-2", "acct-2"),
          makeIdentity("dev-intern-01", "slot-2", "acct-3")
        ]),
        request: makeRequest({ profileId: "slot-2" }),
        taskId: "route-smoke"
      }),
    /profile-account-mismatch/
  );
});
