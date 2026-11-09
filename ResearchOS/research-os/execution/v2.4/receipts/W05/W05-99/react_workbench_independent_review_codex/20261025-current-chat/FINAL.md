# Source14 React 独立复核

结论：**未发现阻止精确本地集成的 P0/P1/P2 问题**。冻结候选 `7d1e3ff288f91254c7304dd32f6e5bb4b66b8f1e`、tree `de59625ee5c1d360c741c95ec3f84b6f2764bb0e` 与登记范围一致；14 个允许路径中实际改动 12 个。复核 worktree 最终 clean，未修改源码、Main 或其他协作者目录。建议 Root 在当前 Main HEAD/dirty/allowlist 再校验后作精确本地 fast-forward；本报告不代 Root 整合或签发正式接受，formal increment = 0。

## 实质代码判断

- `apps/web/src/main.jsx:19` 的状态、主题、设备续期、事件连接、抽屉焦点、反馈与变更调用逻辑保持；`navigation.jsx:11` 的解析、history 和 Link 行为与旧入口等价，解除了入口/页面循环导入。`components/app-shell.jsx:50` 保留通知、项目切换、原生/浏览器导航和设备角色提示；UI primitives 只组合呈现，未新增传输协议。
- `apps/web/src/workbench.jsx:394` 的 `current.generation`、项目/会话一致性、host identity、轮询和命令互斥未变；`:530` 的 writer client/expiry 判断未变。`NativeModelConfiguration`、`NativeProjectEntry`、资格与编码授权的控制逻辑逐段比较保持一致；只移动 JSX、中文主状态与披露区。`session.send/control/permission.respond` 回调和 pending/unknown 处理保留，未把消息接收或配置保存写成业务验收。
- `workbench.jsx:577` 后的受控产物、权限与文件冲突处理完整保持。`screens.jsx:114` 后的周期、任务、成果、资源、设置与路由分发未变；ProfileDraft、ResourceRecovery、SessionContinuation 保留原调用位置/项目身份绑定。未对这些未改工作流作新的穷尽真实验收。
- `screens.jsx:65` 工作台仍分别计算规划任务、业务 ACCEPTED、待评审与当前周期；规划检查通过和执行结束均未合并为业务验收。AuthGate、PairingGate、native/browser split 以及 transport/If-Match/Idempotency/SSE 源文件保持。
- `ops/ci/ui.py:38` 保留旧 17 个 patterns，加 3 个递归 JSX/JS/CJS 输入模式；排除这个列表后，前后 Python AST 完全相同。选择器、断言、阈值、exit 语义未改。作者 571 项来自 sparse 快照；本复核 573 项仅增加 `execution/commands.json` 与 `execution/toolchains/locked.json`，共同 571 项哈希逐项一致。**数量不作为 CI 验收阈值。**

## 独立验证矩阵

| 层次 | 结果 | 证据 |
|---|---|---|
| Commit/tree/allowlist/hash/clean | PASS | PIN-CHECKS.json、INPUT-REFS.json |
| 状态/路由/协议保持及 CI AST/源集合 | 16 项 PASS | STATIC-COMPARISON-FINAL.json |
| pinned production Web build | PASS | commands/011-web-build |
| 现有 W13 React test | 5/5 PASS | commands/012-w13-react |
| own candidate Core build | PASS，首轮 sparse 缺项保留 | commands/013-core-build、015-core-build |
| own preview 浏览器/native-shaped 流程 | 37 项 PASS | browser-independent-01/report.json |
| 展开新会话和编码授权表单 | 320/1024/1440，51 个控件均未越界 | expanded-forms-01/report.json |
| 真正隔离 Core/SQLite/Owner | 7 项 PASS | real-isolated-01/report.json |
| packaged native Desktop、真实模型/provider | NOT_RUN | 不作成功主张 |
| 完整 registered W13/父任务/正式用例 | NOT_RUN | formal increment = 0 |

浏览器验证使用本复核 worktree 自建 bundle 和独立 loopback preview，未使用作者 preview。核对 320/1440 导航焦点与正反 Tab trap、Escape 恢复、路由/history、主题；native-shaped 回调验证明确取消零调用、明确确认后拒绝可见、UNKNOWN 保留草稿、pending 可见、失效 writer 禁发、资料部分失败重试入口。另验证 browser/native 分流、项目入口、目标/任务/验收区别及 pairing gate。fixture 全部业务请求被拦截；没有落到真实 provider。截图已人工查看：`native-1440-light.png`、`native-320-dark.png`、展开表单图与真实项目图。右卡标题和按钮可读、连接点状态一致、可写为状态而非假按钮、资格详情可展开。展开截图因滚动后的 sticky 顶栏位置而出现顶栏位于长图中段，这是 full-page capture 的滚动位置，不是页面重复顶栏。

真实流程使用新建 Owner 凭据、ASCII 数据根、独占随机端口和自己的 discovery：UI 创建“独立隔离河流研究”，打开周期页、返回、切换深浅主题并确认真实 SSE 连接。SQLite 只读汇总证明 1 个 ProjectProfile，且 runtime_dispatches / host_model_configurations / client_sessions 均为 0；未发模型、provider 或 worker。数据库、Owner 凭据、Core 二进制与 owned temporary root 已删除，截图/原始流/配方保留。

## 失败与证据边界

1. `013-core-build` native_exit=1：sparse 缺 `ops/experiment_sandbox` 与 `ops/supervisor`，补检出原始只读依赖后 `015` 成功；无源码改动。
2. `023-static-review` native_exit=1：本复核一度把作者 571 快照计数写成预期；真实 573 的多出两文件已精确比较并由 `024` 解释。原报告和 raw streams 保留，不改阈值、不冒充产品缺陷。
3. own Core 与两次 preview 显式 terminate + wait，Windows 返回 native_exit=1，均有真实 stop receipt；这是主动结束服务。fixture 的确认拒绝与 UNKNOWN 是期望分支。
4. 作者 `LEDGER-SUPPLEMENT.json` 已读取并绑定：追加遗漏的 diff-check exit2，原 ledger/seal 不改；3 份 Core stop.json 的真实 wait exit=1 已存在。作者仍运行 preview 的退出状态是 NOT_CAPTURED_RUNNING，不推测成功。

每个实际构建/测试/服务动作保留 argv/cwd/relevant env、raw stdout/stderr 与 native exit；预检读取和规则发现见本次工具记录。所有新增证据只写入登记 own_receipts。未触碰原始数据、Desktop、Main checkpoint 或 C57。最终建议仅覆盖此冻结源码的受控本地集成，不扩大为原生产品或正式完成结论。
