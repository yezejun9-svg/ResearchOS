# W13 / C26 当前差距与窄场景执行建议

审计类型：`READ_ONLY_PRODUCT_GAP_AUDIT`。本报告不签发验收、不修改产品代码、不运行浏览器或电脑休眠。

输入基线：`a114916149c8b751e20e6164e80a7f3e1ddb6daa`。收尾时共享主仓 HEAD 已前进至 `4528561738d38d1bc41ff3a0f50e1ebd7ae5a327`；下列审计范围相对输入基线无提交差异：`apps/web/src`、`internal/domain/workbench.go`、`internal/domain/workbench_stream.go`、`internal/domain/milestones.go`、`tests/ui`、`ops/ci/ui.py`、`execution/commands.json`、`spec/v2.0/06_ACCEPTANCE_TESTS.md`。保留共享仓既有脏文件和其他 Agent 产物。

## 结论

C26 已有大部分产品实现和分散的实际浏览器夹具证据，但尚无独立、完整的当前版本 C26 执行结果。主要差距是：静默 SSE 失联缺少有界检测；`test.ui.recovery` 未绑定；真实 Windows 电脑休眠恢复未执行。旧 Chromium 生命周期冻结证据不能替代实际电脑休眠。

冻结 worktree 的 control-business-proof 369 / 5c6 及其独立审查不在本次范围；本次仅新增此报告。

## 逐项分类

| 断言 | 已实现且可复用的基础 | 缺代码 | 缺验证 / 资源 |
| --- | --- | --- | --- |
| C26-01：去重、顺序补齐、410 快照水位、旧版本隔离 | `useProjectEvents` 检查项目、event ID、sequence；缺号或 410 后重新获取投影水位；`useQueries` 拒绝同实体较旧 revision / plan_revision / watermark。服务端校验游标与可见事件序列。 | 未发现这些常规分支必须重写；静默连接的检测与唤醒恢复见下文。 | 窄场景将已有重复、乱序、缺号、410、旧投影断言映射到 C26-01，并记录实际 Last-Event-ID / 快照水位。真实唤醒后的补齐仍无证据。 |
| C26-02：五类计数、计划变化、token 不冒充进度 | 服务端 `workbenchProgress` 按 Task 状态和独立接受回执计算六阶段；StageRail 显示服务端五类计数、plan_revision、watermark 和说明。旧测试覆盖 4/6 到 4/9 的分母变化及旧投影拒绝。 | 未发现确定的业务计数缺口。 | 当前窄夹具应明确包含 accepted、pending_review、blocked、active、planned，并逐项比对六阶段服务器投影；保留计划说明与旧投影不回退证据，不用 token 文本变化替代断言。 |
| C26-03：通知唯一、重放无写入副作用 | 服务端 release / recipient / IN_APP 去重与数据库唯一约束；发布与通知事务；现有浏览器重复及逆序重放、写请求捕获、通知只读幂等和精确深链测试。 | 未发现确定的通知业务缺口。 | 抽出已有通知重放场景，单独记录唯一行、唯一卡片和写请求为空；不连带重跑完整 Task / Run / HTTP 状态矩阵。 |
| C26-04：离线提示与最后同步、无假进度、项目隔离 | offline 事件会中止流并显示最后同步 / 可能过期；项目切换中止旧查询，按 api + project + request scope 隔离返回结果；已有显式断网和跨项目测试。 | **静默失联缺有界检测**：在线标记依赖 online/offline、读取异常或新流打开，没有流心跳时限或唤醒时钟跳变检查。 | 新增保持浏览器 online 的静默 SSE 停滞场景及控制面离线场景；电脑真实休眠恢复需要 Windows S3 实测资源。冻结页面仅可保留为浏览器恢复子证据。 |

## 确定的静态代码差距

`apps/web/src/api.js` 的 SSE 分支直接等待 `reader.read()`，没有读取超时；以 `:` 开头的帧被忽略。`internal/domain/workbench_stream.go` 已每 15 秒发送 heartbeat。`apps/web/src/hooks.js` 只响应显式网络事件、流异常及读取结果，没有 heartbeat freshness、`pageshow` / 可见性恢复核对或墙钟间隔核对。

因此，当服务器或链路静默停滞而浏览器仍认为在线、流也尚未报告 EOF 时，当前代码没有保证多久以内将 UI 标为过期并重连。此为静态代码路径判断，本次没有注入网络故障，不声称已经实际复现 Windows 唤醒失败；正常 TCP 错误或系统网络通知可能触发现有恢复。

建议最小实现：向 hook 暴露收到流数据 / 心跳的时刻，使用与服务端心跳间隔相配的有界新鲜度判定；超过窗口即中止该流、显示过期状态并重新对齐当前项目快照。恢复页面或检测到明显墙钟停顿后核对当前快照，保护旧连接代次与旧项目响应。具体阈值由实现确定并在测试中核验。心跳只证明传输存活，不能递增业务 sequence、五类计数或制造业务进度。

## 已有证据与复用边界

1. `execution/verifier/W13/ui-70db969/review.json` 和同目录 `evidence-index.md`：独立结论为 UI 夹具范围通过，`stage_accepted=false`，不能提升为 W13 / C26 正式接受。其 C26 评估包括重复事件、缺口、410、水位、旧投影、离线、跨项目和通知无副作用；明确实际 Chromium freeze 不等于 physical sleep。
2. `execution/receipts/W13/frontend/26c8cc1c78cb431f9cda632e8a3b2b52/report.json`：旧 contracts 场景包含 C17 / C18 / C26 相关子断言。独立重跑证据包括 `6806c926274848df9cd104f51f29de1c`、`bdbd28f9f08945f088cffba91a6c23e7`；旧 core 修复复验为 `8e3f4ce9e93248f0a122e15a6f09ea2d`。均按各自源码水位使用，不冒充当前 HEAD 完整通过。
3. `execution/receipts/W13/frontend/3de0f6ce94ec499dbc812919aae17697/report.json`：I1 共享 core 在前 15 条检查（含 event recovery）通过后，因 resources / light / 320 横向溢出而总体 FAIL。不能改写为 core PASS，也不应丢弃已通过的逐项证据。该回执记录的 `hooks.js`、`api.js`、`scenarios.py`、`contract_cases.py` SHA-256 与本次读取文件一致；后端未由此比较确认一致。
4. `execution/receipts/W14/intent-planning/HANDOFF.md`：保留早期浏览器检查通过但清理报 `WinError 32` 的失败结果；后续 `browser-d2ff0bd7b6a940ad8b2475b737f04489` 为真实可见浏览器四项通过。`execution/receipts/W14/intent-planning/resources-320-cdb4b890e9934d78b5113c0cd037ef18/report.json` 为单一资源页 320px 修复通过，不能扩写成全 core 通过。C26 无需再运行这些已通过的意图输入及页面矩阵。
5. `internal/domain/workbench_test.go` 的 W13 progress / milestone 测试已有投影、通知去重、离线重放、只读水位与发布事务回滚覆盖。这里仅审阅实现与已有测试，本次未执行。
6. `execution/receipts/W13/50b65282-9ee5-4ed7-afbd-0b3ce0472984/receipt.json` 若需追踪阶段状态，应按其 `EXECUTION_REPORTED` 和空独立接受处理；已有 C17 / C18 / C23 / C24 / C25 记录不等于 C26 已完成。

## 执行入口差距

`execution/commands.json` 的 `test.ui.recovery` 仍为 `UNBOUND / NOT_IMPLEMENTED`。`ops/ci/ui.py` 仅允许 `core / contracts / workflow / content`，没有 C26 或 recovery phase。现有 runner 校验完整 expected 列表与源码清单，不能把临时手跑日志直接描述成正式 selector 已绑定。

另有独立的 harness 漂移：`tests/ui/expected.json` 的 core 第 3 条仍为旧的 Requirement 文案，而 `tests/ui/browser_smoke.py` 已输出 I1 自然语言 Requirement 与 bounded planning 文案。由于 runner 做精确列表比较，完整 registered core 会在此不一致处失败。这是相邻 harness 维护事项；不应为完成 C26 重新跑全部 core 页面矩阵。

## 建议的最窄新 selector

以下为待实现设计，当前不存在可执行命令：新增 `--phase recovery`，并在 `test.ui.recovery` 正式登记 W13 / C26。expected 断言应明确覆盖 C26-01 至 C26-04；报告同时保留每个子场景结果及实际休眠标志。

| 子场景 | 复用入口 | 只需新增 / 收集的内容 |
| --- | --- | --- |
| transport | `tests/ui/scenarios.py::event_recovery` | 保留真实服务器快照与受控帧注入，复用重复、乱序、缺号、410、显式断线和项目切换；新增 online 保持 true、无 EOF、无心跳的停滞，核验时限内显示过期与恢复水位。 |
| projection | `tests/ui/contract_cases.py::exact_plan_case` 中投影相关部分 | 小型六阶段夹具显式覆盖五类计数、计划修订说明、旧响应回退拒绝；直接执行这部分，不进入无关 HTTP / Task / Run 状态矩阵。 |
| notification | 同文件 `notification_case` 的重放部分 | 复用实际离线成果通知、5 次及逆序重放、唯一卡片 / 行和零意外写请求；将 CDP freeze 单独标注为浏览器生命周期恢复。 |
| host-sleep | 新增真实宿主观测入口 | 关联实际 Windows S3 睡眠 / 唤醒证据、浏览器前后截图 / 操作轨迹、当前项目快照水位与重连游标；核验计数一致、通知不重复、无额外业务写入。 |

只在恢复场景需要的桌面及一个窄屏视口取证，不重跑 11 个页面与 6 个视口矩阵。若 host-sleep 未执行，报告必须保留 `NOT_RUN / RESOURCE_REQUIRED` 且 `physical_os_sleep=false`；不得因其他子场景通过而签发完整 C26 PASS。正式判断仍交独立 Verifier。

## 真实休眠资源边界

`execution/readiness/windows-sleep/baf0dbd4-ee47-485a-9994-a90b771c156a/report.json` 为 `CAPABILITIES_ONLY_NO_SLEEP_PERFORMED`，qualification 为 false。其 `powercfg /a` 成功并显示 S3 / Hibernate 可用；`/waketimers` 因需提升权限而失败。这仅证明能力发现，不证明睡眠曾发生或恢复正确，无需重复该探针。

下一步需安排已有 Windows S3 宿主的实际休眠和可靠唤醒方式，并由独立观察者关联 Windows Kernel-Power / Power-Troubleshooter 的实际睡眠唤醒记录与 UI / 服务端证据。控制面若与浏览器同机，睡眠时两者都会暂停：应明确使用睡前排队事件或唤醒后服务端更新，不能声称同机服务在睡眠期间持续生成事件。无需消耗 SOURCE 供应商额度，也无需手机资源来关闭 C26。

本次未运行休眠、网络故障、浏览器或后端测试；未修改规格、命令登记或验收状态。
