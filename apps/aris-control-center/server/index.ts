import express from "express";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { WebSocketServer } from "ws";
import { ControlPlane } from "./controller.js";
import { ArisOps } from "./aris.js";
import type { LaunchRequest } from "./shared.js";

const serverDir = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(serverDir, "..");
const configPath = process.env.ARIS_CONFIG || path.join(appRoot, "config", "aris-control-center.example.json");
const controlPlane = new ControlPlane(configPath);
const arisOps = new ArisOps(appRoot, controlPlane);

const app = express();
app.use(express.json({ limit: "2mb" }));

app.get("/api/snapshot", (_req, res) => {
  res.json(controlPlane.snapshot());
});

app.get("/api/aris/dashboard", (_req, res) => {
  res.json(arisOps.dashboard());
});

app.post("/api/refresh-context", (_req, res) => {
  res.json(controlPlane.refreshContext());
});

app.post("/api/route-preview", (req, res) => {
  try {
    res.json(controlPlane.previewRoute(req.body as LaunchRequest));
  } catch (error) {
    res.status(400).json({ error: error instanceof Error ? error.message : String(error) });
  }
});

app.post("/api/launch", (req, res) => {
  const body = req.body as Partial<LaunchRequest>;
  if (!body.label || !body.taskKind || !body.difficulty || !body.machineId || !body.projectId || !body.conversationId) {
    res.status(400).json({ error: "Missing required launch fields" });
    return;
  }
  try {
    const agent = controlPlane.launch(body as LaunchRequest);
    res.json(agent);
  } catch (error) {
    res.status(400).json({ error: error instanceof Error ? error.message : String(error) });
  }
});

app.post("/api/launch-template/:taskId", (req, res) => {
  const template = controlPlane.config.tasks.find((item) => item.id === req.params.taskId);
  if (!template) {
    res.status(404).json({ error: "Task template not found" });
    return;
  }
  try {
    const agent = controlPlane.launch({
      taskTemplateId: template.id,
      label: template.label,
      taskKind: template.taskKind,
      difficulty: template.difficulty,
      machineId: template.machineId,
      projectId: template.projectId,
      conversationId: template.conversationId,
      search: template.search
    });
    res.json(agent);
  } catch (error) {
    res.status(400).json({ error: error instanceof Error ? error.message : String(error) });
  }
});

app.post("/api/aris/tmux", (req, res) => {
  try {
    res.json(arisOps.createTmuxInstance(req.body));
  } catch (error) {
    res.status(400).json({ error: error instanceof Error ? error.message : String(error) });
  }
});

app.post("/api/aris/reflections", (req, res) => {
  try {
    res.json(arisOps.recordReflection(req.body));
  } catch (error) {
    res.status(400).json({ error: error instanceof Error ? error.message : String(error) });
  }
});

app.post("/api/aris/deep-research-plan", (req, res) => {
  try {
    res.json(arisOps.generateDeepResearchPlan(req.body));
  } catch (error) {
    res.status(400).json({ error: error instanceof Error ? error.message : String(error) });
  }
});

app.post("/api/agents/:agentId/stop", (req, res) => {
  const agent = controlPlane.stopAgent(req.params.agentId);
  if (!agent) {
    res.status(404).json({ error: "Agent not found" });
    return;
  }
  res.json(agent);
});

app.get("/api/agents/:agentId/log", (req, res) => {
  const lines = Number(req.query.lines ?? 120);
  res.type("text/plain").send(controlPlane.tail(req.params.agentId, lines));
});

const webDist = path.join(appRoot, "web", "dist");
if (process.env.NODE_ENV === "production") {
  app.use(express.static(webDist));
  app.get("*", (_req, res) => {
    res.sendFile(path.join(webDist, "index.html"));
  });
}

const server = http.createServer(app);
const ws = new WebSocketServer({ server, path: "/ws" });

ws.on("connection", (socket) => {
  controlPlane.connect(socket);
});

const port = Number(process.env.PORT ?? 47951);
server.listen(port, "127.0.0.1", () => {
  controlPlane.startScheduler();
  console.log(`ARIS control center listening on http://127.0.0.1:${port}`);
});
