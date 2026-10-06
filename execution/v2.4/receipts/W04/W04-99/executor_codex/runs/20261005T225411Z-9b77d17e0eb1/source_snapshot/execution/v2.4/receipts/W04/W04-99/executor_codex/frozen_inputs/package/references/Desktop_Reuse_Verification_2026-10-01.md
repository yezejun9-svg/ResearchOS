# Desktop 前端复用核实

版本：2.4.0。核查日期：2026-10-01，Asia/Shanghai。证据等级：`SOURCE_REVIEWED`。本轮读取固定版本源码、仓库树、许可和官方产品资料；没有安装候选、启动桌面应用、调用真实模型或证明 ResearchOS 集成通过。它是选型证据，施工合同见 [19_DESKTOP_IMPLEMENTATION_BLUEPRINT.md](../19_DESKTOP_IMPLEMENTATION_BLUEPRINT.md)。

## 1. 结论与范围

只保留两条前端路线：首选 Mu 已有 Native Desktop 会话界面与 Electron 壳；其资格门失败后，备选 Craft Agents 的 Electron/React 壳与组件。AionUi 是 Mu Desktop 已保留的来源，不再增加第三套应用。前端来源变化不改变 ResearchOS 现有 Go/SQLite 领域权威、调度器和验收权威。

旧 `CLI_Desktop_Local_Inventory.json` 中的 `/workspace/scratch/...` 是先前执行环境的路径，本 Windows 环境没有据此确认这些源码目录仍然存在。本轮通过官方 GitHub 固定 revision 读取源码，没有把历史路径写成当前本地已安装资产。

## 2. 首选 Mu

- 仓库：[qybaihe/mu](https://github.com/qybaihe/mu)。固定 commit：`8dfebe36508ac0c2508735bb866756dab9283e74`；官方 GitHub commit 查询返回时间 `2026-09-30T04:50:58Z`。
- [根 LICENSE](https://github.com/qybaihe/mu/blob/8dfebe36508ac0c2508735bb866756dab9283e74/LICENSE) 是 MIT；[desktop/LICENSE](https://github.com/qybaihe/mu/blob/8dfebe36508ac0c2508735bb866756dab9283e74/desktop/LICENSE) 是 Apache-2.0，含 AionUi 归属。复制相应子树时保留许可、归属和修改说明；不能用根 MIT 覆盖桌面子树及第三方依赖许可。
- [desktop/package.json](https://github.com/qybaihe/mu/blob/8dfebe36508ac0c2508735bb866756dab9283e74/desktop/package.json) 为 `0.1.6`，`muAgentVersion=0.1.7`，Node 范围 `>=22 <25`。这些是源码配置，不代表本项目已经构建安装包。

下列路径均相对该固定 commit：

| 能力 | 实际核实入口 | 采用方式和限制 |
|---|---|---|
| 主会话 | `desktop/packages/desktop/src/renderer/pages/native/components/NativeConversationScreen.tsx` | 已组合消息历史、空态、失败重试、输入与工作面板；复用组件，数据改接 ResearchOS 客户端 |
| 输入/模型/队列 | 同目录 `NativeComposer.tsx`、`composer/NativeModelChip.tsx`、`composer/NativePermissionPill.tsx` | 已使用 SendBox、GoalLine、steering/follow-up 队列；模型选择与权限必须由 ResearchOS 服务核准 |
| 项目/历史 | 同目录 `NativeSiderGroup.tsx`、`NativeNewConversation.tsx`；`../hooks/useNativeConversations.ts` | 复用呈现与交互；ResearchOS 项目 ID、会话 ID、上游 sessionFile 建立显式映射 |
| 最窄前端接口 | `desktop/packages/desktop/src/renderer/pages/native/utils/nativeClient.ts` | `NativeClientContext` 注入客户端；接口有 list/create/open/request/respond/close/remove/rename/事件及目录选择。无需把每个组件改成直接 HTTP 调用 |
| 快照与增量 | `desktop/packages/desktop/src/common/kyrn/nativeBridge.ts`、`common/utils/nativeHost/` | 已有 seq、snapshot、replaced 与 reducer；ResearchOS 需补持久 cursor、命令幂等、writer_epoch 与业务事件映射 |
| 脱离 Electron 的 worker 宿主 | `desktop/packages/desktop/src/process/services/nativeHost/NativeHost.ts`、`nodeFork.ts`、`entry.ts` | NativeHost 无 Electron import；nodeFork 用 Node child_process.fork；可作为 Go supervisor 下 worker 适配的候选切口，尚未验证集成 |
| 文件差异 | `desktop/packages/desktop/src/renderer/pages/conversation/Preview/components/viewers/DiffViewer.tsx` | 路径存在；真实文件读取、基线 hash、冲突保存与回退仍须接 ResearchOS 合同 |
| 主题 | `desktop/packages/desktop/src/renderer/styles/themes/`、`renderer/utils/theme/` | 保留上游基础，映射本包设计 token，避免另写平行主题系统 |
| 构建 | `desktop/scripts/build-with-builder.js`；package 脚本 `build-win:x64`、`dist:win` | 已有 Windows 打包入口；先审阅其 postinstall/下载/原生模块与外部资源，再固定发行内容 |

最关键的一手依据：[native-host.md](https://github.com/qybaihe/mu/blob/8dfebe36508ac0c2508735bb866756dab9283e74/desktop/docs/native-host.md)、[nativeClient.ts](https://github.com/qybaihe/mu/blob/8dfebe36508ac0c2508735bb866756dab9283e74/desktop/packages/desktop/src/renderer/pages/native/utils/nativeClient.ts)、[NativeHost.ts](https://github.com/qybaihe/mu/blob/8dfebe36508ac0c2508735bb866756dab9283e74/desktop/packages/desktop/src/process/services/nativeHost/NativeHost.ts)、[nodeFork.ts](https://github.com/qybaihe/mu/blob/8dfebe36508ac0c2508735bb866756dab9283e74/desktop/packages/desktop/src/process/services/nativeHost/nodeFork.ts)。

上游文档明确说明：Native 路径绕过 AionCore/ACP；旧会话仍可能留在 classic 路径；打包内 Mu 太旧时 auto 模式会回退；WebUI 不启用这套原生会话界面。这些事实要求 W01 验证构建出的实际入口，ResearchOS 不能以“仓库有 NativeHost”为理由宣称已形成唯一核心或手机共享同一界面。

## 3. 唯一备选 Craft Agents

- 官方仓库现为 [craft-ai-agents/craft-agents-oss](https://github.com/craft-ai-agents/craft-agents-oss)；历史 `lukilabs/craft-agents-oss` 地址会重定向。
- 本轮固定 commit：`73bd9c2a3573158bea880984eb8d5fdb41e0cac2`，官方 GitHub commit 返回时间 `2026-09-30T04:22:07Z`。固定源码中的 Electron package 为 `0.14.0`。
- [LICENSE](https://github.com/craft-ai-agents/craft-agents-oss/blob/73bd9c2a3573158bea880984eb8d5fdb41e0cac2/LICENSE) 为 Apache-2.0；[NOTICE](https://github.com/craft-ai-agents/craft-agents-oss/blob/73bd9c2a3573158bea880984eb8d5fdb41e0cac2/NOTICE) 指明 Claude Agent SDK 另受 Anthropic 条款约束；不能把整套依赖视为同一许可。
- [TRADEMARK.md](https://github.com/craft-ai-agents/craft-agents-oss/blob/73bd9c2a3573158bea880984eb8d5fdb41e0cac2/TRADEMARK.md) 要求 fork 使用不同名称、图标、bundle identifier 等；ResearchOS 用自己的品牌，保留准确来源归属。

| 能力 | 固定源码入口 | 采用边界 |
|---|---|---|
| 应用壳/历史 | `apps/electron/src/renderer/components/app-shell/AppShell.tsx`、`SessionList.tsx`、`WorkspaceSwitcher.tsx` | 复用布局和交互；不要携带其独立工作流状态体系作为 ResearchOS 真值 |
| 会话/工具流 | 同目录 `ChatDisplay.tsx`；`packages/ui/src/components/chat/TurnCard.tsx` | 可复用 turn/tool/diff 显示；需要 ResearchOS 事件到展示类型的窄映射 |
| 输入/权限 | `apps/electron/src/renderer/components/app-shell/input/ChatInputZone.tsx`、`input/structured/PermissionRequest.tsx` | 复用输入与请求卡；权限答案由本控制面消费和去重 |
| 文件/diff | `packages/ui/src/components/code-viewer/UnifiedDiffViewer.tsx`、`ShikiDiffViewer.tsx`、`components/overlay/MultiDiffPreviewOverlay.tsx` | 已有 unified/split 显示；不是可直接证明文件写入安全的后端 |
| 首次配置 | `apps/electron/src/renderer/components/onboarding/OnboardingWizard.tsx`、`ProviderSelectStep.tsx`、`CredentialsStep.tsx` | 复用分步界面与状态；重接 ResearchOS 凭据存储与 provider probe |
| 主题 | `apps/electron/src/renderer/context/ThemeContext.tsx`、`hooks/useTheme.ts` | 接本包 token 与用户主题设置 |
| 传输切口 | `apps/electron/src/preload/bootstrap.ts`、`src/transport/build-api.ts`、`channel-map.ts` | 当前是 WebSocket RPC preload，不是旧教程的 preload/index.ts；必须绑定同一 ResearchOS 控制面 |
| 安装 | `apps/electron/electron-builder.yml`、`scripts/build-win.ps1` | 复用 Windows 打包入口；删除未采用 SDK/服务的打包资源、上游自动更新地址和服务域名 |

实际读取：[ChatDisplay](https://github.com/craft-ai-agents/craft-agents-oss/blob/73bd9c2a3573158bea880984eb8d5fdb41e0cac2/apps/electron/src/renderer/components/app-shell/ChatDisplay.tsx)、[preload/bootstrap.ts](https://github.com/craft-ai-agents/craft-agents-oss/blob/73bd9c2a3573158bea880984eb8d5fdb41e0cac2/apps/electron/src/preload/bootstrap.ts)、[UnifiedDiffViewer](https://github.com/craft-ai-agents/craft-agents-oss/blob/73bd9c2a3573158bea880984eb8d5fdb41e0cac2/packages/ui/src/components/code-viewer/UnifiedDiffViewer.tsx)、[OnboardingWizard](https://github.com/craft-ai-agents/craft-agents-oss/blob/73bd9c2a3573158bea880984eb8d5fdb41e0cac2/apps/electron/src/renderer/components/onboarding/OnboardingWizard.tsx)。

Craft 的默认 preload 会路由本地/远程服务，仓库有 server-core 的 sessions、tasks、automations 等业务 handler。这些不能与 ResearchOS Go scheduler 同时成为调度权威。本路线复用 shell/UI，执行器按 PI_COMPOSE 资格结果接入；不同时上线 Craft server、Mu/AionCore 和 ResearchOS 三套主控。React 组件依赖其共享类型、Jotai、UI 包等，复制一个 TSX 并不意味着能独立编译；W01 要固定可运行的最小依赖切片。

## 4. Claude / Qoder 能否直接 clone 官方前端

本轮未找到带明确开放源码复用许可的 Claude Desktop 或 Qoder Desktop 官方完整前端仓库。不能由“GitHub 上有同名仓库”推断可以 fork 商业桌面源码。

- Anthropic 的公开 [claude-code/LICENSE.md](https://github.com/anthropics/claude-code/blob/main/LICENSE.md) 声明 all rights reserved，并指向商业使用条款；这个仓库不能作为 MIT/Apache 桌面前端来源。
- [QoderAI 官方组织](https://github.com/QoderAI) 公开了 SDK、CLI Action、Qoderian、better-harness 等；[官方下载页](https://qoder.com/download) 提供 Desktop/CLI 二进制；[Quick Start](https://docs.qoder.com/quick-start) 说明项目、会话、Quest 与审查体验。此次没有找到其 Desktop 官方前端开放源码许可。Qoderian 是 Obsidian 集成，并不是 Qoder Desktop 源码。
- 因此 Claude/Qoder 用作功能和交互参照：项目/会话历史、中心对话、明确工具进度、文件 diff、待处理请求、可见控制与设置。实际施工 clone 的是以上已固定 Mu/Craft 代码；不要求获取未获开放许可的商业前端，也不复用其品牌。

## 5. 当前仍未证明

Mu UI + Go authority + Mu Node worker 的单会话双端连接、Windows 中文路径、进程树取消、安装后首次启动、离线/休眠恢复、真实模型工具流均 `NOT_RUN`。上游测试或 README 声明不能改成 ResearchOS 的 PASS。Qwen3.8 Flash 在 Qoder 中的具体标识、上下文与工具协议由执行入口另行实测，不能从桌面源码许可推出模型兼容。

GitHub REST 曾出现匿名限流，后续固定树/原文件读取成功；没有把一次失败后变量里残留的 revision 作为另一仓库的版本。AionUi 当前 HEAD 未作为独立候选固定，本包只依赖已固定 Mu 子树的 AionUi 归属。
