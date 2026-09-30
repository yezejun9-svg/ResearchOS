# ResearchOS 当前施工交接

当前可交付的是 Windows x64 开发夹具包与可核验源码。完整产品交付仍未通过：42 例历史结果为 34 PASS、6 NOT_RUN、1 BLOCKED、1 PARTIAL；22 个 WBS 中仅 7 个整阶段历史接受。历史 PASS 不代表所有用例已在最终源码重新接受。

永久项目身份为 `aede0678-7308-43dc-b9f2-cfe3d90cfdfb`，规格快照 SHA-256 为 `2949300fd249ea814714411a509d7fe25323e4be6fc11e6f2077c24fa76c351e`。继续工作先读仓库 `AGENTS.md`、`execution/project_identity.json`、`execution/checkpoint.json`、`execution/bootstrap_ledger.json`、`execution/path_ownership.json` 和原规格 `spec/v2.0/00_START_HERE.md`，再核对现场 Git 与进程。保留现有未提交文件，不自动操作原数据库。

## 本轮已整合内容

- 当前控制实例的五阶段证明有独立的持久数据复算；实测没有收益，稳定槽位保留。实例已停止，当前 OS 运行真实性仍未验证，正式发布权限保持关闭。
- 恢复上下文绑定实际 manifest、路径身份和不可变 journal，修复了两项独立审查缺陷。恢复停在 `RECOVERING` 和 `BLOCKED_RECOVERY_AUTHORIZATION`；实际新代授权、发布切换与回滚未完成。
- UI 能检测 SSE 长时无数据并刷新快照。浏览器证据部分通过，五次失败保留；真实冻结恢复、Windows 休眠和手机监督尚未验证。
- 手动研究周期的合法负向结论可关闭为 COMPLETE。仅没有持久监控绑定、没有自动工作记录的周期可使用该分支，并重验当前调用者、来源和封存字节；自动监控的独立验收链保持原门。

以上范围分别见 `execution/verifier/W16/current-control-admission/3695633/`、`execution/verifier/W16/recovery-context-fence/9253b99/`、`execution/verifier/W13/ui-recovery-c26/`、`execution/verifier/W08/manual-disposition/57ef089/`。这些是原源码仓库中的外部证据；开发 ZIP 不复制私有留出或完整施工回执。

## 交付包与运行入口

精确源码 commit、ZIP 路径、SHA-256、双构建比较和独立夹具检查定位由 `execution/checkpoint.json` 的当前交付记录及 `execution/verifier/W21/current-handoff-index/6374df3/` 的增量定位提供。索引原快照不覆盖，后续定位单独追加。

按 `docs/installation/README.md` 验证并解压包，在新绝对数据路径和空闲 loopback 端口用 `scripts/start.ps1 -Fresh` 启动，以 `scripts/stop.ps1` 停止。停止脚本保留数据，并核验实例身份。该入口只启动临时开发实例；不能用于现有权威数据库迁移、SCM 安装或正式发布。

原实例与受保护服务的最后登记 PID 为 32736、79136，仅作续跑线索。使用前需重核身份；不要仅凭 PID 停止进程。原 schema13 数据与保护服务保持原状，已拒绝的启用动作不自动重试。

## 未闭合项与恢复条件

`RQ-W05-CLI-POLICY-001` 需要受支持、已授权的真实 CLI 工具能力；`RQ-W17-LOCAL-CUTOVER-POLICY-001` 需要受支持的迁移实例凭据签发与启用。两项操作此前均在执行前被自动审批拒绝，记录的理由为 `blocked by policy`。恢复条件不是绕过拒绝的授权。

真实闭环、独立 Windows 服务身份、W18 恢复资格、手机访问、物理休眠和至少八小时运行、干净 Windows 安装、完整当前版本 42 例以及完整切换/回滚证据仍缺。费用实际值未知时保留 null，金额上限保持 cap=null。Jev 已完成的历史资格保持 FAILED/ADVISORY/NONE，不能提升自动决策权限。

许可证仍有两项缺口：ResearchOS 主模块许可未指定；安装的 Rolldown Windows native binding 第三方声明完整性未证实。原依赖与许可证据保留，不能自动替用户选择主模块许可。

当前版本证据的准确限制在 `execution/verifier/W21/current-handoff-index/6374df3/cases.md` 和 `wbs.md`。同一失败输入最多自动重试两次，三轮没有新证据或指标进步后停止对应支路；不能通过新窗口或新候选编号归零。已通过且无相关改动的用例不重复执行。

## 下一步

依照开放资源请求恢复真实运行器与目标实例启用后，只重新验证受当前版本影响的正式断言及资源门，再完成真实设备、隔夜和恢复验收。不能把本交接、包校验或局部 PASS 作为 W21-G01、A15 或整个 Goal 完成。
