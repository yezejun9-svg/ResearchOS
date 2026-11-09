# 阶段二：受信本地资格执行 Source 候选

候选提交 `c9e47c6cd16946ac02a874422a894249f87c6c50`，父提交为阶段一冻结 `a57ca3e3`。隔离 worktree：`D:/作品集/ResearchOS/research-os/.local/worktrees/w05-runtime-qualification-source-20261012`。本目录是新证据包；阶段一冻结证据、Main、Canon、失败计数均未改写。

结论：完成可审查的 Source 实现，并在隔离临时数据库用真实 Host、Mu SDK/AppContainer 和单独 verifier.exe 贯通 synthetic SSE 资格执行及普通会话执行。**真实模型调用为 0；不是实际 Ollama 资格、Desktop 完整交互验收、protected holdout 或 W05/Main24 正式完成。**

## 实现与边界

受信管理请求冻结 Owner/project/session/model/runtime/task/plan/profile 和授权目的、期限。control 新增 `--runtime-qualification-request` 与 `--runtime-verifier-manifest`；只允许正常 Host composition，不扩展 frozen `/v2/command` 或三种 Native frame。它是后续 Desktop privileged producer 可复用的启动组件，当前没有新增 renderer 按钮或配置后自动执行。已有 control 持有 data-root lease 时明确拒绝消费请求，要求管理端完成有序重启，不能创建第二 coordinator。

唯一 coordinator 在 scan lock 内检查当前配置、原计划、Owner、executor 空闲和现有 authority，按原 Begin gates 生成原 Run/lease，以不含 lease 的私有 idempotency 回执一次性消费请求，再通过同一 coordinator 的 `RunAdmitted` 执行。已消费、失效、失败状态不自动重试。

Host 重新验证原生 OS Owner；固定 purpose verifier 的安装清单绑定实际 exe SHA、声明的 SourceCommit、固定 protocol/service 和空参数。启动后核验 Windows image hash、PID、创建时间并进行 nonce 握手。服务根由真实管理安装行为显式登记，不靠任意新 ID 推断独立性；根无项目 grant、无 credential，项目子 principal 只有 VERIFIER，并调用现有 `RegisterExecutionIdentity` 记录 parent/root。已有撤销、权限或安装漂移均拒绝。独立性仅为应用进程与 authority lineage 分离，不声称 OS 级保护或 protected holdout。

Verifier 短期 token 仅在原 Run settled 后发行，经专用继承匿名管道交给核验进程，不进入命令行、环境、renderer、scheduler、worker、配置文件或日志，结束后撤销。它自行从 API 重新读取当前 Task/Run、sealed profile/observed LOG/outputs，与受信不可变 snapshot 校对，执行同一确定性核验，再调用现有 `/acceptances` 由服务端重算和 `/runtimes/{id}/qualify`。不创建 PASS 回执、不改变原 acceptance/admission gates。Host 只有在原有 AVAILABLE/qualification 检查通过后，才能按 Owner 原请求签发精确 `mu_turn` purpose 期限。

`runtimeSetupGrants` 只允许一个原项目基础 grant，以及同一个 Owner 派生 executor、同一个 prepared runtime/plan、匹配原 Task/Run/epoch 的已有资格 claim 或原 qualified Mu dispatch grant。无关项目、task-only、missing run、wrong task、restricted 改写均拒绝；不泛化放开 grant 数量。

## UNKNOWN 核验修正

原始生产 broker 已在无上界本地调用中生成 `UNKNOWN/UNKNOWN/money:null/reservation_id:null`，旧 `verifyMuTurn` 只认 RESERVE/UPPER_BOUND 导致独立核验失败。`attempt09` 保存了实际拒绝原因 `Bounded durable effect reservation missing.`，没有补假上界或把钱写成 0。

新增分支限于 prepared credential-free numeric-loopback MODEL、`max_cost:null`、原 `none` credential revision。核对唯一原 ledger、原 provider key/event/run/project/time、原请求 hash、原 null money/reservation；完整真实 run budget scopes 进入两次 acceptance snapshot，所有 ancestor 必须 UNLIMITED_AMOUNT + cap:null + ALLOW_AND_RECORD，完整无环链终结于 GLOBAL。当前 policy 的有效/修改时间晚于原 Run 即拒绝，策略漂移不能被复算掩盖。原 RESERVE/UPPER_BOUND 分支完整保留，其他 model/output/profile/receipt/native/epoch/context/revocation 检查继续运行。

## 检查与原始失败

- `attempt13-final-regression.txt`：原 bounded Mu 独立核验、伪造拒绝、原资格 root/profile/capability/budget gates、purpose revocation、窄 grant、请求消费、17 个 UNKNOWN 反例及 verifier 私有帧/URL 反例通过。DOMAIN 文件与最终提交一致；之后仅补充 verifier 输出封印交叉核对及 Host 直接调用安装参数校验。
- `attempt14-frozen-source-synthetic.txt`：最终提交构建的 verifier.exe，真实 Host/native Mu、独立进程及服务器 acceptance/qualify、精确目的授权、普通 `session.send` SETTLED；synthetic SSE 2 次，真实模型 0；子 verifier token 已撤销；原两个 MODEL ledger 均 UNKNOWN/null，未写 ACTUAL、未释放。
- `attempt15-frozen-verifier.txt`：最终提交私有管道格式、大小、未知字段和不可信 URL 拒绝通过。
- `build-provenance.txt`：control.exe 与 verifier.exe 的 Go build metadata 均绑定最终提交，`vcs.modified=false`。

失败原样保留：attempt01 空间不足的完整 checkout；attempt05/07/08 旧核验拒绝；attempt06 资源读取暂时不可用；attempt09 精确拒绝定位；attempt12 新增账本断言误计入无关 inventory bootstrap fixture 的资源零预留，修正查询只核对实际 MODEL effect keys 后 attempt14 通过。未删除旧失败、未把 fixture 运行推广为产品资格。

## 后续集成条件

Root/非作者独审本冻结 Source，特别审查服务身份实际来源、进程/私有凭据边界、唯一 coordinator 生命周期、UNKNOWN 分支与窄 grant 复用。Desktop 正常设置/privileged producer 集成由另一支路处理。实际本地模型资格需 Root 在 Source 独审后单独按已授权范围执行一次，并保留原运行证据；付费模型和 protected holdout 不在本候选结果中。

重现 synthetic fixture：Go 1.27.1；先构建 `./apps/runtime-verifier`，运行 `go test ./internal/host -count=1 -run '^TestManagedLocalRuntimeQualificationSyntheticTransport$' -v -args --local-runtime-assets-dir=<固定真实Mu资源目录> --local-runtime-verifier-executable=<候选exe绝对路径>`。该测试硬编码使用 httptest synthetic model server，资源路径仅显式测试 flags，不写入产品默认配置。
