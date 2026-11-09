# Qualification projection A independent review — NOT_ACCEPTED

Candidate `525a9c923a8761a9491070123de3c94aa5618d71`, tree `ee490d97969fb85e2bc2eeeda067188ebb07045b`, base `4f4023c956f84d65743f39ce77d6c8899a21ada1`.

发现一个新增生产回归、一个无效阴性对照和一组必须补齐的验收证据，不能签发 LIMITED_SOURCE_ACCEPTED。候选源码保持冻结。

## Findings

1. **F01 / P1 — native-offline 资格入口回归。** `internal/runtimepolicy/qualification_projection.go:158-163` 在区分 Mu backend 之前要求 model_config，并对任何 runtime_qualification 返回错误。现有 `TestRuntimeCoordinatorNativeQualification` 在 exact base PASS，在 candidate FAIL：`GATE_FAILED: qualification projection: projection source config missing`。两次使用同一 argv/env，完整 JSON、native exit、cwd 都已保存到 `base-regressions.*` 与 `candidate-regressions.*`。应只对 Mu 投影执行严格资格校验，保留没有 marker 的 native-offline 原流程，并添加对应回归。

2. **F02 / P2 — adapter 篡改矩阵的克隆本身无效。** `adapters/runtime/qualification_projection_windows_test.go:82-90` 使用 json.Unmarshal，将数字转成 float64。`exactNumber` 仅接受 json.Number/int/int64，因此未篡改 clone 在 qualification max_calls 判断就失败；大部分字段检查失效也可能保持测试绿色。需用 UseNumber 克隆，先证明未改 clone 通过，再逐字段篡改。E 内独立 probe 因 Go internal import 范围限制编译失败，已保留原始诊断；未绕过、未增加 Source overlay。此结论依据源码控制流，不冒称该 probe 已动态证实。

3. **F03 / P2 — 全 consumer 和 normal/legacy 验收覆盖不足。** A04 要求的完整字段/authority/null/partial 矩阵未覆盖 brokerEffect、drain 等各 consumer；adapter 另有 F02。normal/legacy 新测试仅覆盖 8/1 staging 与 request validator，未证明原始 8/4 host/verifier；普通 session 集成在 base/candidate 都于 :146 MODEL_UNAVAILABLE 失败。该同基线失败可排除该项新增回归，不能算普通链路通过。A09 ordinary snapshot 和 A10 altered projection 应补充有有效正对照的隔离测试。

## Independently observed evidence

- Author raw 与本次重跑均为 72 test nodes = 19 top-level + 53 subtests，另 3 package pass；零 skip/fail。102 仅是作者静态断言调用点统计，未视为动态断言数。
- frozen SDK worker + loopback fixture：原 profile8/4 保持，effective1/0；实际 wire 无 coding tools，一次 MODEL；host provider identity 仍绑定 original config。
- hostile tool_calls fixture：一次 provider 请求，零 TOOL effects；未认定 B 的终态关闭。
- marker 在真实 Task 类型验证之后、manifest hash/INSERT 之前建立；stage、adapter prelaunch、brokerEffect preprepare、brokerModel pretransport、verifier、drain 都调用同一 helper。全字段/hash/canonical/deepcopy 设计主体连通，不能抵消 F01 与覆盖缺口。
- focused build 原生退出 0；独立 build binary 在删除前记录 SHA/size。
- source manifest/input/receipt hash 全匹配；15 文件 diff 属 allowlist；canonical binary patch 与现有 patch 字节一致，reverse check 通过；22 个 formatter 外部路径 blob 各自等于 HEAD。
- base/candidate tracked clean；Main HEAD/index/20 项既有 dirty 状态保留。并发 Root 允许的共享 checkpoint/ownership/handoff 差异以 guard-comparison.json 为准，非本 reviewer 写入。

## Evidence boundaries

Source 早期 compile、错误、skip、原始被覆盖 patch 等 full raw 缺失仍然缺失，SUPPLEMENT 与 diagnostics 原样保留。本次复跑仅增加新证据，不能补称原始日志已捕获。完整命令 argv、cwd、allowlisted env、native exit 和 raw hash 见 *.command.json / diagnostic-ledger.jsonl；详细 A01-A12 状态见 review.json。

仅 Source/隔离 fixture 审查；无实际 provider/Ollama/产品数据调用，无 Source/Main/package/实际 DB 修复，无安装包修改、旧 Run 修复或 B 闭合声明。formal 增量0/42，22 父任务保持开放。

## Cleanup policy result

本任务新 Dtemp/cache/build 和 E/__pycache__ 的已验证路径 Remove-Item 清理命令在启动前被自动策略拒绝（blocked by policy）。文件保留，未更换工具或路径绕过。该拒绝不影响已记录的源码/测试结论。
