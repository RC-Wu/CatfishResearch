# CatfishResearch

[English](README.md) | 中文

CatfishResearch 是这个仓库当前的身份。它保留 ARIS 的工作流血统，但主线已经转到 Catfish：一个文档优先、文件可回放的研究控制平面，包含小型 runtime core、provider routing、后端优先的 control center，以及清晰标注 provenance 的整套文档。

如果某个能力只是写在文档里，它就按 contract 或 roadmap 处理。只有真的落到代码里的能力，README 才会指向对应文件。

## 当前已有内容

- `docs/catfish/` 保存 Catfish 架构、路由、control center 和 roadmap 文档。
- `tools/catfish_runtime.py`、`tools/catfish_route_core.py`、`tools/catfish_route_eval.py`、`tools/catfish_remote_dispatch.py`、`tools/codex_route_preview.py`、`tools/cc_switch_bridge.py` 提供 runtime 和 control-plane 辅助能力。
- `apps/catfish-control-center/` 是当前的 control-center CLI 和 dashboard 实现。
- `assets/router/` 保存 provider registry、provider health snapshot 和 capability ledger。
- `skills/skills-codex/` 保留 Codex-native skill 树，同时 upstream `skills/` 仍然存在。

## 当前 Control Center 状态

control center 不是 web app，而是一个后端优先的 CLI，可以渲染 materialized snapshot，也可以读取 live `state-root`。

支持的输入：

- `--snapshot`：读取 materialized JSON snapshot。
- `--state-root`：读取 Catfish live state tree，包含 `system/` 和 `projects/`。

支持的视图包括：

- `dashboard`
- `projects`
- `stage-competitions`
- `pending-reviews`
- `provider-status`
- `recent-launches`
- `capability-summaries`
- `diversity-metrics`
- `recent-events`

示例：

```bash
python apps/catfish-control-center/main.py \
  --state-root /path/to/catfish-state \
  --view dashboard
```

live state 的说明见 [`docs/catfish/CONTROL_CENTER_LIVE_20260325.md`](docs/catfish/CONTROL_CENTER_LIVE_20260325.md)。原始 skeleton 仍保留在 [`docs/catfish/CONTROL_CENTER_20260325.md`](docs/catfish/CONTROL_CENTER_20260325.md) 作为历史参考。

## 生产安全目标

CatfishResearch 的目标不是“先做大再说”，而是先让系统可检查、可回放、可追溯。

- 优先使用文件化 state，而不是隐藏式内存状态。
- 竞争和评分保持 parent-owned，避免 child 自己给自己打分。
- provider 选择必须经过 registry、health、quota 和 capability 数据的约束。
- control center 读取的 contract 要和 runtime / dispatcher 写入的 contract 一致。
- 仓库不会假装已经有一个持久化服务、数据库或 web UI，除非它真的存在。

这些限制是当前基线，不是以后再补的“理想化约束”。

## onboarding 方向

像 3d-edit 这样的下游工作，应该按 Catfish project 的方式接入，而不是单独造一条特例路径：

1. 先定义 Catfish manifest 里的 project 边界。
2. 再把 runtime snapshot 落到 `state-root` 下面。
3. 让 control center 读取 runtime 和 dispatcher 已经认识的同一套文件。
4. 只有当文档真的描述了现实现状时，才把项目特定说明加到 `docs/catfish/`。

这样 onboarding 才是统一的，不会过早分叉出一条特殊 runtime。

## provenance

CatfishResearch 继承 ARIS 工作流血统，但它不是 ARIS 的脚注。

- ARIS 是上游 workflow 和历史 provenance。
- CatfishResearch 是这个 worktree 里使用的仓库身份。
- 合并记录保存在 [`docs/catfish/MERGE_ARIS_20260325.md`](docs/catfish/MERGE_ARIS_20260325.md)。
- 旧的 ARIS-oriented README 保存在 [`docs/legacy/README_ARIS_20260328.md`](docs/legacy/README_ARIS_20260328.md)。

## 从这里开始

- [`docs/catfish/INDEX_20260325.md`](docs/catfish/INDEX_20260325.md)
- [`docs/catfish/ARCHITECTURE_20260325.md`](docs/catfish/ARCHITECTURE_20260325.md)
- [`docs/catfish/RUNTIME_ENGINE_20260325.md`](docs/catfish/RUNTIME_ENGINE_20260325.md)
- [`docs/catfish/PROVIDER_ROUTING_20260325.md`](docs/catfish/PROVIDER_ROUTING_20260325.md)
- [`docs/catfish/REMOTE_DISPATCH_20260325.md`](docs/catfish/REMOTE_DISPATCH_20260325.md)
- [`docs/catfish/ROADMAP_20260325.md`](docs/catfish/ROADMAP_20260325.md)
- [`docs/catfish/CONTROL_CENTER_LIVE_20260325.md`](docs/catfish/CONTROL_CENTER_LIVE_20260325.md)

如果你要看 ARIS 时代的工作流叙事，请直接看 legacy README，而不是主 README。
