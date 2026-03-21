import type {
  ControlPlaneConfig,
  IdentitySnapshot,
  LaunchRequest,
  LiveContext,
  ProfileConfig,
  RoutedSelection,
  TaskTemplate
} from "./shared.js";

function describeCandidate(profile: ProfileConfig, issues: string[]) {
  return `${profile.id}[${issues.join(", ")}]`;
}

function profileSnapshots(liveContext: LiveContext, profileId: string) {
  return liveContext.identities.filter((item) => item.profileId === profileId);
}

function profileIsConsistent(liveContext: LiveContext, profileId: string) {
  const accountKeys = new Set(
    profileSnapshots(liveContext, profileId)
      .filter((item) => item.available && item.verified && item.accountKey)
      .map((item) => item.accountKey)
  );
  return accountKeys.size <= 1;
}

function identityForMachine(liveContext: LiveContext, machineId: string, profileId: string) {
  return liveContext.identities.find((item) => item.machineId === machineId && item.profileId === profileId);
}

function scoreProfile(profile: ProfileConfig) {
  return Number(profile.credit.remaining) * Math.max(Number(profile.routingWeight) || 0, 0.01);
}

function candidateIssues(profile: ProfileConfig, identity: IdentitySnapshot | undefined, liveContext: LiveContext) {
  const issues: string[] = [];
  if (!identity) {
    issues.push("missing-identity");
  } else {
    if (!identity.available) {
      issues.push(...(identity.issues.length ? identity.issues : ["auth-unavailable"]));
    } else if (!identity.verified) {
      issues.push(...(identity.issues.length ? identity.issues : ["identity-unverified"]));
    } else if (identity.issues.length) {
      issues.push(...identity.issues);
    }
  }
  if (profile.credit.remaining <= profile.credit.reserveFloor) {
    issues.push(`credit-below-reserve:${profile.credit.remaining}`);
  }
  if (!profileIsConsistent(liveContext, profile.id)) {
    issues.push("profile-account-mismatch");
  }
  return [...new Set(issues)];
}

export function makeTaskRuntimeKey(projectId: string, conversationId: string, taskId: string) {
  return `${projectId}::${conversationId}::${taskId}`;
}

export function selectRoute(options: {
  config: ControlPlaneConfig;
  liveContext: LiveContext;
  profiles: ProfileConfig[];
  request: LaunchRequest;
  template?: TaskTemplate;
  taskId: string;
  lockedProfileId?: string;
}): RoutedSelection {
  const { config, liveContext, profiles, request, template, taskId, lockedProfileId } = options;
  const machineId = request.machineId || template?.machineId || "pc";
  const machineProfiles = profiles.filter((item) => item.enabled && item.machineIds.includes(machineId));

  if (!machineProfiles.length) {
    throw new Error(`No enabled profile can launch on ${machineId}`);
  }

  const candidates = machineProfiles.map((profile) => {
    const identity = identityForMachine(liveContext, machineId, profile.id);
    return {
      profile,
      identity,
      issues: candidateIssues(profile, identity, liveContext),
      score: scoreProfile(profile)
    };
  });

  const healthyCandidates = candidates.filter((candidate) => candidate.issues.length === 0);
  const pinnedCandidate = candidates.find((candidate) => candidate.profile.id === config.routing.pinProfileId);
  const explicitCandidate = request.profileId
    ? candidates.find((candidate) => candidate.profile.id === request.profileId)
    : undefined;
  const lockedCandidate = lockedProfileId
    ? candidates.find((candidate) => candidate.profile.id === lockedProfileId)
    : undefined;

  let chosen = healthyCandidates[0];
  const rationale: string[] = [
    `routing.mode=${config.routing.mode}`,
    `task.id=${taskId}`,
    `machine=${machineId}`
  ];

  if (lockedProfileId) {
    rationale.push(`selection=task-lock:${lockedProfileId}`);
    if (!lockedCandidate) {
      throw new Error(`Task ${taskId} is locked to profile ${lockedProfileId}, but that profile cannot run on ${machineId}`);
    }
    if (lockedCandidate.issues.length) {
      throw new Error(`Task ${taskId} is locked to unhealthy profile ${describeCandidate(lockedCandidate.profile, lockedCandidate.issues)}`);
    }
    chosen = lockedCandidate;
  } else if (request.profileId) {
    if (!explicitCandidate) {
      throw new Error(`Requested profile ${request.profileId} cannot launch on ${machineId}`);
    }
    rationale.push(`selection=explicit:${explicitCandidate.profile.id}`);
    if (
      explicitCandidate.profile.id !== config.routing.pinProfileId &&
      !explicitCandidate.profile.allowSelection
    ) {
      throw new Error(`Profile ${explicitCandidate.profile.id} is not operator-selectable`);
    }
    if (explicitCandidate.issues.length) {
      throw new Error(`Profile ${describeCandidate(explicitCandidate.profile, explicitCandidate.issues)} is not launchable`);
    }
    chosen = explicitCandidate;
  } else if (config.routing.allowMultiAccount) {
    rationale.push("selection=weighted");
    chosen = [...healthyCandidates].sort((left, right) => right.score - left.score)[0];
  } else {
    rationale.push(`selection=pinned:${config.routing.pinProfileId}`);
    if (!pinnedCandidate) {
      throw new Error(`Pinned profile ${config.routing.pinProfileId} cannot launch on ${machineId}`);
    }
    if (pinnedCandidate.issues.length) {
      throw new Error(`Pinned profile ${describeCandidate(pinnedCandidate.profile, pinnedCandidate.issues)} is not launchable`);
    }
    chosen = pinnedCandidate;
  }

  if (!chosen) {
    const details = candidates.map((candidate) => describeCandidate(candidate.profile, candidate.issues.length ? candidate.issues : ["ok"]));
    throw new Error(`No healthy profile can launch on ${machineId}: ${details.join("; ")}`);
  }

  const tierId = config.routing.taskKindTierMap[request.taskKind] || config.routing.difficultyTierMap[request.difficulty];
  const tier = chosen.profile.modelTiers[tierId] ?? Object.values(chosen.profile.modelTiers)[0];
  const browserMode = request.browserMode || template?.browserMode || tier.browserMode || "none";
  const search = request.search ?? template?.search ?? tier.search ?? browserMode === "codex-search";

  rationale.push(
    `profile=${chosen.profile.id}`,
    `credit.remaining=${chosen.profile.credit.remaining}`,
    `routing.score=${chosen.score.toFixed(3)}`,
    `tier=${tierId}`,
    `browserMode=${browserMode}`
  );

  return {
    profileId: chosen.profile.id,
    machineId,
    tierId,
    model: tier.model,
    reasoningEffort: tier.reasoningEffort,
    search,
    browserMode,
    rationale
  };
}
