# ResearchOS 自用 Agent 工具链资源核对

建议先采用 **DeepSeek 官方 Pi 协议配置作为审查和测试依据**；需要扩充工具来源时，再试 **官方 MCP Go SDK 的窄工具适配层**。现阶段不建议用 Claude Agent SDK 替换 Mu。此为资源研究结论，未安装、采纳或验证任何候选的运行资格。

实际公开 GET 核对日期为 2026-10-07；每次 UTC 起止、HTTP 状态、最终 URL、原始响应及 SHA 见 `*.capture.json`。下列“最近”按固定 commit 的提交时间，不按搜索引擎抓取时间。GitHub HEAD 与页面 release 缓存可能不同，本报告以实际 GitHub API 返回的完整 commit 为准，不声称查得的 HEAD 是最新发布包。

## 当前项目边界

本轮只读快照显示 `@earendil-works/pi-ai` 为 0.87.1，并已依赖 `@anthropic-ai/sdk` 0.124.0。ResearchOS 的 `worker.mjs` 使用真正 `createAgentSession`，经 `streamSimpleOpenAICompletions` 的自定义 fetch 转到 Go MODEL broker；`SessionManager.inMemory`、关闭内建工具和外部配置加载，工具由 Go 显式声明。SDK retry、compaction 均关闭。源位置见 worker 第 729–804 行；完整原字节和 SHA 在 `local-inputs.snapshot.json`。

Go broker 保留 PREPARED、STARTED、UNKNOWN 的持久效应状态；worker 的初始化 ACK、SDK 队列消费、prepare/commit seal 是独立边界。Go 的 UNKNOWN 分支明确禁止自动重试（`runtime_model_windows.go:60–63`）。因此新库应接在已有模型传输或工具端口后面，不应并行启动另一个业务循环。以上是当前 Main 读到的源码事实，不能当作未整合 provider 候选或当前 LIVE 资格。

## 候选表

| 候选与固定版本 | 核到的能力及许可 | Windows / Go / Node / Mu 接入判断 | 对当前缺口的作用与最小实验 |
|---|---|---|---|
| [DeepSeek 官方 Agent 接入指南](https://github.com/deepseek-ai/awesome-deepseek-agent/tree/9546b8f5c3ed668ec12fce083e32c5b16f1523cb)，commit `9546b8f5`，提交 2026-09-17 | 文档集；Pi 指南列出 `openai-completions`、DeepSeek thinking 格式及保留 reasoning history 的配置。根目录和 API 未发现明确 LICENSE，不能据此授予复制代码的开源许可。 | 最低成本。直接比对现有固定 Mu API；Windows 配置示例存在，但不写用户全局 `models.json`，不采纳指南中全局安装/升级步骤。 | 最有价值的是 reasoning/tool-history 兼容性依据。规划离线同 Run MODEL→TOOL→MODEL、reasoning 原文及流式 tool arguments 夹具；所有字段仍经现有 broker 校验，不解决 Pause/ACK。 |
| [DeepSeek 官方 Tool Calls](https://api-docs.deepseek.com/guides/tool_calls/) 与 [OpenCode Go](https://opencode.ai/docs/go/) | 前者描述原生 DeepSeek 的 tool/strict 协议；后者实际列出 `deepseek-v4.1-flash` 和 `/zen/go/v1/chat/completions`。文档及服务条款不等同 SDK 开源许可证。 | 保留当前 Go gateway + Mu OpenAI-completions 的方向，成本低。DeepSeek 原生 `/beta` strict 行为不能直接套在 Go gateway。 | 规划本地 SSE split、EOF、400/429、reasoning alias、abort 和 exact ACK 负控。README/路由表不证明账号可用、quota、严格预算上界或实际成本；本轮没有 authenticated GET 或 MODEL POST。 |
| [Anthropic TypeScript API SDK](https://github.com/anthropics/anthropic-sdk-typescript/tree/d49bdab458000bcdffe77bd84b03293f31824fb3)，package 0.131.0，提交 2026-09-30 | MIT；直接 Messages API，streaming 和 beta toolRunner，后者会运行自己的工具循环。Node 20+；本地 Mu 已含较早的 0.124.0。 | Windows/Node 可评估；现有 Node 版本足够不是实测兼容证明。不要重复引入第二份 SDK 或直接升级锁；Mu 当前指定 OpenAI-completions，若加 Anthropic provider 需独立 wire/schema 接口设计。 | 可作未来 Claude 模型调用适配参考，保留 Go scheduler；不启用 toolRunner 自动执行。最小实验是无凭证 mock transport 的请求/流事件映射和 retry=0，不借新 SDK 重放 UNKNOWN。 |
| [Anthropic Go API SDK](https://github.com/anthropics/anthropic-sdk-go/tree/c9ebe447ac92c91748af817c265398e5d81ca49f)，README v1.78.0，提交 2026-09-30 | MIT，Go 1.24+；Messages、streaming、beta tool runner。 | Go Host 集成成本中等，但 Mu 已承担推理历史，增加 Go Anthropic 对话循环会重复职责。Windows 编译和取消清理仍需本地资格。OpenCode Go 的 Chat Completions 不是 Anthropic Messages。 | 暂作备选 provider transport/reference，不接当前 Flash 路由。规划单响应与流响应的故障注入；需要显式禁 SDK 自动重试并保持原 effect key。 |
| [官方 MCP Go SDK](https://github.com/modelcontextprotocol/go-sdk/tree/8dd5d6a7e12689d047ca309e0d367c6868f388e9)，提交 2026-10-07，go.mod 1.25 | 客户端/服务端/JSON-RPC；stdio 工具调用。当前 LICENSE 是 MIT→Apache-2.0 过渡：新贡献 Apache、未再授权旧贡献 MIT，文档 CC-BY-4.0，不能笼统标 MIT。 | 中等成本。适合 Go 工具适配，不必替换 Node/Mu。Windows stdio 子进程须接 ResearchOS owned Job/句柄；不能直接把示例 `exec.Command` 当现有进程治理。 | 可扩工具互通，不提供数据库事务 ACK。先规划一个无副作用本地工具、显式 schema/capability 白名单、重复 call ID、取消、进程退出与未知结果测试；sampling/客户端任意命令默认不启用。 |
| [Claude Agent SDK TypeScript](https://github.com/anthropics/claude-agent-sdk-typescript/tree/d4f0435765128047dbe7c99e1fc46e1fbed85357)，提交 2026-10-06 | Claude Code 子进程、内置工具、MCP、hooks、session resume、file checkpoint。TS 仓库 LICENSE 为 all rights reserved / Commercial Terms，并非 MIT；Python wrapper 的许可层级另论，不能混为一谈。 | 高成本替代执行器；Go 需子进程/Node 桥与重新审查身份、预算、进程和工具权限。DeepSeek 官方 Claude Code 指南走原生 `/anthropic`，不是 Go Flash Chat Completions 可直接兼容的证据。 | 不推荐进入当前产品链。最小未来实验只做隔离协议观察、关闭内置危险工具和外部配置。SDK session history/file rewind 不等同 ResearchOS checkpoint/效应补偿，不能解决当前 Pause/ACK。 |

MIT/Apache 的摘要仅标明捕获到的许可层级；若以后复制/分发组件，应保留对应原 LICENSE/NOTICE。SDK 代码许可也不免除模型服务的账户和服务条件。Claude Agent SDK 官方文档对第三方产品提供 claude.ai 登录有单独限制；本轮没有使用登录、密钥或订阅资源。

## 三个必须分开的事实

1. DeepSeek 官方新仓库是接入索引。里面的 Deep Code、DeepSeek-TUI 等链接不能因为收录就称为 DeepSeek 官方实现。本轮没有找到并核实一个可直接替换 Mu 的新 DeepSeek 官方 agent runtime；这是本轮有限查询的结果，不是对全部 GitHub 仓库的不存在证明。CUDA/推理内核、训练和 GPU 调度栈不在本项目这次适配范围。
2. [Claude sessions](https://code.claude.com/docs/en/agent-sdk/sessions) 保存对话历史；[file checkpoint](https://code.claude.com/docs/en/agent-sdk/file-checkpointing) 只覆盖指定编辑工具，不能倒回任意 Bash/外部副作用。我们的结论是：没有候选能自动补齐 ResearchOS 暂停、租约 epoch、checkpoint adoption、CANCEL ACK→COMPLETED 或 UNKNOWN 对账。
3. 原生 DeepSeek Pi 指南给的是 V4 Pro/Flash，OpenCode Go 页面给的是 V4.1 Flash；endpoint、model ID、reasoning、strict 和 token/cost 帽必须按各自服务单独核定。不得把文档样例的 384K 输出、1M context 或旧价复制成已验证的 ResearchOS 运行上限。

## 建议后续顺序（全部 NOT_RUN）

E1：无需新依赖，先把官方 Pi 配置与已封 provider 候选做字段差异表，随后另批只本地 SDK/broker SSE 夹具。验证同一 Run 工具循环、原 history、canonical MODEL key、credit/ACK、取消、EOF 和 UNKNOWN 无重试。不能借此解除旧 held 正例或清零失败链。

E2：若用户需要新的工具连接，针对固定 MCP commit 提出单工具端口实验。Go journal 仍是唯一事实来源；MCP request ID 只作传输关联，收到 response 不自动等于业务 CONFIRMED。先无副作用，再单独设计可写工具的幂等和恢复。

E3：将来需要 Claude provider 时才评估 API SDK（优先沿现有 Pi 内置依赖）；在模型 transport 与效应 ledger 间接线，不引入 beta toolRunner 的第二循环。Claude Agent SDK 替换只保留为独立研究方案。

本轮只有公开 GET 和本地只读源码/文档快照；安装、构建、产品运行、模型调用、凭证读取、canonical 改写均为 0。本报告不是依赖采纳或源码接受。公开浏览有一次 DeepSeek thinking 页面工具 Internal Error；独立原始 HTTP 捕获随后为 200，两条观察分别保留，不把网页工具错误变成已知 native exit。
