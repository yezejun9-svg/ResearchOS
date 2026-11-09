# W05 A21 v2 restored21 Root actual caller Source

结论：`SOURCE_PREPARED_PENDING_INDEPENDENT_CALLER_REVIEW_AND_ROOT_ACTUAL`。此包只准备后续 Root 实际调用，不签发执行授权、runtime PASS、Main 采用或正式接受。A21 v2 原 Source 独审为 `SOURCE_ACCEPTED_P2_ADDRESSED_PENDING_RUNTIME_QUALIFICATION`，实际 Go 测试仍为 0。

固定源输入是已独立接受的 H20R2 public fixture A20→plain21 的 61 个 Source refs（实际 9 PASS）及 A21 v2 五文件 Source overlay。三个既有文件只增加 restored21 分支、恢复 policy 和 CLI 文案；A21 新增两份 domain 文件，因此组合为 63 个源文件。`backup_upgrade.go` 的 H20 分发保留。A21 测试先调用 H20 `UpgradeLocal`，断言 plain21 有 21 条 migration、无 client_sessions，再进行 session-ready21→22；测试同时比较返回与磁盘 `Recovery` 的完整序列化值。程序字节仍是 public fixture，真实维护版 21/22 release/program provenance 保持 OPEN。

`contract.json` 固定新 worktree、隔离环境、isolation/validation receipts，固定 H20 actual 和 A21 v2 的 HDF/MF/overlay 引用，列出九个父测试及四个漂移叶子的选择合同。Root 应先让非作者独审本 caller Source；随后由 Root 提供当前 HEAD 以及 checkpoint、path_ownership、step_state、commands 四个精确 SHA/bytes（checkpoint 另带 revision）。`prepare_root_actual.py` 只可由 Root 在批准的执行阶段运行，使用已拥有的 Windows Job helper 创建新 detached sparse worktree，保留实际 Git argv/result/raw stdout/stderr，严守四个 Canon ref 的前后字节。它不绑定历史 CP revision。

`validate_root_actual.py` 在隔离 worktree 中按 H20 61 + A21 五文件精确组合，持有 SourceReadGuard；Go format 后继续持有候选 Source refs，再用 `go list -test -deps -compiled -tags=researchos_native_recovery_harness -json` 记录全部编译输入、embed、产品范围和工具 inventory。它仅编译 `internal/domain` tagged test binary，通过官方 test2json 选择精确九父；预期原始 JSONL 有 13 个唯一 run 与 13 个 pass、零 fail/skip、包级 pass，明确拒绝零断言。每次外部调用使用 Owned Windows Job 和二进制 stdout/stderr 句柄，保存完整 argv、结果、exit 与 raw archive，所有 Job、Source guard 和句柄必须关闭。PID/FILETIME 应保持 Python int 或十进制字符串；Root 后续复核不得经 JavaScript Number 缩窄。

`validation.closed.json` 若成功只表示开发组件 `accepted H20 fixture plain21 → session-ready21 → 22` 与 returned/disk report 一致；不外推到 public coordinator 晚期故障无发布、真实 21/22 程序、Owner、B 分支、完整 20→24、formal42 或 single-writer cutover。实际调用的测试若失败，脚本仍封存每次 invocation 的完整原始结果，并显式写 FAILED closed status；Root 按现场证据处理。

本 Source 构造只执行 Python AST、字节 hash、精确路径和文本数据流检查。40 项通过，125 个输入 refs；SourceReadGuard 已关闭、零 retained handles；Go/parser/compiler/formatter/test2json/native/SQL/Git/product CLI/model 实际运行数为 0。唯一新原始失败为 PowerShell 只读比较查询的 ParserError，Root 已分配 945，详见 `original-failure.945.json`。由于原工具调用只转发了 stdout/stderr 文本，chunk id 与 process exit 元数据未保留，记录为 NULL，未伪造。

STOP / FINAL；等待独立 caller Source 审查和 Root 实际验证。
