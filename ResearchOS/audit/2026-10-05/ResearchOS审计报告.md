# ResearchOS 完成情况与工程审计

审计时间：2026-10-05，Asia/Shanghai。已阅读用户指定的原聊天，按最终交接给 **Qoder 桌面 Agent / Qwen3.8-Flash** 的 v2.4 目标审计：自有 CLI 与 Desktop，共享会话，真实模型对话、文件操作、工具执行、持续 Goal，以及研究和恢复能力。

**结论：已有大量可追溯的局部实现，但尚未达到可交付的编码 Agent 产品。当前主要问题是产品入口、跨模块协作与卡片接受标准没有对齐。** 本轮发现并复现了项目授权绕过、运行中接管绕过、事件序号冲突及桌面启动失败。

产品代码在本轮测试起点为 `5c62c936455d3db4c9e919389bdff1b17fb4d266`。施工仍在继续；16:54 的状态快照为 `59414b0ef8b771874df630350fe1ab47e1fb8063`、checkpoint revision 155。这期间 Git 差异仅涉及 W10 施工登记，下面所审查的产品源码未改变。数字为当时快照，不保证之后施工状态不再更新。

**实际完成情况**

| 指标 | 审计快照 | 含义 |
|---|---:|---|
| 实施卡登记 ACCEPTED | 28 / 71 | 约 39% 的卡片被接受，不能换算成产品完成度 |
| 父任务终验 | 1 / 22 | 仅 W00-99 开工基线通过 |
| v2.4 正式用例终验 | 0 / 42 | v2.0 的历史 PASS 不计作新版通过 |
| 当前施工 | W10-01 IN_PROGRESS | 2 张 BLOCKED，40 张未开始 |
| 接受卡证据哈希 | 573 / 573 匹配 | 所有登记文件存在且字节匹配，证明证据可追溯 |

状态来自 [step_state.json](D:/作品集/ResearchOS/research-os/execution/v2.4/step_state.json)，本轮复算保存在 [acceptance-audit.json](D:/作品集/ResearchOS/audit/2026-10-05/acceptance-audit.json)。已存在的有效工作包括 Go/SQLite 领域与协议实现、上下文与检索、权限及预算局部检查、Mu/Pi 上游资格验证、部分真实来源读取，以及对应独立审查。证据完整不等于证据覆盖了整张卡的交付要求。

**按影响排序的问题**

1. **P1：空 project_id 可绕过项目授权，读取并接管其他项目会话。**

   [v2.go:180](D:/作品集/ResearchOS/research-os/internal/api/v2.go:180) 只校验客户端提交的非空项目 ID；[client_protocol.go:825](D:/作品集/ResearchOS/research-os/internal/domain/client_protocol.go:825) 又允许空项目解析会话。隔离复现中，一个有有效凭证、但没有目标项目 grant 的 READER，显式提交项目 ID 得到 403，改成 null 后得到完整会话快照；接管请求也返回 ACKNOWLEDGED。

   前提是已有有效凭证且知道目标 session ID，不是匿名访问。应先解析会话真实归属，再基于完整 Principal 校验读取和写入权限；仅白名单中的宿主级方法允许 null 项目。需要从真实 `/v2/command` 路径验证无授权读取和接管均拒绝。

2. **P1：v1/v2 共用 outbox，却使用两套序号分配，能堵住项目后续写入。**

   [client_protocol_journal.go:117](D:/作品集/ResearchOS/research-os/internal/domain/client_protocol_journal.go:117) 用 outbox 最大序号加一；[store.go:341](D:/作品集/ResearchOS/research-os/internal/domain/store.go:341) 用 ProjectState.event_sequence 加一。v2 不推进后者。

   实测 `v1 createProject → v2 session.attach → v1 createRequirement`：state 的序号为 1，outbox 已有 2，最后一步即使带最新 ETag 也返回 409。事务回滚后旧序号仍在，重试无法自然恢复。应统一分配与事件类型消费，或将会话 journal 放入独立表；修复必须覆盖 v1/v2 混用及 SSE，不能只测两套接口各自通过。

3. **P1：实际 Desktop 入口启动前即异常，之后还有路径和页面接线断点。**

   [main.js:54](D:/作品集/ResearchOS/research-os/apps/desktop/main/main.js:54) 注册的 IPC 已包含目录选择器，[main.js:74](D:/作品集/ResearchOS/research-os/apps/desktop/main/main.js:74) 又注册一次。使用仓库现有 **Electron 37.10.3 原生运行时**加载真实入口，在 `app.whenReady()` 前得到 `Attempted to register a second handler for 'ros:workspacePickDirectory'`，退出码 2。记录见 [desktop-native-output.json](D:/作品集/ResearchOS/audit/2026-10-05/desktop-native-output.json)。探针只增加异常捕获，避免弹出错误对话框，没有改产品代码。

   [main.js:15](D:/作品集/ResearchOS/research-os/apps/desktop/main/main.js:15) 的 ROOT 还导致 preload 指向不存在的 `apps/preload/preload.js`，宿主发现文件指向仓库外层。实际加载的 [workbench.html:102](D:/作品集/ResearchOS/research-os/apps/desktop/main/workbench.html:102) 调用 `WorkspaceList` 等不存在的方法，随后错误输出访问不存在的 DOM 节点；本轮模拟 DOM 执行复现初始化异常。该页面也未使用新 v2 工作台桥接。应修复单一入口与 preload，接上实际工作台，再从真实安装件完成首次使用流程。

4. **P1：HTTP 接管没有调用已经实现的停机确认逻辑。**

   [session_service.go:201](D:/作品集/ResearchOS/research-os/internal/domain/session_service.go:201) 检查运行中的子进程和队列；HTTP 所用的另一实现却在 [client_protocol.go:964](D:/作品集/ResearchOS/research-os/internal/domain/client_protocol.go:964) 直接推进 epoch。

   对同一个 RUNNING、children_stopped=false、queue_empty=false 的会话，直接服务返回 STOP_CONFIRMATION_REQUIRED，HTTP 却成功接管，epoch 由 1 变 2，原 run 仍 RUNNING。应让两条入口使用同一个、可接受现有事务的交接实现，原子处理停机确认、writer、lease、epoch 和事件。仅改数据库 epoch 不能证明旧进程的副作用已停止。

5. **P1：部分 ACCEPTED 卡没有完成自己明列的产品要求。**

   W05-01 要求真实 provider 推理、Mu/Pi worker 和模型读取文件；其 [receipt.json:204](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-01/receipt.json:204) 至后续各项明确披露 provider、CLI、唯一宿主等路径未运行，实际 worker 是 cmd.exe + Job Object，没有模型工具循环。后续 [W14 阻塞记录:7](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W14/W14-01/block_record_round1.json:7) 已指出：broker 没有能应答其协议的 worker，这一缺口并非缺凭证或费用授权。

   [W13-01 卡:29](D:/作品集/ResearchOS/research-os/.local/worktrees/v24-continuation/spec/v2.4/tasks/steps/W13-01.md:29) 明确要求 Windows 安装、开始菜单启动和 U01；实际 [回执:207](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-01/receipt.json:207) 承认没有执行。两张卡仍登记 ACCEPTED。规格 [21_EXECUTION_CARDS.md:14](D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/21_EXECUTION_CARDS.md:14) 明确不应把未完成卡改为 ACCEPTED。

   这些披露值得保留，但不能替代完成要求。应复核接受范围，把局部通过保存在 substeps，让卡片状态准确反映剩余必做项，不删除旧回执、不降低规格。

6. **P2：会话事件翻页会漏掉未读取的事件。**

   [continuity.jsx:93](D:/作品集/ResearchOS/research-os/apps/web/src/continuity.jsx:93) 优先采用 high_watermark 作为下次游标。本轮执行真实 appendEvents 函数，构造 250 条待补事件、首批 200 条的协议页面，游标直接变成 250，跳过其余 50 条。应使用 next_sequence，并在 has_more 为真时继续读取。复现见 [frontend-repro-output.txt](D:/作品集/ResearchOS/audit/2026-10-05/frontend-repro-output.txt)。这项为函数与模拟 DOM 证据，没有将其冒充原生 UI 端到端验收。

7. **P2：正式检查入口与卡片状态脱节，下一轮仍会遇到已知死路。**

   [W09-02 独立报告:35](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W09/W09-02/independent_review.json:35) 记录，规格指定的 `test.security --task-id W09 --check-id W09-02` 返回 NOT_IMPLEMENTED、零断言；新增 `test.retrieval.revocation` 有实际检查价值，但 W09-99 仍指向原死路。这里同时存在规格路由缺陷和整合未完成，不能全部归因于实现者不会写代码。

   审计时 client_mapping 的 23 个方法仍全部 PLANNED、20 个 rpc_binding 为空，17 个 owner_card 已被接受；CLI/Desktop/worker 入口还有 UNBOUND。应由 registry owner 将规格所需 selector 连接到真实 handler，并验证 owner 卡接受后相应入口可运行。无需再增加一份人工填写的进度表。

8. **P2：恢复回归目前明确失败，完整本地回归也未被本轮证明通过。**

   现有 `TestW17UpgradeActiveRecovery` 在 [backup_upgrade_test.go:699](D:/作品集/ResearchOS/research-os/internal/domain/backup_upgrade_test.go:699) 失败：`no such table: runtime_dispatches`。本轮首次批量运行发现后，单独重跑仍失败。需要核对升级后的 schema、运行器恢复查询与迁移夹具；目前只能确认测试失败，不将其扩大成所有真实升级必然丢数据。

   六个包的有界抽检中，CLI、API、store、retrieval、sources 包通过，domain 包有上述失败，并达到每包 180 秒的本轮时间界限。日志记录了 310 个通过的测试/子测试条目、1 个显式失败、2 个跳过；domain 后半部分未跑完。超时本身不作为产品死锁结论。见 [go-tests-command.json](D:/作品集/ResearchOS/audit/2026-10-05/go-tests-command.json)、[单独复测](D:/作品集/ResearchOS/audit/2026-10-05/upgrade-recovery-recheck.txt)。

**工程管理上的提点**

- 当前测试擅长检查局部合同，却漏掉了“入口实际调用的是另一套实现”“两个模块共用同一张表”“真正窗口加载的是另一页”。新增检查应优先覆盖这些连接处：真实 Electron 主入口、HTTP handler、v1/v2 混用、跨客户端接管和多页事件恢复。
- 当前交接文件仍保留 v2.0 的 34 PASS 口径；checkpoint 的 accepted_steps 只有 21 条，step_state 为 28 条，next_step 已是 W10-01 而 next_command 仍引用 W05-01。应由权威 step_state 生成当前视图，并明确历史报告适用版本。235 条自由文本 obligation 不能当作 235 个独立有效缺陷；需去重、标明 owner 和可验证的完成条件。
- Git 里跟踪了 940 个 Desktop node_modules 文件，约 323 MiB，包含平台运行时。建议将可重建依赖改为锁文件和可验证安装/构建，发行件保存为构建产物；不要在本轮直接删库中的既有文件。源码目录、依赖目录和施工证据的保留策略应分别明确。
- 既有复用和协议工作应继续利用，后续整合要收敛到一条真正服务用户的路径。当前最需要证明的是安装后用户能完成一次工作，而不是单张卡的断言数量继续增加。

**建议交给 Qoder 的下一轮具体范围**

1. 先修本报告的项目授权、outbox 冲突、接管门禁，以及 Desktop 启动链；用当前公开入口跑负例与正常路径。
2. 指定一个整合 owner，打通 `自有 CLI/Desktop → Go host → Mu/Pi worker → 已授权真实模型 → 读/改文件 → 跑测试 → settled/取消`。从干净安装目录开始，使用同一会话在两端查看和接续，保存实际 diff、调用与退出结果。
3. 对 W05/W13 等卡重新核对本卡硬要求和状态，对冻结 selector 做统一绑定检查；保留已经通过的局部证据。
4. 该用户路径真正通过后，继续后续研究、评测、自改进和完整 42 例终验。安全与恢复失败不能靠“ACCEPT_WITH_LIMITATIONS”变成已完成。

本轮只做审计，未修改产品源码、正式数据库或验收状态，也未恢复、暂停或代替 Qoder 的施工 Goal。后端三项复现使用真实 Go handler、Go overlay 和隔离临时 SQLite，没有外部模型调用；三项测试的 PASS 表示缺陷复现成功。主审已独立重跑。详见 [后端报告](D:/作品集/ResearchOS/audit/2026-10-05/backend-report.md) 和 [复现输出](D:/作品集/ResearchOS/audit/2026-10-05/backend-results.txt)。

自动审批以 `blocked by policy` 拒绝了本轮超时测试临时目录的清理，未绕过限制。残留目录是 `C:\Users\yqyyds\AppData\Local\Temp\TestW16C20PrivateVerifierGrantRemoved1480761319`。复现脚本和审计日志保留在本报告同目录，供后续整改验证。
