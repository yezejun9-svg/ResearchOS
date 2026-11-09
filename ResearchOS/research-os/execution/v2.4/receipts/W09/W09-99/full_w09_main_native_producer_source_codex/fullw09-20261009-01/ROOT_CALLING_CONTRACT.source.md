# 三个 W09 Native selector 的 Source 交付

状态为 `SOURCE_READY_PENDING_INDEPENDENT_REVIEW`。本目录没有 Root scope、请求、registration、ModeProof、route lease 或 capture index，不提供执行授权。Main Source21、Canon、既有 C19 Native 及两个已成功 dispatcher 回执未修改。

| selector | Main 测试/断言 | mode | 后续 mode review |
|---|---|---|---|
| W09-G01 | 完整 5 tests / 8 IDs | FIXTURE | retrieval 一份 |
| W09-G02 | 完整 8 tests / 7 IDs | LIVE_WINDOWS | retrieval 一份 |
| A06 | 完整 8 tests / 7 IDs | FIXTURE | retrieval、security 两份不同 decision，可引用同一 Native |

三个 selector 都按 `./adapters/retrieval`、`./internal/domain` 顺序执行。G01 的完整集合包含两个 C19 子测试；此包没有 standalone C19 入口，不重跑旧两个 dispatcher，也不把旧 C19 结果拼入 G01。

`source.choice.json` 固定三个不同的 run ID、输出目录、私有 scratch 和回执目录，所有目录当前不存在。`compiler-source-blueprint.json` 固定 3905 个当前输入字节、19 个 module GoMod 和 Main 编译目录文件集合。353 个允许的 package 名称来自旧闭包加 retrieval 的两个测试变体，只是上限；真实 package 数保持 null，未来由实际两 package 的 Go list 输出确定。旧 MR2 实际闭包只有 domain 的测试变体，未提供可复用的完整两 package 测试程序资格，因此保留独立空 cache 编译路径。

非作者 review 的精确 schema、decision 值及必需绑定列在 `root-calling-contract.json`。review 必须绑定本次 HDF/MF、所有 caller、choice/blueprint、完整三个 selector 和 Source21，明确实际未执行、formal delta 0。Root 后续分别捕获本 Source 作者和 reviewer 的实际交付：固定 Root session 原始 header + communication metadata + agent_message 三行，校验真实源日志的 byte offsets/hash，不能只给自述 SHA。

Root 每个 selector 后续发行唯一 scope，并登记 `checkpoint.work_in_progress.w09_native_producer_scopes[selector_key]`、`path_ownership.card_path_bindings["W09-99"].subtasks["full_w09_main_native_producer_" + selector_key]` 和唯一 `FULL_W09_MAIN_NATIVE_PRODUCER_<selector_key>` worker。结构以 runtime `validate_authority` 中的 exact dictionaries 为准。lease 为唯一 32hex，必须有时区，期限最多 3600 秒，运行时仍有效；checkpoint revision > 371，ownership revision > 175。四个当前 Canon pins 在 Root 正式阶段提供，Source 准备阶段未读取或持有 Canon pair。

为避免 scope/vector 互相引用，scope 不含 canonical vector。Root 先发行 scope、真实工具读取该 scope 并封存原始工具 pair、登记 owner/worker，再封存当前四文件 vector，最后发行 request。request 精确字段是 schema、issued_by、selector、scope_ref、canonical_vector_ref、calling_contract_ref、scope_audit_ref。Root 原始工具 pair 必须来自固定 Root session 且包含 scope SHA；本包里的 audit control 是过去真实记录的有限样本，不能作为新 scope 授权。

按合同 `future_argv.prepare` 和 `future_argv.run` 各调用一次，四个位置参数为 selector、Root request 绝对路径、SHA256、bytes。两个 entrypoint 都先验证授权，缺失授权时不创建运行目录。prepare 只建立独立目录和空 cache；run 必须绑定同一 request/vector 和关闭干净的 prepare 回执。

未来 run 在持有 SourceReadGuard 时最多进行一次 `go list -test -deps -compiled -export -json` 和一次 Main producer。Go list 闭包必须包含两 package 的普通、test variant、test main，所有实际输入在冻结集合内，生成/导出物仅来自本次私有 cache，并在 producer 前持有。主 producer 使用精确 Main runner，通过私有 UUID 对象固定输出 run；原始 Main 和 stdlib UUID 字节不变。所有后代在 unnamed exclusive Windows Job 中，必须得到严格整数 PID、uint64 FILETIME、原始 stdout/stderr、实际外层 exit 和完整 Job/guard 收尾。

scope、lease、Canon、Source21、目录集合在准备、list 前、producer 前、launcher 中、packet 校验前重复验证。任一失败即停止，无自动重试；关闭 guard、归档 Native packet 和保存失败诊断独立尝试，保留原始异常与二级错误。未知独立子进程 exit 保持 null。Source 控制没有调用 Go、Native、SQL、dispatcher 或模型。

实际产物验证使用 Main `verify_native`、`verify_owned`、`verify_a06`；G01 另验证 C19 闭包。G02 的原始 Windows/Unicode/root-replacement/junction 证据留在 Native packet，LIVE_WINDOWS ModeProof 仍需后续独立 review。Source 控制和 Native packet 均不能决定 FormalCaseAccepted。

原机械诊断 1026、1029 在 `original-diagnostics.json` 及真实 session 原始工具 pair 中保留，不改为 PASS。正向与逆向 diff 是本包 runtime 相对已合格 C19 v2 runtime 的 Source 变换；逆向检查逐字节恢复原始文件，未写回旧 Source 或 Main。
