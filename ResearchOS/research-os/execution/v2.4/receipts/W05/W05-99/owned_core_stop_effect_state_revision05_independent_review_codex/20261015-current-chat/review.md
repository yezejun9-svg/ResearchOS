# STOP-r5 独立审查

结论：SUPPORTED_WITH_LIMITS。candidate 37a1f6d3e9d1c64b0d5fab5d30bc8000dd4ac373 / tree b9c88515d6663c8af372bb05cccc931410c3368b 的 STOP-R4-F01 修复得到本轮独立 Source、真实 SQLite store 和编译后 CLI 证据支持。没有新增 Source finding；Root 尚需自行采纳，actual/formal 增量均为 0。

审查覆盖 full19 生产调用链、19 组字段绑定、取消检查及 owner/ACE/保留句柄边界。与 r4 相比 17 个文件逐字节不变；exact2 delta 中生产仅将最新 effect 的 state != CONFIRMED 改为 IS NOT CONFIRMED，保留 project/run/effect_key/max(sequence)、唯一 CONFIRMED MODEL 及原 request/dispatch 绑定。不将历史较旧行当成最新状态。

- 独立 missing/null 两例、独立有限16项、author preflight/reserved16项均通过 native Go。missing/null 新行计入 NonModelEffects=1，既有 ConfirmedModelEffects=1，ExactOldSubjectSafe=false。
- 两个全新实际编译 PREFLIGHT_ONLY CLI 否定用例均 STOP_UNAVAILABLE；每例 87 表/36 行/quick_check=ok，原 native 身份仍存活且 census 不变；均未编译 STOP grant，无 STOP_ATTEMPT/TERMINATE_INTENT，无停止调用。fixture 后续清理与产品信号计数分开。
- 一个全新有效基线双 compiled grant 正例得到 STOPPED_LEASE_VERIFIED，一次 TerminateProcess、retained handle exit_observed=true、numeric exit=1381191507、before_signal=false；postflight 87 表/35 行及全部 census 与 baseline 相同。inspect 和 repeat commit 同值且 operation journal 哈希不变。未伪造旧 worker/verifier 原生等待：这些历史证明为明确标识的 synthetic fixture。

全部 SQLite/dataRoot/operations/journals/build/cache/Source/evidence 在 D；新许可 C root 仅两个 fixture/parent exe，复制与 D build hash 一致，owner/DACL 链已保存。未重跑或追认旧 author C data/journal 越界，也未改变共享/祖先 ACL。旧 r4 ownerACL 支持保留，未重复整个旧矩阵。新 C 私有镜像通过不说明 unsafe D 安装自动合格；同 SID、管理员/OS actor 不在恶意隔离保证内。

限制仍包括完整 Commit 在其自身 durable intent 后取消/过期、foreign SID 执行、power loss、hostile race、deeper SafetySnapshot/history 和异常 JSON 编码分支。retained WaitForSingleObject 成功由原生调用代码路径与 exit_observed 支持，journal 没有另存独立 numeric wait-result 字段；不能补造旧 Wait 证据。未创建新 boot/proof class，未接触原始 Root/Core/Desktop/DB/API/provider/model/keys/worker。

命令诊断：0001 尝试不存在的父 AGENTS 失败，原始退出和错误保留；首 recipe 的 scope placeholder/shell 名称不精确作为真实记录限制，不补称已预写。0002/0003 以精确脚本恢复读取并核验 scope。nested logger 的 mode 由预写 0018.ps1 指定而未重复进 relevant_environment map。正例两次跨阶段拒绝 exit1 是预期断言。旧 Root 8 mixed groups 与 author6非零分类只引用，不重计、不清零。

review.json、coverage.json、findings.json、limits.json、failure-ledger.json、source-fixture-verification.json、command-index.json 和 FINAL-manifest.json 组成审查包。仅本任务可再生 cache/warm exe 已清理；三份原生 fixture 数据/operations 与归档证据保留。

封存诊断：0024 因 0001 失败发生在 stdout 文件建立前而触发 FileNotFoundError；0025 明确登记该缺失，不补造空 stdout。诊断及原失败脚本保留，不构成新增 Source 缺陷。最终封存命令的 stdout/stderr/exit 在其返回后闭合，作为邻接回执保留并显式排除自身哈希循环。
