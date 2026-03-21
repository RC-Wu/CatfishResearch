$ErrorActionPreference = "Stop"
$ProjectRoot = "F:\InformationAndCourses\Code\codex-subagent-control-plane"

param(
  [Parameter(Mandatory = $true)][string]$Label,
  [Parameter(Mandatory = $true)][string]$Prompt,
  [string]$TaskLabel = "Remote Ad Hoc Task",
  [string]$TaskKind = "research",
  [string]$Difficulty = "medium",
  [string]$Machine = "dev-intern-02",
  [string]$Project = "codex-subagent-control-plane",
  [string]$Conversation = "pc-subagent-system-20260317",
  [switch]$Search
)

$taskId = ($TaskLabel.ToLower() -replace "[^a-z0-9]+", "-").Trim("-")
$args = @(
  "tsx",
  "scripts/control_plane_cli.ts",
  "launch",
  "--label", $Label,
  "--prompt", $Prompt,
  "--task-label", $TaskLabel,
  "--task-id", $taskId,
  "--task-kind", $TaskKind,
  "--difficulty", $Difficulty,
  "--machine", $Machine,
  "--project", $Project,
  "--conversation", $Conversation
)

if ($Search) {
  $args += "--search"
}

& "npx.cmd" @args
