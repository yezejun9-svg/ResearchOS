# W21 R03 当前评价策略独立复核

结论：`PARTIAL_WITH_FIXTURE_STARTUP_FAILURE`。A08 的当前纯函数公开证据绑定为 `PASS_IN_SCOPE`，但整批当前测试不能签为 PASS；既有正式 C07/C08/A08 verdict 不重签、不升级。目标源码为 `27ced22e73da7631d65bdd6e1844de24dd198065`。

## 执行边界

只在本目录保存复核材料；产品源码、规范、canonical 状态及原证据均未修改。执行前逐个追踪四个 W11 测试的 helper，记录在 `preflight.md`。测试只使用临时 SQLite、公开合成 artifact 和进程内 loopback fixture。protected 分支仅有分类元数据，没有 private payload。新增 overlay 只读原先已接受的 10 份公开 A08 响应，并调用纯验证函数。

没有执行 native runner、真实 provider、私有数据导出、旧对抗流程、30 次调用 producer、SOURCE3、CLI activation 或 S2。`ImportFrozenQualifications` / `prepareQualification` 可能查询安装服务，均未调用。本复核不证明当前安装服务 freshness 或真实 OS 隔离。

## 两次运行及证据完整性

| 运行 | 原始结果 | 退出码及限制 |
| --- | --- | --- |
| 第一次 | Go JSON 有 package PASS；5 个顶层测试和 22 个子测试 PASS；91 个语义断言 PASS，无失败断言 | 报告脚本解析被 Go 拆分的长 JSON 输出时失败，脚本 exit=1；Go OS exit 未持久化，不能推定为 0 |
| 第二次 | 90 个语义断言 PASS，无失败语义断言；`TestW11PromptBoundaries/json-body` 在业务调用之前因 loopback fixture readiness 超时失败，连带父测试/package FAIL | Go OS exit=1，已保存于 `tests.exit.txt`、`command.json`；没有 SKIP |

第一次原始文件 `tests-attempt-01.raw.jsonl` 的 SHA-256 为 `66731e33729e78b9219c12c7bf0250c3adede656f652191cf5af49946883722d`；第二次 `tests.raw.jsonl` 为 `e34b276bd9e3b39e053ef6858ab40fa89c93a810a7d12a619866a118ef384a41`。第二次 fixture 对 17731、17741、17743 的三个启动探针均失败，缺少当前这次的 json-body 语义断言；不能用第一次 PASS 掩盖第二次失败。

为修复报告解析而重复执行是本次流程缺陷。收到主 Agent 的禁止重跑指令后没有第三次执行；仅按测试聚合既存 Output 修复报告。后续应先保存 OS exit 与 raw，再解析，报告故障只重处理已有文件。

两次各自 before/after 的 625 个受审源码、SQL、契约、冻结 JSON 与工具链文件哈希均一致。固定 Go 路径、argv、cwd、环境和时间详见 `command.json`；Go 二进制 SHA-256 为 `d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490`。未把报告脚本 exit=0 当成 Go 测试 PASS。

## 当前语义结论

C07 的 required check、缺失引用和 artifact hash 失败仍阻止采用；新旧 manual decision 路径均拒绝绕过，maximum-score fixture 信号不能覆盖 deterministic FAIL。C08 的 timeout、model revision 变化、低置信度和矛盾证据均保持 abstain，BOUNDED_AUTO 请求拒绝；独立 requirement 操作继续可用。这些是公开 fixture 证据，不是生产可用性证明。

A08 新增的 48 个纯函数断言全部通过：两种语言各 24 项。原公开 SafeSummary 可被当前 validator 接受；DRAFT 到 FAILED 的保存响应保留同一契约和 acceptance 引用；当前 `qualificationReceiptBinding` 接受原有效证据，并拒绝八类重新计算哈希但语义错误的 receipt（input、policy、verifier、author、measurement、缺少 check、失败 check、check evidence）。五维 qualification key 的任一维变化均不能继承旧 receipt。

固定五维为 task_type=`evidence-validity`、language=`zh` / `zh-en`、provider=`typesafe`、model_revision=`jev-1.13.0`、rubric_revision=`objective-source-records-v1`。每个 key 是 development=30、holdout=15，未达到 60/30 阈值；两个 key 的 holdout 合计 30 不会授权任一个 key。状态仍为 `FAILED` / `ADVISORY` / authority `NONE`，原评估流程 `COMPLETED` 不改变资格失败。

原公开聚合数据合计 13 correct、17 abstain、30 total、0 false accept、0 false reject。zh 和 zh-en 各有 8 个 negative label，false-accept 分数分别为 0/8；nonabstained coverage 为 6/15 和 7/15，accept coverage 为 1/15 和 2/15。实际自动行动覆盖均为 0，cost 为 UNKNOWN。这些均来自已接受数据的机械推导，没有新 live 调用；详见 `safe-derived-metrics.json`。

## 历史复用与变化

C07/C08 接受基线为 `617e6b2b0f061373bb2bebd82bb488b3f9c7441d`；A08 为 `d6acd16f9144700c77d7bc0f3cb54464a16688d8`，原正式记录是 `execution/verifier/W11/6b9ede5e-9edb-4f07-af80-d8220ba6ccfa.json`。只读 10 份公开输入，并核对原 artifact manifest 中的 SHA-256，详见 `accepted-public-inputs.json`。

`historical-source-comparison.json` 是 28 个相关路径的比较子集，不声称依赖闭包完整。对 C07/C08：7 项字节不变、13 项变化、8 项不在原清单；对 A08：16 项不变、10 项变化、2 项不在原清单。A08 基线以来 `decision.go`、`adapters/decision/jev.go`、`adapters/protectedstore/frozen_summary.go` 字节不变；当前 `qualification_live.go` 使用共享纯 binding 收紧 receipt 校验，并核对聚合 hash 和 rates 后保留 FAILED/ADVISORY。此次只验证纯绑定，未执行 service 写入流程。

原 A08 的私有冻结、标签独立性、OS/service 隔离继续按既有接受证据复用；当前只补分类拒绝与公开绑定证据，不能重新认证隔离。逐条 C07-01..03、C08-01..03、A08-01..06 及 json-body 缺口映射在 `assertion-scope-map.json`，每条均标明 `formal_verdict_reissued=false`。

## 交付

原始输出、真实退出码、两次独立 source hash 清单、断言提取、逐条映射、输入来源和 overlay 源码均保留。`artifact-manifest.json` 对本目录除 manifest 自身之外的文件逐一记录 SHA-256 和大小。整体剩余限制是第二次 json-body fixture readiness 失败，以及本任务明确排除的真实服务/私有数据/OS 层证明；不据此开启其他阶段或修改正式状态。
