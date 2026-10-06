# W21 R01 / R07 当前定向核查

结论：`PASS_TARGETED_DELTA_WITH_EXPLICIT_HISTORICAL_REUSE`。在 `27ced22e73da7631d65bdd6e1844de24dd198065` 上，指定 6 个 selector 全部通过，34 条完整 assertion、0 skip、Go 实际退出码 0。测试前后及分析结束时 325 个受检源文件哈希一致。本报告不改变正式 42 case 状态，不签发完整 case 重验结论。

| 工作项 | 当前实际执行 | 断言数 | 保留的历史证据与限制 |
|---|---|---:|---|
| R01 | W04 context recovery/restricted、W17 C02 project isolation | 27 | C01 冻结模型 transcript 和已接受 parser replay 分开复用；没有新模型续跑，也未覆盖所有新增 planning/research context |
| R07 | W09 C19 origin/unknown、chain invalidation、A06 HTTP invalidation/context | 7 | A06 junction/root identity 与 fallback/cache 仅复用历史证据，没有再次执行 |

实际 argv、时间、Go 退出码见 `execution.json`，完整原始日志见 `go-test.raw.jsonl`，34 条 assertion 的原始起止行见 `current-assertions.json`。`assertion-map.json` 逐条绑定原 C01/C02/C19/A06 共 11 项冻结验收断言、旧验收回执、当前证据与未覆盖边界。

C02 在真实 loopback HTTP 服务上检查 reader/planner/executor 的 A 正向读取、B 越权拒绝、共享来源范围与版本、无 grant 拒绝、context/materialization 和审计日志：正文及日志的 B 秘密标记泄漏为 0。W04 restricted 使用公开合成的零字节标记对象，未连接 Protected store。其余调用使用本地 SQLite、HTTP handler 与本地文件快照。

`c01-archive-check.json` 记录重新机械核对的冻结 input/prompt、stdout/stderr、manifest、record/version vector、当前 B/历史 A 决策、425 计算结果、零追问、封存计算日志和确定性 FIXTURE 验收绑定。当前 `adapters/runtime/codex.go` 与已接受的 `2c1529f` parser replay 字节一致。因此复用既有 parser replay；本次没有新 Go parser replay、CLI 或 provider 调用。原 live revision 仍是 `7d57b24`，provider model revision/cost 仍未知，原外部 CLI 二进制只保留历史证明。

`current-contract-delta.json` 对旧 Git 版本与当前文件分别核对哈希。retrieval adapter、Windows root identity 与 `retrieval.go` 未变；context、local retrieval 与部分共享授权/HTTP 文件已变，定向测试补验这些交叉路径。该清单不是已证明的传递依赖闭包，不能凭未变 adapter 宣称完整当前 A06 或 C01 验收。

执行记录包含一次包装器故障：首次 Go raw 的 6 test 与 package 都为 PASS，但 Python 按单个 Output 解析长 JSON 时失败，Go 退出码未在异常前保存。其全部原始证据保留于 `attempt-1-parser-failed/`，退出码不可推断。修正为拼接完整行且先保存实际退出码后，第二次指定执行得到实际 Go exit 0；之后未扩大或继续重复测试。两次执行均保留，不把首次包装器失败描述成产品失败。

本批没有 native child/runtime、受保护材料、外部 provider、生产激活、旧 S2/CLI/activation/SOURCE 重跑、blocked cleanup 或数据库生产操作。只写本目录 verifier 证据，没有修改 Go、规格、canonical 状态或旧回执。

主批次 R05/R08/R09 的只读独立核查另见 `root-batches-review.md` 与 `.json`：分别 11/18、9/54、2/19 项 test/assertion，R05 Go 退出码保持未知，R08/R09 已保存实际退出码 0。没有重跑这些测试，也未签发完整 C11–C16、A02/A03 或 A12。
