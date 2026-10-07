# W07 完整接受链预检

本报告由 `codex:/root/queue_upgrade_impl` 独立编写。结论范围为执行准备；正式接受数为 0。源码依据与实际只读检查见 `snapshot.json`、`snapshot.command.json`，机器可读字段表见 `field_map.json`。本轮没有运行 LIVE、旧 proof 正例或修改 canonical 状态。

当前卡必须依次完成真实执行、完整 context、独立 review、Root 实际收到 review 消息、Root issuance、canonical owner 登记。SOURCE_READY 工具审查、56 个工具测试和旧 run-8017 只支持工具开发资格；不能替代其中任何一步。

## 先固定输入与角色

1. Root 串行整合所有影响当前编译图的源码，包括已审查的 collector relocation 和 S6。保持原失败回执。固定源码、两个 registry、tool lock；旧 source capture 不得重新标记为当前。实际变更是否已合入以执行前 HEAD 与文件 hash 为准。
2. 只读核验 canonical `step_state.json`、外部冻结 plan 和 W07-99 卡。DAG 依赖精确为 W07-01、W07-02、W03-99，三者必须 ACCEPTED 且证据 hash 有效。W05-99 不是本卡 DAG 依赖；S6 源码稳定是当前执行输入的前提。A05 是 W07 唯一 final case，C06 的 final owner 为 W08。保留 42 个 case 和 22 个 task 的完整目录。
3. 明确三种实际角色：新 proof 的 executor、独立 reviewer、`codex:/root`。忽略大小写后必须三者不同。现有卡 `codex:/root` 是准备阶段归属，不可拿它冒充独立执行者。collector 当前写入 `codex:/root/sources_parent_impl`，context 必须按实际 proof 和真实责任归属记录；保留准备历史，不改旧 proof 身份。执行前确定 reviewer，使 GLOBAL run receipt 可绑定其身份。
4. 获取冻结基线的仓库内只读副本。外部 package 可用于 CLI `--plan`，但 context refs 必须仓库内相对路径。已有 `execution/v2.4/receipts/W04/W04-99/executor_codex/frozen_inputs/package` 可逐项 hash 核验后引用；也可由 Root 在已授权 W07 路径保存相同字节副本。不要使用不存在的主线 `spec/v2.4/`。

## 四个真实 dispatcher

以下是供 Root/执行者运行的 PowerShell 命令，本审查没有执行。cwd 必须主仓库，所有命令实际 stdout/stderr/整数退出码均需保存。`$lockedPython` 从已 hash 核验的 tool lock 读取。每条命令失败时保留原回执，不制造替代 PASS。

```powershell
Set-Location -LiteralPath 'D:/作品集/ResearchOS/research-os'
$lockedPython = 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe'
Remove-Item Env:RESEARCHOS_W07_PROOF_REF -ErrorAction SilentlyContinue
& $lockedPython -B -X utf8 execution/command_dispatcher/dispatch.py test.sources.fixture --task-id W07 --check-id W07-G01 --spec v2.0
& $lockedPython -B -X utf8 execution/command_dispatcher/dispatch.py test.sources.live --task-id W07 --check-id W07-G02 --spec v2.4
```

G01 必须独立 FIXTURE。G02 必须新鲜 LIVE_SERVICE：真实 GitHub、X、论文来源，加 13 个注入故障；不是靠 LIVE 标签或测试形状通过。新 G02 输出的 `product_proof_ref` 给出实际 proof 路径。只在该 proof 与当前源码/工具/输入仍完全一致、资格检查无缺口时，执行者可用现有只读重放入口复用它：

```powershell
$env:RESEARCHOS_W07_PROOF_REF = '<从本次成功 G02 stdout 逐字读取的仓库相对 proof 路径>'
& $lockedPython -B -X utf8 execution/command_dispatcher/dispatch.py test.sources.live --task-id W07 --check-id W07-H07 --spec v2.4
& $lockedPython -B -X utf8 execution/command_dispatcher/dispatch.py test.sources.live --task-id W07 --case-id A05 --spec v2.4
Remove-Item Env:RESEARCHOS_W07_PROOF_REF -ErrorAction SilentlyContinue
```

这仍是四次实际注册命令调用。G02/H07/A05 绑定同一新 proof；G01 的 FIXTURE proof 必须与 LIVE 的 source-before/source-after 完全一致并有完整 H07。G01 registry 是 `execution/commands.json`，其他三条是 `execution/v2.4/commands.json`。两者命令均需 BOUND 且含精确 selector；不是改 frozen 卡命令来缩门。

每个原生 `execution/invocations/<id>/receipt.json` 保存 W07 目录内逐字节副本（profile 的 receipt_ref 限定 W07 前缀）；原件和副本 hash 必须一致。不能改 receipt 内 stdout/stderr：仍引用 `execution/invocations/<id>/stdout.txt` 和 `stderr.txt`。记录实际 uuid、argv、cwd、registry/toolchain/dispatcher/input hash、时间、assertion IDs。context 的四行 id 精确为 W07-G01、W07-G02、W07-H07、A05；前三个各 1 断言，A05 为 A05-01 至 A05-05。

## 文件创建顺序与字段

1. 新 capture 完整保存：source-before/after、product vector、Go inventory 的 invocation 与 JSON 流、build invocation 和 binary、三来源的 invocation/request/report/关闭或 VACUUM 后 DB、H07 原始 Go JSON 与报告、proof 和 execution report。不让 receipt 指定代码或 SQL 执行；qualification 只读固定模块和固定 SQL。
2. 保存冻结 spec refs、工具身份文件，再构建完整 formal version-vector 与 source_coverage。`field_map.json` 给出每组规则；source coverage 不能只列 MINIMUM_SOURCE。Go inventory 的所有本地包、当前完整 Go 文件、字面量 embed、固定 contracts/migrations 范围都要纳入。五组均非空。不要把 context/review/issuance 或即将修改的 step_state 放入 vector 形成 hash 循环。目录新增/删除由 coverage roots 捕获；固定工具文件可用 exact_files。
3. 保存四个不同 GLOBAL 文件：run_receipt、version_manifest、command_receipt、assertion_results。必须在 context 的 `global_evidence_refs` 中按这个插入顺序写键；当前实现按 `values()` 顺序解包。version manifest 的 formal vector ref 指向步骤 2 的 JSON，内容必须与 context 内嵌 vector 完全相等。package manifest ref 同时必须出现于 vector.spec_files。
4. 冻结 context，created_at 不早于 proof.ended_at。execution_report_ref 指向本次真实 report，compilation_invocation_ref 指向本次真实 go-list.invocation。registered_commands 与 GLOBAL command receipt 相同。每个 GLOBAL assertion 的 expected/actual/status/raw refs 原样来自 proof；另加实际拒绝证据的 locator 和 command_keys。禁止用任意正例片段充当拒绝证据。
5. 独立 reviewer 读取完整 context、执行/拒绝 raw、真实三来源与 13 H07，核对 A05 五断言和 G01/G02/H07 三门。只在无缺项/失败时写 ACCEPTED review；review 的 context_ref、proof_ref、vector 必须指向步骤 4 的最终字节。GLOBAL 验证需要真实 review 文件以读取 reviewer_id；不要造一个已接受 review 来满足函数参数。
6. reviewer 实际向 Root 发送消息，正文包含完整 review SHA 和 proof SHA。Root 按真实收到的事件保存 received-message，再写 issuance。执行者/reviewer 不代写 Root 观察。顺序必须：proof ended <= context created <= review issued <= message received <= issuance observed <= owner accepted_at。
7. Root 以 canonical state 原 hash 做串行检查，按实际审查结果更新 W07-99 状态和真实 actor/accepted_at，保留既有历史 evidence，增加恰好一份 context/review/issuance 的 refs。evidence path 相对 `execution/v2.4/`，不是仓库根。根型证据重复会拒绝；历史审查用不同 schema，不可注册多个同型 root。没有现成 accept CLI：`task_packet.py` 只读 list/show/next；`parent_gate_ledger.py` 是派生报表，不赋予接受资格。
8. 正式登记后再运行当前完整只读 derive，核对 W07 VALID_ACCEPTED/A05 CURRENT 和依赖快照 CAS。若失败如实保留错误并回到治理流程，不能以合成 ACCEPTED owner 调用 verify_owner 作为提前签发依据。全目录有其他 owner 缺口时总体 PARTIAL 不等于 W07 自动失败/通过；逐项检查 W07 输出。最终父任务接受还需 Root 按 canonical 流程维护 checkpoint/派生 ledger；本报告不代签。

## 最后只读检查命令

```powershell
& $lockedPython -B -X utf8 'D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/tools/task_packet.py' --plan 'D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/contracts/execution.plan.json' show W07-99 --state execution/v2.4/step_state.json
& $lockedPython -B -X utf8 execution/v2.4/formal_case_index.py --repo 'D:/作品集/ResearchOS/research-os' --state 'D:/作品集/ResearchOS/research-os/execution/v2.4/step_state.json' --plan 'D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/contracts/execution.plan.json'
```

Root 如需更新 `parent_gate_ledger.json`，在自己的串行状态写范围内运行其生成器并保存回执；本审查只读取现有派生 ledger。接受结果只覆盖生成时读取的 hash；后续相关源码、registry、工具、输入或目录清单变化需要重新资格验证。

## 当前待闭合项

以 snapshot 时间为准：卡仍为 IN_PROGRESS，旧 8017 已有当前字节漂移；它仅作字段样本。缺少本轮完全稳定源码下的四 native 绑定、新鲜三来源/13 H07 proof、完整当前 context/GLOBAL4、独立正式 review、Root 实际接收事件及 issuance、最终 canonical 登记与当前 derive。旧工具 SOURCE_READY review 不等于本轮产品 review；准备阶段 context 也不是 current-context。上述文件必须由相应真实参与者生成，不能由本预检拼造。
