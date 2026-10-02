# ResearchOS v2.4 施工交接 — W04 支路（2026-10-02）

## 冻结环境（每条命令都要用，勿换工具链）

```
cd D:/作品集/ResearchOS/research-os
export GO="$PWD/.local/tools/go1.27.1/go/bin/go.exe" GOTOOLCHAIN=local GOENV=off \
       GOPATH="$PWD/.local/gopath" GOCACHE="$PWD/.local/gocache" \
       RESEARCHOS_GO="$GO" RESEARCHOS_NODE=node RESEARCHOS_NPM_CLI=npm_cli
```

Windows 控制台是 GBK：含非 ASCII 的输出必须重定向到 `.local/*.txt` 再读回；含引号/制表符的多行脚本一律用 Write 工具落成 `.local/*.py`，不要用 heredoc（本卡已多次因此炸掉）。

## 已完成并已提交

- `W01-01 … W03-02`、`W17-01`、`W04-01` 共 **14/71 卡 ACCEPTED**（登记在 `execution/v2.4/step_state.json`，每条都带 executor_id ≠ verifier_id 与 sha256 证据钉）。`W01-99` 因缺 LIVE 资源 **BLOCKED**（只阻塞该支路，未重置任何失败计数）。
- `W04-01` 由第 5 个全新身份无保留 ACCEPT：复核者自己复现 158 断言、原样重跑 53 例变异矩阵（无一翻转）、自跑 17 例变异、并独立做 CreateBackup/RestoreBackup 往返（污染对照仍复现 `RESTORE_CONTRACT_INCOMPATIBLE: WorkspaceBinding`）。checkpoint rev 25。
- `W04-02` 施工完成度（提交 `40babf14`、`38025c24`，工作树干净）：`go run ./tests/context/check` 连续三次 **PASS 239**、断言 id 列表一致、0 失败；绑定行 `python execution/command_dispatcher/dispatch.py test.context --task-id W04 --check-id W04-02` → PASS 239（invocation `15c7e956`）。变异 15 例中 14 例死在具名断言上；1 例存活（Z3）如实标注为「存储层先拒绝篡改、服务内 receipt/summary 校验够不到」的冗余防御。
- 本卡顺带修掉两个真实产品缺陷（都在写范围内）：
  1. `internal/domain/changes.go` `resolveConflict` 要求冲突记录**先**写明 `resolution_proposal_id`（正是该操作要写入的字段，`CreateConflictRequest` 也不含它）→ 任何冲突永远无法解决。
  2. `internal/domain/context.go` `createContext` 只把「任务自己引用为输入的 DecisionReceipt」列入冻结结果 → 新会话恢复不出项目当前生效决定，违反本卡步骤 1；现在合并 `ProjectState.current_decision_refs`，去重，解析失败的走 `unresolved_items`。
- 遗留 `internal/domain` 测试失败已用 A/B（把本卡文件换回 HEAD 重跑同一批）证明与本卡无关，记录在 checkpoint `known_pre_existing_failures`。
- `commands.json` 现为 **rev 11**（新增 `check_id W04-02` 由 Go 构建检查应答，其余 selector 继续原样转发给 `ops/ci/context.py`）。这是写范围外的「延续文件」，已在 checkpoint `integrity_events` 披露；后果：已接受的 W04-01 回执所钉 rev 10 的 commands.json 哈希成为历史，回执未被改写。

## 在飞事项（不要重复派工）

`w0402_verifier_r1`（后台子 Agent）正在独立复核 W04-02，裁定会写到
`execution/v2.4/receipts/W04/W04-02/independent_review_round1.json`。到稿后：

- **ACCEPT / ACCEPT_WITH_RESERVATIONS**：按 `tools/task_packet.py` 流程登记 ACCEPTED（step_state 增加记录，evidence 用 `receipts/W04/W04-02/` 下文件的 sha256、路径相对 `execution/v2.4/`），checkpoint rev 25→26，`accepted_steps` 追加，失败计数只追加不重置，然后提交并 `task_packet.py next` 取下一张卡（预计 `W04-03`）。
- **REJECT**：按点名条目整改后，用**新的**复核身份重跑（同一身份不得复审自己的结论）；不要重置失败计数，不要为通过而削弱门槛。

复核者被明确要求判定 3 项显式 `not_verified` 是否属于「正确延期」还是「本卡义务」：`CHG-PROPOSAL-NAMES-ITS-IMPACT`（需 `analyzeChangeImpact`，依赖 W06 orchestration 夹具）、`CHG-OPTIONAL-RETRIEVAL-DEGRADES`（需检索/FTS 路径）、`CTX-BUNDLE-DECISION-SCOPE`（应用变更前的空决定集说明）。

## 还欠什么（不得提前宣布完成）

目标口径是 **22 个父任务 + 42 个正式用例全部有效接受**；当前 0/22、正式用例终验未开始。剩余主干：`W04-02` 之后的 W04-03…W04-99，以及 W05…W21 各支路；`W01-99` 需 LIVE 资源；W04 父门禁还欠：迁移自有表的 workspace 绑定（含 store 级规范路径唯一性且恢复仍绿）、`/v2/command` 的 `workspace.register`/`project.bootstrap` 路由（属 client_protocol 的 owner 卡）、真实原生目录选择器（`internal/host` 目前传 nil chooser）、`W04-02`/`W08` 的 Goal/Task 链与 RESEARCH/REUSE_DECISION/IMPLEMENTATION 推进。另有登记债：`commands.json` 里 GOPATH/GOCACHE 为绝对路径（L1 待重指向）、`execution/invocations/` 未被忽略而持续堆积（R3 的 .gitignore owner 卡）、VB-4 写者归属需绑到已验证 OS principal、VB-2 `RESEARCHOS_GO` 未登记为 required_env。
