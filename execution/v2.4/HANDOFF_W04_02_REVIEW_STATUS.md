# W12-01 分支交接 — 写给下一个窗口

> **文件名是历史遗留，内容是当前交接。** 本文件仍叫 `HANDOFF_W04_02_REVIEW_STATUS.md`，因为
> `receipts/W04/W04-02/independent_review_round1.json` 与 `round2.json` 都按这个名字引用它，
> 而这两份裁定已被 hash 进 `step_state.json` 的 W04-02 证据集——改名会让已冻结证据里的路径悬空。
> 所以名字不动，内容整篇重写。上一版（W04-02 待整改）由 git 历史保留。

更新时间：2026-10-03（UTC）· 仓库：`D:/作品集/ResearchOS/research-os`
上一版（W04-02 待整改）由 git 历史保留，不删；本版取代它的叙述。
**它是叙述，不是权威**；权威是下面「先跑这四条」里的机器输出。两者不一致时以机器输出为准，并把这当作一次待报的偏差。

## 1 · 一句话现状

W04-02 已被第三个全新身份判 **ACCEPT_WITH_RESERVATIONS**（0 条 blocking），已登记，checkpoint 到 **rev 28**、
**15/71** 卡 ACCEPTED；`task_packet next` 现在选出的卡是 **W12-01**，不是 W04 的任何卡。

## 2 · 先跑这四条，确认真实状态（不要跳过这步）

```bash
cd D:/作品集/ResearchOS/research-os
export PYTHONIOENCODING=utf-8
git log --oneline -4                      # HEAD 应为 b7db6981「W04-02 accepted with reservations」
git status --porcelain | grep -v '^??'     # 应为空（源码树干净）
python -c "import json,io;c=json.load(io.open('execution/v2.4/checkpoint.json',encoding='utf-8'));print(c['revision'],c['expected_previous_revision'],len(c['accepted_steps']),c['work_in_progress'],c['current_step_id'],len(c['failure_counters']),len(c['open_obligations_before_next_card']),c['blocked_steps'])"
python "D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/tools/task_packet.py" next --state execution/v2.4/step_state.json
```

本文件写完时的实测值：HEAD `b7db6981`；源码树 0 个 modified；checkpoint
`revision 28 / expected_previous_revision 27 / accepted_steps 15 / work_in_progress None /
current_step_id W12-01 / failure_counters 13 / open_obligations_before_next_card 48 /
blocked_steps ['W01-99']`；`task_packet next` 返回 `state_source=VALIDATED_FILE`、
`product_acceptance=NOT_ASSERTED`、`step.id=W12-01`。

锁定环境（必须用仓库内工具链，勿用系统 go/node）：

```bash
export GO="$PWD/.local/tools/go1.27.1/go/bin/go.exe" GOTOOLCHAIN=local GOENV=off
export GOPATH="$PWD/.local/gopath" GOCACHE="$PWD/.local/gocache"
export RESEARCHOS_GO="$GO" RESEARCHOS_NODE=node RESEARCHOS_NPM_CLI=npm_cli
```

## 3 · 下一张卡：W12-01「费用预占、对账与有限重试」

| 通道 | 内容（取自 `task_packet next` 输出，勿凭记忆） |
| --- | --- |
| 父任务 / 优先级 / 阶段 | `W12` / 160 / `IMPLEMENTATION_SLICE` |
| 依赖 | `W03-02`（已 ACCEPTED） |
| write_scope | `internal/domain/budget*.go`、`internal/domain/resource*.go`、`tests/resources/**`、`execution/v2.4/receipts/W12/W12-01/**` |
| 绑定命令 | `python execution/command_dispatcher/dispatch.py test.resources --task-id W12 --check-id W12-01`（cwd=REPOSITORY） |
| 受影响正式用例 | C11 / C13 / C14 / C15（本卡只能增量，终验属各用例 owner） |
| receipt 目录 | `execution/v2.4/receipts/W12/W12-01` |
| resource_requirements | 空 |

**选卡跳号是正常的**：卡按 DAG + priority 排，不按编号。W12-01 早于 W05–W11 被选出并不说明状态坏了。

### 这张卡的第一个坑是命令注册表，不是预算逻辑

`commands.json` 现在是 **rev 11**，`test.context` 由 W04 线绑定。W12-01 需要 `test.resources`。
历史上在这一步出过真实事故：往 `commands.json` 追加 `test.context` 时**静默重路由并收窄了 auto 解析**，
使 `W06-G02`、`W12-C13`、`W17-C02` 和用例 `C01/C02/C13` 变成 `NOT_IMPLEMENTED`，而当时的 receipt 断言这不可能发生。

所以：追加 `test.resources` 之后，**把所有既有 selector 全部重跑一遍**并把结果写进 receipt，
不要只验新键；其余 selector 必须继续 default-forward 到 `ops/ci/context.py` 带遗留工具环境；
parity 要在 `--spec v2.4` 与 `--spec v2.0` 两条路由下各测一次。任何新的环境变量依赖必须同时登记成 `required_env`
（`RESEARCHOS_GO` 没登记时，遗留 `internal/domain` 测试会出现 20+ 条假失败——那不是测试红，是误诊）。

另外：`W12-C13` 这一行历史上被独立复核定性为**已验收 W12 夹具自身的 route-independent 抖动**
（第 1 次 `COMMAND_FAILED 10`，第 2、3 次 `PASS 13`）。判抖还是判确定性看**断言数**：
`COMMAND_FAILED 0` 是 task-only 未绑定时的确定性 fail-closed，多跑不变；断言数会变的才是真抖。
逐次记录，别把「重试才绿」写成一个干净的 PASS。

## 4 · W04-02 这轮做了什么（细节都在 receipt 目录，别在这里找数字）

- 九条合并整改项全部闭合，台账在 `receipts/W04/W04-02/post_review_actions.json`。
  它的生成器会拒绝把任何一条称为 closed，除非它引用的断言 id 真的在交付的运行里、
  引用的变异真的被判死——这个自检当时就抓住了我自己把「存活变异」误标成问题的一处。
- 检查从 `PASS 239`（3 条 skip）到 **`PASS 282`**（2 条 skip），三次串行运行 id 序列逐序相同；
  **已验收 W04-01 的 158 条 id 按集合差全部仍在**。
- 变异矩阵 33 例：**32 死 / 1 存活 / 0 崩溃**，逐例 hash 精确复原。存活的正是 r2 自创的 revision-CAS 变异，
  按**等价变异附证明**上报（上游 412 门卫使两值必然 hash 相等），补偿对照是 Z2。
- 两轮都存活的 **Z3 现在被两条 id 杀死**：服务侧完整性门卫终于有了能触达它的正对照。
- 裁定：`independent_review_round3.json`，`reviewed_at 2026-10-02T17:53:52Z`（晚于两次 REJECT），
  身份 `w0402_verifier_r3`。它自己重跑、自己改 id 名、自己删 roster 条目、自己整文件回退 `changes.go`，
  全部 hash 精确复原并在裁定里写明。
- 4 条 reservation 已转成义务，按 owner 卡索引在 `carry_forward_obligations.json`。

## 5 · 三条纪律，别再犯

**能重算的数字就不要抄，也别让生成器替你把话说错。** 这轮我的 receipt 里有一个字段写着
`failing_tests: ["FAIL:"], count: 1`，而它引用的文件里有 4 条 `--- FAIL: Test...`——生成器用
`split(" ")[1]` 取到了字面量 `FAIL:` 而不是测试名。是复核者发现的（R-1）。
更正走 `precision_notes.json`，**receipt.json 逐字节不动**，因为复核者已经读过并重算过它的 `receipt_hash`；
那个 hash 现在仍然自校验通过。生成器的 bug 已修，但已发布的 receipt 不重新生成。

**`.local` 不能是正式证据的唯一副本。** 那份 receipt 用路径引用了 6 个 `.local` 下的产物
（三次稳定性运行、遗留套件全量输出、A/B 结果、绑定命令 stdout）。它们已按字节复制进 receipt 目录并 pin 住。
引用 scratch 路径等于埋一个将来必然悬空的引用。

**登记脚本的「已实测」要看测的是哪条分支。** `.local/register_w0402_accepted.py` 之前有个 `vid` 未定义的
NameError，任何 ACCEPT 路径都会崩；交接文档说它「已实测」，实测的只是拒绝路径。
它的身份去重还只读 `verifier_id`，而 r2 用的是 `reviewer_id`——**r2 的身份本可以再次裁定**。
两处都已修，并用 `.local/test_register_guards.py` 在 `.local/guardtest` 的临时副本上验了 **8/8 条守卫**
（绝不在真 receipt 目录里放假裁定，因为登记会把该目录整个 hash 进证据）。
它的 `ACCEPTS` 原本还漏了规范词 `ACCEPT_WITH_LIMITATIONS`，也补上了。

## 6 · 完成度红线（禁止据此宣布完成）

**15/71 卡 ACCEPTED、0/22 父任务、0/42 正式用例终验。** 接受一张卡 ≠ 接受父任务 ≠ 签正式用例。

W04 父门槛仍欠（都在 `carry_forward_obligations.json` 与 checkpoint 的 `open_obligations_before_next_card` 里）：
migration 权威表（WorkspaceBinding / BootstrapStage / BootstrapReplay / Project + 存储层规范化路径唯一性
+ 一次真实 CreateBackup/RestoreBackup 复证）、`/v2/command` 路由 `workspace.register` 与 `project.bootstrap`、
`internal/host` 那个 nil 参数后面的原生目录选择器、`bootstrap_task_id` 指向的 Goal/Task 链、
W08 对 RESEARCH / REUSE_DECISION / IMPLEMENTATION 的晋升、W04-99 的正式用例、
以及 W04-01 三个漂移 pin 的重 pin（`legacy.go` / `main.go` / `commands.json`）。

W01-99 因缺 LIVE 资源继续只阻塞该支路，**失败计数不清零**（现在 13 条，是追加不是重置）。
`blocked_resources` 里仍有 6 项缺资源。

## 7 · 工作树里可能出现的「别人的改动」

本轮的变异矩阵会临时改 `internal/domain/context.go`、`materialize.go`、`http.go` 和
`tests/context/check/w0402.go`，逐例 hash 精确复原；runner 一旦复原失败会**中止整张矩阵**。
交接时源码树 0 个 modified（已用 `git status --porcelain` 复验）。
若接手时见到这几个文件 modified，先确认是否有复核或矩阵仍在运行，再决定复原，不要顺手 commit。

`qualification/v2.4/mu/` 是 2026-10-01 就存在的未跟踪 vendor 快照（自带 `.git`），与任何卡无关。
**它未被 gitignore**：在它附近做宽泛 `git add <dir>` 会静默加进一个 mode-160000 gitlink（历史上发生过两次）。
每次 add/commit 之后都查一次 `git ls-files -s | awk '$1=="160000"'`。

## 8 · 复核派遣的两条硬规则

**先派出的裁定 binding。** 不要因为「以为后台 Agent 死了」就另派一个——上一轮这样犯过：
以为 r1 随窗口丢失而派了 r2，结果 r1 活着，两个 Go 重负载套件同机并发。
派之前先查 `receipts/<TID>/<SID>/independent_review*.json` 是否已有新文件，并查进程表里有没有 `go.exe`。

**Go 负载一律串行。** 复核 Agent 在跑时，主 Agent 不得同时跑任何 check / 测试 / 矩阵。
本轮所有检查、变异矩阵、A/B 都是串行的，复核期间主 Agent 只做纯 Python 与文件写入。
