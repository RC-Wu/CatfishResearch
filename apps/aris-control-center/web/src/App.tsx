import { startTransition, useDeferredValue, useEffect, useState } from "react";

type ViewMode = "operations" | "router" | "memory" | "research";

type Dashboard = {
  generatedAt: string;
  label: string;
  snapshot: {
    config: {
      machines: Array<{ id: string; label: string; launcher: string }>;
      profiles: Array<{ id: string; label: string; routingWeight: number }>;
    };
    state: {
      agents: Array<{
        id: string;
        label: string;
        state: string;
        machineId: string;
        profileId: string;
        model: string;
        reasoningEffort: string;
        output?: string;
        error?: string;
        createdAt: string;
      }>;
    };
  };
  tmuxInstances: Array<Record<string, unknown>>;
  reflections: Array<{ title: string; preview: string; filePath: string }>;
  proposals: Array<{ title: string; preview: string; filePath: string }>;
  researchPlans: Array<Record<string, unknown>>;
  routeMatrix: Array<{ machineId: string; entries: Array<{ taskKind: string; difficulty: string; route: Record<string, unknown> }> }>;
  relays: Array<{ id: string; label: string; provider: string; baseUrl: string; status: string }>;
  knowledgeSpaces: Array<{ label: string; count: number; path: string }>;
};

const emptyDashboard: Dashboard = {
  generatedAt: "",
  label: "ARIS Ops Atlas",
  snapshot: { config: { machines: [], profiles: [] }, state: { agents: [] } },
  tmuxInstances: [],
  reflections: [],
  proposals: [],
  researchPlans: [],
  routeMatrix: [],
  relays: [],
  knowledgeSpaces: []
};

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(await response.text());
  return (await response.json()) as T;
}

async function postJson<T>(url: string, body: unknown): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!response.ok) throw new Error(await response.text());
  return (await response.json()) as T;
}

function formatTime(value: string) {
  return value ? new Date(value).toLocaleString() : "--";
}

export function App() {
  const [dashboard, setDashboard] = useState<Dashboard>(emptyDashboard);
  const [viewMode, setViewMode] = useState<ViewMode>("operations");
  const [errorMessage, setErrorMessage] = useState("");
  const [selectedAgentId, setSelectedAgentId] = useState("");
  const [launchLabel, setLaunchLabel] = useState("ARIS ad hoc task");
  const [launchPrompt, setLaunchPrompt] = useState("Summarize the current state and propose the next move.");
  const [launchMachine, setLaunchMachine] = useState("dev-intern-02");
  const [tmuxLabel, setTmuxLabel] = useState("ARIS Main");
  const [tmuxMachine, setTmuxMachine] = useState("dev-intern-02");
  const [reflectionTitle, setReflectionTitle] = useState("ARIS reflection");
  const [reflectionObservation, setReflectionObservation] = useState("Observed runtime pattern.");
  const [reflectionUpgrade, setReflectionUpgrade] = useState("Promote stable lessons into the upgrade layer.");
  const [researchTopic, setResearchTopic] = useState("mesh token compression for ARIS");
  const [researchAgents, setResearchAgents] = useState("72");
  const deferredReflections = useDeferredValue(dashboard.reflections);

  useEffect(() => {
    void refreshDashboard();
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => void refreshDashboard(), 10000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws`);
    socket.onmessage = () => startTransition(() => void refreshDashboard());
    return () => socket.close();
  }, []);

  const agents = dashboard.snapshot.state.agents;
  const selectedAgent = agents.find((agent) => agent.id === selectedAgentId) ?? agents[0];

  useEffect(() => {
    if (!selectedAgentId && agents.length) setSelectedAgentId(agents[0].id);
    if (selectedAgentId && !agents.some((agent) => agent.id === selectedAgentId)) setSelectedAgentId(agents[0]?.id || "");
  }, [agents, selectedAgentId]);

  async function refreshDashboard() {
    try {
      setErrorMessage("");
      setDashboard(await getJson<Dashboard>("/api/aris/dashboard"));
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : String(error));
    }
  }

  async function launchAgent() {
    await postJson("/api/launch", {
      label: launchLabel,
      prompt: launchPrompt,
      taskKind: "research",
      difficulty: "medium",
      machineId: launchMachine,
      projectId: "pua_research",
      conversationId: "aris-control-center",
      search: true
    });
    await refreshDashboard();
  }

  async function createTmux() {
    await postJson("/api/aris/tmux", { label: tmuxLabel, machineId: tmuxMachine });
    await refreshDashboard();
  }

  async function reflect() {
    await postJson("/api/aris/reflections", {
      title: reflectionTitle,
      scope: "cross-project",
      projectId: "pua_research",
      observation: reflectionObservation,
      lesson: reflectionObservation,
      upgradeProposal: reflectionUpgrade
    });
    await refreshDashboard();
  }

  async function createResearchPlan() {
    await postJson("/api/aris/deep-research-plan", {
      topic: researchTopic,
      agentCount: Number(researchAgents),
      machineId: "dev-intern-02",
      difficulty: "high"
    });
    await refreshDashboard();
  }

  return (
    <div className="shell">
      <header className="hero">
        <div className="hero-copy">
          <p className="eyebrow">ARIS Control Center</p>
          <h1>{dashboard.label}</h1>
          <p className="hero-text">把 donor 控制平面、detached remote workers、tmux session 描述、反思升级和 60+ 深研规划压进一个能真实运营的 ARIS 面板。</p>
        </div>
        <div className="hero-grid">
          <article className="metric"><span>Agents</span><strong>{agents.length}</strong><small>{agents.filter((agent) => agent.state === "running" || agent.state === "starting").length} active</small></article>
          <article className="metric"><span>TMUX</span><strong>{dashboard.tmuxInstances.length}</strong><small>one instance, one session</small></article>
          <article className="metric"><span>Memory</span><strong>{dashboard.reflections.length}</strong><small>{dashboard.proposals.length} upgrade notes</small></article>
          <article className="metric"><span>Swarm</span><strong>{dashboard.researchPlans.length}</strong><small>latest {String(dashboard.researchPlans[0]?.targetAgents ?? 0)} agents</small></article>
        </div>
      </header>

      <div className="tabs">
        {(["operations", "router", "memory", "research"] as ViewMode[]).map((mode) => (
          <button key={mode} type="button" className={viewMode === mode ? "tab active" : "tab"} onClick={() => setViewMode(mode)}>
            {mode}
          </button>
        ))}
        <button type="button" className="tab ghost" onClick={() => void refreshDashboard()}>refresh</button>
      </div>

      {errorMessage ? <div className="banner">{errorMessage}</div> : null}

      <main className="layout">
        <aside className="rail card">
          <section>
            <div className="section-head"><h2>Machines</h2><span>{formatTime(dashboard.generatedAt)}</span></div>
            <div className="stack">
              {dashboard.snapshot.config.machines.map((machine) => (
                <article key={machine.id} className="mini-card"><strong>{machine.label}</strong><small>{machine.id}</small><small>{machine.launcher}</small></article>
              ))}
            </div>
          </section>
          <section>
            <div className="section-head"><h2>Profiles</h2><span>{dashboard.snapshot.config.profiles.length}</span></div>
            <div className="stack">
              {dashboard.snapshot.config.profiles.map((profile) => (
                <article key={profile.id} className="mini-card"><strong>{profile.label}</strong><small>{profile.id}</small><small>weight {profile.routingWeight}</small></article>
              ))}
            </div>
          </section>
        </aside>

        <section className="main">
          {viewMode === "operations" ? (
            <>
              <section className="card">
                <div className="section-head"><h2>Launch Agent</h2><span>Codex runtime</span></div>
                <div className="form-grid">
                  <label>Label<input value={launchLabel} onChange={(event) => setLaunchLabel(event.target.value)} /></label>
                  <label>Machine<select value={launchMachine} onChange={(event) => setLaunchMachine(event.target.value)}>{dashboard.snapshot.config.machines.map((machine) => <option key={machine.id} value={machine.id}>{machine.label}</option>)}</select></label>
                  <label className="full">Prompt<textarea rows={4} value={launchPrompt} onChange={(event) => setLaunchPrompt(event.target.value)} /></label>
                </div>
                <button type="button" className="primary" onClick={() => void launchAgent()}>launch</button>
              </section>

              <section className="grid">
                <article className="card">
                  <div className="section-head"><h2>Recent Agents</h2><span>{agents.length}</span></div>
                  <div className="stack">
                    {agents.slice(0, 8).map((agent) => (
                      <button key={agent.id} type="button" className={selectedAgent?.id === agent.id ? "agent-card active" : "agent-card"} onClick={() => setSelectedAgentId(agent.id)}>
                        <strong>{agent.label}</strong>
                        <small>{agent.machineId} / {agent.profileId}</small>
                        <small>{agent.model} / {agent.reasoningEffort}</small>
                        <span className={`pill state-${agent.state}`}>{agent.state}</span>
                      </button>
                    ))}
                  </div>
                </article>
                <article className="card">
                  <div className="section-head"><h2>Inspector</h2><span>{selectedAgent?.state || "idle"}</span></div>
                  {selectedAgent ? (
                    <div className="stack">
                      <article className="mini-card"><strong>{selectedAgent.label}</strong><small>{formatTime(selectedAgent.createdAt)}</small><small>{selectedAgent.machineId}</small></article>
                      <article className="text-card"><h3>Output</h3><p>{selectedAgent.output || selectedAgent.error || "No output yet."}</p></article>
                    </div>
                  ) : <p className="empty">No agent selected.</p>}
                </article>
              </section>

              <section className="card">
                <div className="section-head"><h2>TMUX Instances</h2><span>{dashboard.tmuxInstances.length}</span></div>
                <div className="form-grid compact">
                  <label>Label<input value={tmuxLabel} onChange={(event) => setTmuxLabel(event.target.value)} /></label>
                  <label>Machine<select value={tmuxMachine} onChange={(event) => setTmuxMachine(event.target.value)}>{dashboard.snapshot.config.machines.map((machine) => <option key={machine.id} value={machine.id}>{machine.label}</option>)}</select></label>
                </div>
                <button type="button" className="primary" onClick={() => void createTmux()}>create tmux descriptor</button>
                <div className="stack">
                  {dashboard.tmuxInstances.slice(0, 6).map((instance) => (
                    <article key={String(instance.id)} className="mini-card"><strong>{String(instance.label)}</strong><small>{String(instance.machineId)}</small><small>{String(instance.attachCommand)}</small></article>
                  ))}
                </div>
              </section>
            </>
          ) : null}

          {viewMode === "router" ? (
            <section className="grid">
              <article className="card">
                <div className="section-head"><h2>Relays</h2><span>{dashboard.relays.length}</span></div>
                <div className="stack">
                  {dashboard.relays.map((relay) => (
                    <article key={relay.id} className="mini-card"><strong>{relay.label}</strong><small>{relay.provider}</small><small>{relay.baseUrl}</small><span className={`pill ${relay.status === "ready" ? "state-running" : "state-failed"}`}>{relay.status}</span></article>
                  ))}
                </div>
              </article>
              <article className="card">
                <div className="section-head"><h2>Route Matrix</h2><span>difficulty-aware</span></div>
                <div className="stack">
                  {dashboard.routeMatrix.map((row) => (
                    <article key={row.machineId} className="matrix-card">
                      <strong>{row.machineId}</strong>
                      <div className="matrix-grid">
                        {row.entries.map((entry) => (
                          <div key={`${row.machineId}-${entry.taskKind}-${entry.difficulty}`} className="matrix-cell">
                            <span>{entry.taskKind}</span>
                            <strong>{entry.difficulty}</strong>
                            <small>{String(entry.route.profileId || entry.route.error || "--")}</small>
                            <small>{String(entry.route.model || "")}</small>
                          </div>
                        ))}
                      </div>
                    </article>
                  ))}
                </div>
              </article>
            </section>
          ) : null}

          {viewMode === "memory" ? (
            <>
              <section className="grid">
                <article className="card">
                  <div className="section-head"><h2>Knowledge Spaces</h2><span>{dashboard.knowledgeSpaces.length}</span></div>
                  <div className="stack">
                    {dashboard.knowledgeSpaces.map((space) => (
                      <article key={space.label} className="mini-card"><strong>{space.label}</strong><small>{space.count} notes</small><small>{space.path}</small></article>
                    ))}
                  </div>
                </article>
                <article className="card">
                  <div className="section-head"><h2>Record Reflection</h2><span>self-upgrade</span></div>
                  <div className="form-grid">
                    <label>Title<input value={reflectionTitle} onChange={(event) => setReflectionTitle(event.target.value)} /></label>
                    <label className="full">Observation<textarea rows={3} value={reflectionObservation} onChange={(event) => setReflectionObservation(event.target.value)} /></label>
                    <label className="full">Upgrade<textarea rows={3} value={reflectionUpgrade} onChange={(event) => setReflectionUpgrade(event.target.value)} /></label>
                  </div>
                  <button type="button" className="primary" onClick={() => void reflect()}>store reflection</button>
                </article>
              </section>
              <section className="grid">
                <article className="card">
                  <div className="section-head"><h2>Reflections</h2><span>{dashboard.reflections.length}</span></div>
                  <div className="stack">
                    {deferredReflections.map((item) => <article key={item.filePath} className="text-card"><h3>{item.title}</h3><p>{item.preview}</p></article>)}
                  </div>
                </article>
                <article className="card">
                  <div className="section-head"><h2>Upgrade Proposals</h2><span>{dashboard.proposals.length}</span></div>
                  <div className="stack">
                    {dashboard.proposals.map((item) => <article key={item.filePath} className="text-card"><h3>{item.title}</h3><p>{item.preview}</p></article>)}
                  </div>
                </article>
              </section>
            </>
          ) : null}

          {viewMode === "research" ? (
            <>
              <section className="card">
                <div className="section-head"><h2>Deep Research Planner</h2><span>60+ shard swarm</span></div>
                <div className="form-grid compact">
                  <label className="full">Topic<input value={researchTopic} onChange={(event) => setResearchTopic(event.target.value)} /></label>
                  <label>Agents<input value={researchAgents} onChange={(event) => setResearchAgents(event.target.value)} /></label>
                </div>
                <button type="button" className="primary" onClick={() => void createResearchPlan()}>build plan</button>
              </section>
              <section className="card">
                <div className="section-head"><h2>Recent Plans</h2><span>{dashboard.researchPlans.length}</span></div>
                <div className="stack">
                  {dashboard.researchPlans.map((plan) => <article key={String(plan.id)} className="text-card"><h3>{String(plan.topic)}</h3><p>agents: {String(plan.targetAgents)} | machine: {String(plan.targetMachine)}</p><p>{JSON.stringify((plan.shards as Array<unknown> | undefined)?.slice(0, 2) ?? [], null, 2)}</p></article>)}
                </div>
              </section>
            </>
          ) : null}
        </section>
      </main>
    </div>
  );
}
