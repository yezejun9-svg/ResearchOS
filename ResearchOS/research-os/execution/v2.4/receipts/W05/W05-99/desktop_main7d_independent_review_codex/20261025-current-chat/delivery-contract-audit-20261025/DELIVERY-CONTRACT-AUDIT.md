# CLI / Desktop 真实交付合同审查

结论：`DELIVERY_GAPS_CONFIRMED_OWNED_IMPLEMENTATION_CAN_PROCEED`。Main 当前为 `ecc28dd3c91a0f68dcddb41b53325aa7f0e81419`；读取时 CP556、ownership342。当前开发构建、一次 owned native smoke 和 Main exact7 整合证据可复用其明确范围，不能据此接受安装发行、普通用户反复使用、W13 或 A15。建议立即推进独立 owned 安装工程；C57 原数据恢复所需管理员会话仅阻对应恢复分支。

本审查只读合同、登记、施工状态和已经封存的当前候选审查报告；不运行 GUI/Core、构建、测试或 dispatcher，不读取原业务数据库，不修改源代码、共享登记或冻结门槛。34 个实读输入已复制并按原始字节封存。`current_spec.json` 实际位于 `execution/v2.4/`，指向 `.local/worktrees/v24-continuation/spec/v2.4`；PACKAGE_MANIFEST 与 execution.plan 的 SHA-256 均与指针相符。合同的初始 NOT_RUN/NOT_STARTED 不被当作当前实施状态。

## 要求、现有证据与缺口

| 用户要求与合同定位 | 当前可使用的证据 | 尚缺的交付行为 / 证据 |
|---|---|---|
| 两个发行件：product P07、delivery U08、A15-06/07；蓝图 §11 | R3 源码/完整开发树审查；Main exact7 整合审查 | 可安装 CLI 发行件与 Desktop Windows 安装件，各自版本/hash，安装后真实入口。本文未对旧发行物作全面库存，不能把旧包自动判不存在或等同当前包。 |
| 普通 Windows 11 x64 用户，无开发 Node/Go/Bun、无手工后台命令；蓝图204、212 | 开发树包含 Electron/Core/Mu 等本次已审查组成；owned smoke 使用绑定工具和新状态 | 干净用户环境的安装、开始菜单启动、新终端 CLI 启动；脱离源码目录和开发工具链的实测。把开发树压缩即发行不满足此要求。 |
| 固定安装位置、数据持续保留、CLI/Desktop 同核心；蓝图96、204-206 | 本次新状态 smoke 的 READY、React、host.status、匹配进程退出；仅一次启动 | 默认安装 `%LOCALAPPDATA%\Programs\ResearchOS`，业务数据 `%LOCALAPPDATA%\ResearchOS`；重复启动发现同版本兼容 core、同数据/会话、单写入者、身份鉴别与离线诊断。开发 launcher 明确拒绝已存在状态目录（STATE_NOT_FRESH），不能成为普通入口。 |
| 升级与失败回退；W20-01步骤3、蓝图210 | 当前开发文档明确不提供升级路径 | 检查活动任务与数据库版本；安全检查点、备份、版本兼容；新版本失败保持旧版本与备份可启动；实际升级和回退回执。不能只换 exe 或凭文件 hash 宣称迁移安全。 |
| 卸载默认保留业务数据；A15、蓝图210 | 当前开发树仅隔离新状态 | 明确安装目录/数据目录/项目目录边界，卸载不默删数据；删除数据为独立明确选择。实际卸载后证据与重装复用数据；无需触碰 C57 原数据。 |
| 完整 Desktop 主流程；W13-P03/U04、C23-05/06、A15-05 | 原生 smoke 仅确认入口、渲染、状态请求和关闭；W13-01/02 有范围受限的已接受增量 | 项目目录、实际模型设置、会话、工具、文件/diff/成果、Goal 控制和 typed 错误；11视图与最终真实 API/事件对应。nav 数量与窗口标题不能替代流程。W13可区分 fixture 阶段，W20必须真实最终后端。 |
| 正常关闭、隔天接续、CLI→Desktop→CLI；P02/P05/P06、U03/U05 | 单次 smoke 证明其 owned Core 退出，未运行持续会话 | 持续宿主、session/core 发现、双端交接与恢复证据；现有正常退出证据不等于托盘继续、睡眠重启或隔夜资格。 |
| 可复现交付与完整验收；A15-01至07、W20-G01/G02/G03 | 同一候选字节的已封存构建与 smoke 可引用；Main 整合已验证 | 构建 revision/锁/依赖/许可/SBOM/配置模板、秘密扫描、安装与恢复文档及原始回执；重跑对账、其余41例有效结果再纳入A15，不能借发行包将当前 formal0/42 提升。 |

合同没有冻结 MSI、NSIS、MSIX 等具体安装格式。选择须服从现有可复用打包器、普通用户可安装与实际入口等要求；不另造格式门槛。签名状态如实标记，无签名资源不等于不可开展本地工程，不得写“已签名/无警告”。禁用上游更新地址；未配置自有更新服务时允许经验证的本地新安装包更新（蓝图210-212）。

## 平台登记与卡片边界

`CURRENT-CONTRACT-AND-REGISTRY.json` 按 dispatcher 的实际 auto 选择逻辑保存每键完整条目；未调用 dispatcher，以免生成无意义执行回执。

- v2.4 `desktop.shell_launch` 仍 UNBOUND，旧 argv 为 `apps/desktop`；`desktop.installer_build` 仍 UNBOUND，旧 cwd/argv 指向 `third_party/mu/desktop` / `dist:win`。不能仅把 state 改成 BOUND，更不能把 fresh-state-only development launcher冒充普通用户 shell。
- v2.4 没有 `release.reproduce` 与 `acceptance.audit`，auto 回退 v2.0；旧 `release.reproduce` 为 UNBOUND；旧 `acceptance.audit` 只绑定 W16/C20，W20/A15 与 W20-G01 等选择器均不受理。需要平台 owner 串行登记真实 handler、argv/cwd、精确 selectors、模式、超时、环境名与实际 assertion IDs，同时保留既有 C20 行为。
- `test.ui.routes` 的 W13-01 路径运行 injected-fake 检查，C23 转发旧 workflow；本次新 native smoke 不会自动进入该处理器或成为 C23 全例。只有真正实现并验证对应选择器才能扩展登记。
- W20-01 依赖 W13-03、W17-03、W18-02。当前 step_state：W13-03 BLOCKED（既有 NVDA 前台限制与被拒审查，不重试绕过），W18-02 ACCEPTED；W17-03 与 W20 各卡未有状态行，不能按缺行当已接受。W20-02 还依赖 W16-99/W19-99；本次不审查或改变这些父门。
- Root 可另注册明确的 DEVELOPMENT 候选工程范围推进无关缺口；不得借此跳过 W20-01 依赖、修改冻结DAG或签发卡片/父门。新文件使用 W02 当前实际路径映射；共享 commands、锁、迁移与 ownership 仅由整合 owner 串行变更。

## 可立即实施的最小工程范围

1. **正常启动入口与开发入口分开实现。** 在新的独立候选工作区加入安装布局解析和稳定数据根；普通入口通过现有同用户身份、discovery、协议兼容与单写入者机制连接或启动 Core，不要求手工复制 token。保留开发 launcher 的 fresh-state 防护。首先在新建 owned 数据根制造合法项目/session，第二次打开必须读取同一身份/状态，CLI 与 Desktop 指向同一核心；禁止把旧 C57 目录用作试验输入。
2. **产出两种实际安装入口。** 复用已确定的打包基础，把当前真实 CLI、Desktop/Core、选定 worker 与必要运行时、迁移、许可和协议版本装入明确布局；记录每个安装件与运行二进制 hash，替换上游品牌与更新地址。安装默认 per-user；生成开始菜单与独立 CLI 入口；开发时允许显式 owned 安装/数据根，最终验证默认真实用户路径。
3. **实现可验证的升级/卸载保留。** 在仅新建的 owned 测试数据里覆盖活动任务拒绝升级、可安全升级、备份失败、迁移失败回退、版本不兼容拒绝、卸载后项目与会话仍在。测试数据包含非空项目/session与版本信息，避免只证明空目录存活。不要调用原系统卸载器、替换现有安装或默认删除数据。
4. **冻结并补齐实际命令选择器。** 向 Root 提交 v2.4 `shell_launch`、`installer_build`、`release.reproduce`、`acceptance.audit` 的具体提案；开发构建、安装行为与正式 A15 校验分开，未实现选择器非零。适配器不能让开发测试输出的 PASS 冒充 frozen A15-01..07 全断言。
5. **按新增能力做有限验证。** 先检查安装输出组成/迁移绑定和持久启动的真实行为；在合法新建的干净 Windows 用户环境或 VM，再测试安装→启动→CLI/Desktop同数据→升级失败恢复→卸载留数据。缺该环境时保留 owned-local 证据等级并阻该实测，不阻源码、打包、安装器与新数据逻辑开发。最终仍补真实模型/全流程/隔夜/独立Verifier等原门。

上述是 Root 可据以登记的具体工程建议，本文没有写入实现或启动安装。Root 的并行源码检查负责判定现有打包器和哪些生产模块能直接复用，避免本审查重复探索或擅自扩展代码范围。

当前可复用历史证据定位：`../complete-tree/R3-INDEPENDENT-REVIEW.md`、`../native-proof/NATIVE-PROOF-REVIEW.md`、`../main-integration-post/POST-REVIEW.md`，对应 seal 已原样纳入输入。formal 增量0；不签发 W13/W20/A15，不恢复或接受 C57，不改变任何原失败计数。
