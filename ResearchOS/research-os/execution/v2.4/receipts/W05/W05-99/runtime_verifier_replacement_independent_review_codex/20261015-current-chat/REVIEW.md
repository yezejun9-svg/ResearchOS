# 独立修订审查：LIMITED_SOURCE_ACCEPTED

候选 `4f4023c956f84d65743f39ce77d6c8899a21ada1`，tree `3db13a15cc52b2b0bd75cae3452c66509a9f55c9`。本轮接受 F1/F2 修订及相应限定 Source/Windows fixture 行为，未发现新的阻断问题。不是产品注册替换、安装包合格、真实模型 qualification、父任务或正式用例接受。formal increment=0，formal 0/42，22 个父任务保持 open。

本轮 reviewer 为 `codex:/root/verifier_revision_review`，按项目要求使用 gpt-6-astra/high 进行独立审查。没有修改候选源码、index、refs、Main、checkpoint 或旧 evidence；没有访问实际产品 DataRoot、GUI、凭据或网络模型。

## 修订判断

F1 已修复。plan v2 持久化 `history_sequence`、前驱 operation ID、plan SHA256 和 terminal event hash。全历史按 sequence 逐项校验连续性、前驱摘要和精确旧记录；事件内部仍验证 sequence/previous/hash 与合法状态转换。At 仅保留格式与审计用途，不决定先后顺序。commit 重验相同 causal head，并在发布后验证启动 gate；recover 检查其前驱，COMMITTED 与 ABORTED 都推进历史。旧 plan/schema 不被静默迁移，未知/歧义继续拒绝。原时间精度与跨事务时钟回退两个独立反例以原字节 overlay 重跑通过。时钟相等/倒退、fork、cycle、missing predecessor、摘要漂移、sequence gap、ABA stale plan、恢复后下一事务绑定均有本轮新鲜执行证据。

F2 已修复。所有 `local-verifier-` reserved principal、lineage 与 grant 先被枚举和校验，再判定具体 root 关系。缺 grant、缺 lineage、同时缺失/移走、错误派生 ID、额外 grant、孤立 lineage/grant 均拒绝；原 detached+grantless 双 child 反例通过。合法其他 root 要求有效 root 结构、child 派生 ID、唯一 project grant；允许其保留撤销状态，但全部 reserved 记录都进入 LineageHash。独立追加三种反例确认：预检后其他完整 root 的撤销、整树删除、grant 漂移均阻止 commit，注册字节不变且没有创建 journal。这验证了合法其他 root 不是可绕过 snapshot 的隐藏区。

## 新鲜执行与输入固定

- `01-focused`：native exit 0，15 个 top-level PASS，含子测试 91 PASS、1 SKIP、0 FAIL；包含 8 个真实 Windows 子进程终止点（各 exit 1）、11 次实际 control CLI 调用、preflight/commit/recover/repeat、startup gate before store.Open、ReplaceFile 外部 race UNKNOWN、只读 census/WAL、ACL/reparse/hardlink 及身份/安装负例。
- `02-original-probes`：原 reviewer probe 文件字节未改，3 PASS，exit 0。日志 SHA256 `b2a636ef8ea7faf2ba73d511fc15d452ad6ab147126cbcf4e7c183d87cf11a92`。
- `05-affected-regression`：`go test ./internal/host ./apps/control -count=1 -json`，native exit 0，73 个 top-level PASS，含子测试 188 PASS、15 SKIP、0 FAIL。跳过列表及原始原因保存在 summary/log，未视为通过。
- `06-extra-probes`：独立追加其他 root snapshot 漂移测试，1 top-level/3 子例，共 4 PASS，exit 0；overlay 不写候选源码。
- clean candidate 下独立 `go build` 与 CLI 测试内实际 build 均开启 `GOFLAGS=-buildvcs=true`。单独构建的 control 读回 `vcs.revision=4f4023c956f84d65743f39ce77d6c8899a21ada1`、`vcs.modified=false`。二进制 SHA256 `c4a3b498fc15120828427b237b8176710acfd7a9333cd24e9911fded9cd63e24`。这补足作者旧 HEAD+dirty 构建元数据边界；仍仅为本地测试构建，不是产品包接受。

每条执行记录保留实际 argv、cwd、environment allowlist、开始结束时间、数值 exit 和原始 log hash；GOPROXY/GOSUMDB=off，没有传入模型/provider 配置。所有尝试保存在 append-only attempt-ledger，当前 reviewer 执行失败数 0；历史失败与 skip 未删除或重置。

独立核对作者 FINAL-manifest 的 46 个文件引用，全部 hash/bytes 一致。revision patch 与 `git diff --binary --full-index c5ea3082 HEAD` 逐字节一致，仅 4 个 host 文件；cumulative patch 与 `git diff --binary --full-index c8b7adab HEAD` 一致，保持 exact8。710 个现存 tracked 源码/构建输入与作者/旧 reviewer evidence 文件前后 guard 完全相同；前后候选工作树均 clean。Git 对象修复是 Root 的独立工作，不作为本次 Source 接受或主仓完整性结论。

## 剩余边界

foreign-owner 负例仍因当前 token 不具备 WRITE_OWNER 明确 SKIP，未宣称跨 SID 的原生权限测试已经完成。其余完整 suite 的环境依赖 skip 同样不计通过。作者 managed legacy Mu synthetic 证据只核对冻结引用，本轮没有把它提升成真实 provider 或正式验收。

严格 exe owner/protected single-ACE 要求保留；后续实际包必须分别确认 manifest 与 exe ACL，不能由 fixture 推断实际安装满足。8 个真实进程终止点证明相应恢复边界，不等价于机器断电或任意 partial orphan 恢复证明。歧义仍保持 UNKNOWN。

接受只绑定此 commit/tree、scope 与 patch；Main 集成、实际包组合、原 DataRoot preflight/commit、正常重开及新的 qualification 由 Root 后续单独执行并留证，本报告不替代这些证据。
