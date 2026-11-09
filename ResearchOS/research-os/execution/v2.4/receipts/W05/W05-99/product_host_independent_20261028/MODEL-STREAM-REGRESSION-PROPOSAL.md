# ModelStream 定向回归必要性与范围提案

结论：`RELEVANT_REGRESSION_FIXTURE_NOT_QUALIFIED`。7 个 TestCLIModelStream 顶层测试与 exact14 的 CLI 入口、discovery/config 路由及 Native3 credential 改动直接相关；现有记录全部在缺少 RESEARCHOS_NODE / RESEARCHOS_MU_BUNDLE 时退出，不能称通过，也未运行其实际流断言。建议 Root 单列 bounded fixture scope 后执行，本审查未执行。

源码依据：apps/cli/cli_model_stream_integration_windows_test.go:43 调用单用例 TLS 子进程，:46–47 在缺 env 时 Fatal，:65–99 构建临时 DB / in-process Host / HTTP / named-pipe Native3，:107–117 构建真实 CLI 并执行 init，:281 无 argv 启动真实 CLI，:331 写入普通 stdin，:466 写 /cancel。这实际覆盖本次 main.go 裸入口及 cli_contract.go / cli_native.go / cli_verbs.go 共用路径。它使用无 product marker 的临时 executable，属于 dev-mode 非回归证据；不覆盖 installed productHost、Electron singleton 或真实产品 Core。

建议只运行 ^TestCLIModelStream 前缀的 7 个顶层测试：CausalDurableJSONL、InterruptedPrefix、CancelObservedPrefix、SecretQuarantine、DurableCommitFailure、PipelinedTerminal、SemanticSecretQuarantine（后者 5 个子项）。前 3 与 PipelinedTerminal 对本次保留 JSONL / stdin / 取消链最直接；其他异常结果与秘密隔离分支共用 fixture，可一并在有界范围补齐。不得借此前缀顺带跑整个 apps/cli 或 boundary renderer suite。

候选环境：冻结 source 后，实核 pinned Go、已构建 Node 和 Mu bundle 的路径、hash、完整 bundle 依赖树；RESEARCHOS_NODE 与 RESEARCHOS_MU_BUNDLE 使用经核验当前 build 产物；RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR、TEMP、TMP、GOCACHE、GOTMPDIR 设到新 owned 目录，隔离真实 CLI config/discovery/credential env。测试自行注入的 fixture credential 保留，不读取用户 credential。未授权前不写执行 scope、不启动测试。

执行性质必须如实标记：真实 CLI 子进程 + 真实 Native3 named pipe + Node/Mu worker + 本机 HTTP/TLS 模型 fixture；不是纯 mock，不是外部 provider，不是 Electron/Core 产品启动，不是正式用例接受。包含本地 DB 和 Native3 的真实 OS 行为，因此当前仅 source/build/mock scope 不足以默许执行。Scope 需明确 PID 所有权、临时根、超时及清理边界。Go test 及每个 TLS 子进程原始 stdout/stderr/exit/source/tool pins 必须留证；旧缺 env 失败保持不变。

本次判断仅静态实读现有测试和 exact14 diff；新增 native_runs=0，external_provider_calls=0，formal_increment=0。Root 若本轮先作限定 source/build 接受，应显式保留此 fixture 未资格及 installed CLI 流实际门。