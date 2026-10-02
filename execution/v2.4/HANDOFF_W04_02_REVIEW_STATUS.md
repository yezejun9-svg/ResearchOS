# W04 分支交接（W04-02 待整改）— 写给下一个窗口

更新时间：2026-10-02（UTC）· 仓库：`D:/作品集/ResearchOS/research-os`
本文件由执行 Agent 撰写，取代它自己前几版层层叠加的叙述（旧版由 git 历史保留，不删）。
**它是叙述，不是权威**；权威是下面「先跑这四条」里的机器输出。两者不一致时以机器输出为准，并把这当作一次待报的偏差。

## 1 · 一句话现状

W04-02 的实现与证据已完整入库，被两个先后独立身份各判一次 **REJECT**（都复核在未整改的树上），
9 条合并整改项已登记，下一张可做的卡**仍是 W04-02**，不是新卡。

## 2 · 先跑这四条，确认真实状态（不要跳过这步）

```bash
cd D:/作品集/ResearchOS/research-os
git log --oneline -3                      # HEAD 应为「交接整理」那次提交，且下面第 4 条不报错
git status --porcelain                     # 应只见 ?? execution/... 与 ?? qualification/... 两类未跟踪目录
python -c "import json,io;c=json.load(io.open('execution/v2.4/checkpoint.json',encoding='utf-8'));print(c['revision'],c['accepted_steps'],c['work_in_progress']['status'],c['failure_counters'][-1]['origin_key'])"
python "D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/tools/task_packet.py" next --state execution/v2.4/step_state.json
```

本文件写完时的实测值：checkpoint `revision 27`、`accepted_steps` 14 项、
`work_in_progress.status = EXECUTION_REPORTED`、最后一条计数是 `W04-02/independent_review_round2`、
`blocked_steps = ['W01-99']`、`task_packet next` 返回 `step.id = W04-02` 且 `product_acceptance = NOT_ASSERTED`。
锁定环境（必须用仓库内工具链，勿用系统 go/node）：

```bash
export GO="$PWD/.local/tools/go1.27.1/go/bin/go.exe" GOTOOLCHAIN=local GOENV=off
export GOPATH="$PWD/.local/gopath" GOCACHE="$PWD/.local/gocache"
export RESEARCHOS_GO="$GO" RESEARCHOS_NODE=node RESEARCHOS_NPM_CLI=npm_cli
```

## 3 · 这张卡现在是什么状态

| 通道 | 内容 |
| --- | --- |
| 检查 | `go run ./tests/context/check` → **PASS 239**（40 CTX + 41 CHG 为本卡新增），0 失败，3 条 `not_verified`；三次以上运行的断言 id 集合逐序相同 |
| 绑定命令 | `python execution/command_dispatcher/dispatch.py test.context --task-id W04 --check-id W04-02` → PASS 239，exit 0（registry `commands.json` rev 11；round-2 复核确认未削弱已接受的 W04-01：其 158 条 id 是 239 条的真子集） |
| 变异 | 15 例，14 例按点名 id 致死，Z3 存活；**存活的真因已由复核查清**（见 B5），原先写成「冗余防线」是错的 |
| 产品缺陷修复 | 两处真实缺陷已修并保留：`changes.go` 的 `resolveConflict` 门卫自相矛盾（原先任何冲突都不可能被判解决）；`context.go` 的 `createContext` 丢弃 ProjectState 上的治理决定 |
| 裁定 | `receipts/W04/W04-02/independent_review_round1.json`（r1，REJECT，8 项）与 `independent_review_round2.json`（r2，REJECT，7 项，5 项与 r1 重合、3 项为新增） |
| 执行者回应 | `executor_response_round1.json`、`executor_response_round2.json`；W04-01 的 hash 漂移披露在 `receipts/W04/W04-01/pin_drift_erratum_1.json` |

## 4 · 9 条整改项与建议顺序（都在 checkpoint `open_obligations` 里，这里只是可读版）

1. **产品缺陷优先**：`resolveConflict` 了结冲突后必须像 `applyChange:547-557` 那样把该 id 从
   `ProjectState.blocking_conflict_ids` 中摘除，并加关联校验与 OPEN 状态门卫——现状是任何 APPLIED
   变更都能了结任何冲突（实测 Requirement 文本变更以 200 了结 ProjectState 冲突），且 RESOLVED
   冲突可被重复了结；后果是之后每次冻结都把已关闭冲突报成 `unresolved=["Open conflict: <id>"]`，
   直接违背本卡「新会话恢复准确下一步」。
2. **按值断言下一步**：`resume_instruction` / next step 与 `unresolved_items` 内容要有真断言，不能只
   检查键存在（`put()` 的 schema 校验本来就保证键存在）。
3. **取消假跳过**：`createChange` 经 `closure()` 确定性填充 `impacted_refs` 与 `impact_link_ids`（实测
   3/3），所以 `CHG-PROPOSAL-NAMES-ITS-IMPACT` 属本卡 step 3，不是 W06 的债。
4. **接受权限要真**：`w0402.go:608` 现在靠 `403 || 409` 过关，而探针拿到的 403 是「role not authorized」
   （该主体根本没有 VERIFIER）——这正是本卡已为 AA1 修掉的那类陷阱的孪生；要用真正持有 VERIFIER 的主体断言。
5. **补正向对照**：`CTX-CONTEXT-READABLE-AGAIN-AFTER-RESTORE`（`w0402.go:351`）**任何运行都不会发出**，
   因为 `store.go:165` 以「回执不可变」拒绝那次 UPDATE；于是篡改拒绝只走存储支路、服务侧完整性检查
   零覆盖，这也是 Z3 幸存的真因。
6. **证据文本更正**：两处计数仍报错、`progress_note_1.json` 没有 hash 且 provenance 少一个文件、
   被宣告的「6 个 pre-existing 遗留失败」实为两态都通过（诚实 A/B 只剩一个确定性失败
   `TestW17UpgradeActiveRecovery: no such table: runtime_dispatches`，其余 3 个是本机 loopback 抖动）、
   两个跳过的归因（`CHG-OPTIONAL-RETRIEVAL-DEGRADES` 实质可延但归因错、`CHG-PROPOSAL-NAMES-ITS-IMPACT` 根本不该延）。
7. **补第二个存活变异的处理**：r2 自创的「存调用方声称的 revision 而非 `state["revision"]`」在 PASS 239 下存活。
8. **堵静默退化**：检查程序可以无声丢掉断言 id（`w0402.go:430-436`），既无失败也无数量地板；
   `contextPhase` 首次拒绝即 `return`（这个坑本历史里已经记过一次）。
9. **W04-01 hash 漂移**：已用重算方式披露（`receipt.json` 30 条 artifact hash 中 3 条变了；
   `step_state` 的 20 条 pin 全部完好）。不撤销 W04-01、不偷偷重 pin；后续按 commit pin 的事属于既有的
   registry/回执卫生义务。

做完 1–8 后：**串行**复跑 `go run ./tests/context/check`（≥2 次比对 id 集合）与变异矩阵，再派**第三个全新身份**
复核整改后的树；登记用 `python .local/register_w0402_accepted.py`（`--dry-run` 先看它找到哪个裁定）。它硬性要求
裁定是 ACCEPT/ACCEPT_WITH_RESERVATIONS、**晚于两次 REJECT 的时间戳**、身份不属于执行者也不属于 r1/r2、且不再留有
`blocking_issues`；通过才写 `step_state` 的 ACCEPTED 记录（hash 现场重算）、把 checkpoint 27→28、追加
`failure_counters` 并把复核发现转成义务。**已实测**：当前它只输出「no registrable ACCEPT」，拒绝写入。

## 5 · 两条纪律，别再犯

**不要以为后台 Agent 死了就另派一个。** 这一轮我就犯了：以为 r1 随上一窗口丢失，派了 r2，结果 r1 活着，
两个 Go 重负载套件同机并发，r1 观测到一次 `TestRuntimeCoordinatorConcurrentSealConflict` 抖动并归因于此。
后果写成硬规则，而不是靠记性：**先派出的裁定 binding，后派出的那次不能充当「整改后的复核」**。
交接前先查 `receipts/W04/W04-02/independent_review*.json` 是否已有新文件，或在同一份通知里等它落地。

**能重算的数字就不要抄。** 我给 W04-01 写漂移 erratum 的第一版量错了 pin 集（拿 `step_state` 的 20 条去
描述 `receipt.json` 的 30 条），差点发布「0 drifted」旁边跟一句声称漂移的话。提交前重算才发现，
现在两个集合分开陈述。

## 6 · 完成度红线（禁止据此宣布完成）

14/71 卡 ACCEPTED、**0/22 父任务**、**0/42 正式用例终验**。W04 父门槛仍欠：migration 权威表
（WorkspaceBinding / BootstrapStage / BootstrapReplay / Project + 存储层规范化路径唯一性 + 一次真实
CreateBackup/RestoreBackup 复证）、`/v2/command` 路由 `workspace.register` 与 `project.bootstrap`
（`internal/domain/client_protocol.go` 的 owner 卡）、`internal/host` 那个 nil 参数后面的原生目录选择器、
`bootstrap_task_id` 指向的 Goal/Task 链、W08 对 RESEARCH / REUSE_DECISION / IMPLEMENTATION 的晋升、
以及 W04-99 的正式用例。W01-99 因缺 LIVE 资源继续只阻塞该支路，失败计数不清零。

## 7 · 工作树里可能出现的「别人的改动」

两个复核 Agent 都曾临时回退 `internal/domain/changes.go`、`context.go` 做 A/B；截至本文件更新时源码树
**干净**（已用 `git status --porcelain` 复验，两文件 hash 已按复核报告字节复原）。若接手时又见到这两个
文件 modified，先确认是否有复核仍在运行，再决定复原，不要顺手 commit。
`qualification/v2.4/mu/` 是 2026-10-01 就存在的未跟踪 vendor 快照（自带 `.git`），与本卡无关、不在任何人范围内。
