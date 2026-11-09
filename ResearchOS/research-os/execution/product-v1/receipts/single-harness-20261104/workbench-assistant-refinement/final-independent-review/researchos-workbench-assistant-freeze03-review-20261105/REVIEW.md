# UI exact6 freeze03 独立复核

**APPROVED_SOURCE_FIXTURE_ONLY**。源码阻塞为空。`formal_increment=0`，`product_journey_increment=0`。批准仅覆盖下列冻结源码及已审计的夹具结果，不代表真实几何、Native 模型执行、取消实际资格或正式产品验收通过。

freeze03 manifest SHA256：`111157d419e8d8257e54d86ec5c06ec68418172beee5bfddac0e87a5f94b282d`。forward `6a5b3a08abdaed2617e9e087d6f9e21bd6a6f2a90d08d6cbd430b6f4e351eb2a`；inverse `a49775e9fc40ba9e4db5a4c841c5efacc7fa9d68b7b8938a7a4096b751354bf4`。均实际哈希核对一致。完整 exact6 source_sha256 写在 review.json；baseline/candidate/worktree 的六文件对应均核实，scope/contract 的写范围仍为四生产文件和两个已有测试，无桥接/Host/controller/DTO变更。

## 发现关闭情况

- freeze01 R1：同项目选择其他历史任务时旧 ACK 泄漏。freeze02 已用实际 selectTask 清除 ACK，绑定 project/controller/task；freeze03 保持此修复。
- freeze01 R2：旧 Task 遮掉 UNKNOWN 请求身份、操作错误称读取错误。freeze02 已保留完整 pending 身份并区分此前 Task，保持 canSend 禁用和只核对原请求。freeze03 保持此修复。
- freeze01 R3：阻止提交原因在长活动轨迹后。freeze02 已把真实 UNVERIFIED 摘要及 HarnessPermissionNotice 放到 composer 紧前方，详情表留右栏；freeze03 CSS/布局文件与 freeze02 哈希相同。
- freeze02 R2-cancel-ACK：本页提交后再取消，旧 submit ACK 遮掉取消错误。freeze03 `workbench.jsx:487–493` 在 cancelTask 开始清除 ACK；`harness-progress.js:37` 令 cancel context 优先；`workbench.jsx:514` 技术错误标签同步。取消失败再无因旧提交 ACK 被说成读取错误的已报告分支。

这些是历次拒绝后修复关闭，不能将01/02报告回写为通过。review.json diagnostic_events 保留每次已证实发现的 origin_key/classification/detail，以及本轮关闭信息。旧报告和冻结包均未修改。

## 新增测试的语义审查

`tests/ui/desktop/harness-workbench.test.mjs:223–246` 从真实生产文件提取 send/cancelTask，注入状态 setter 后调用生产 createHarnessController；未复制 send/cancel 核心算法。

`248–266`：实际 send 得到 ACK，随后取消返回 STATE_CONFLICT，内部刷新又失败。断言 ACK 已清、context=cancel、投影 OPERATION_ERROR、保留 STATE_CONFLICT、仅一次 submit/一次 cancel/两次 read。它覆盖 freeze02 遗漏的本页 accepted→取消路径。

`268–291`：实际 send 后取消 UNKNOWN，断言 pending 原取消 request_id/kind、旧 Task 引用、ACK清除、第二次 submit 被拒绝，以及原请求 reconcile 一次。它与原先 load→select→cancel 用例互补。

这些是有效生产 handler/controller/投影夹具；仍不是 React 挂载、CSS几何或真实 Native取消验证。JSX错误标签本轮为源码核对，不伪称有专门渲染断言。现有 draft版本/卸载/替换controller、Task状态转换、事件scope/epoch去重、ACK后get失败用例仍保留。

NativeMuWorkbench起至文件尾仍与 baseline 逐字一致；共享 WorkbenchLayout 默认展开策略保持，新增样式限于 assistant variant。既有 ARIA 名称、Native picker、opaque workspace ref、Enter/IME、权限fail-closed与用户草稿保护未发现本次新增回归。未引入假事件、进度、模型回答或验收状态。

## 实际 tests03 证据审计

只读审计目录：`product-v1-owned-verification-20261104/runs/product-v1-workbench-refinement-tests-03/`。

- stdout：73 tests / 73 pass / 0 fail / 0 skipped，明确包含上述两条新增 send→cancel 用例通过。SHA256 `f786e01c0ad826ea5ab467601a9465874fa1218868fd9d652d9faeb53b87aaa1`，与 RESULT 匹配；空stderr SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`匹配。
- RESULT：root_exit_code=0、job_total_processes=6、job_active_zero=true、stop_proved=true；无 timeout、termination尝试、input_drift、自动重试。`formal_increment=0`、resource_ready=false。
- 原 f13 controller pin 为 `f13f630d21548bf8bbb9f1bdaf08b78adc41546d32f00216c05f6ae3664a218c`；scope 实际SHA256 `db2a1a48bb989fab6edefc7cb012b3eee81fec4149629fa25a50863190b74300` 与 RESULT/CONSUMED一致。CONSUMED中的初始 outcome-unknown由终态RESULT说明已结束，不单独误判仍在运行。
- scope 的49项输入在本次只读hash审计中49/49一致；详细记录 `tests03-input-hash-audit.json`。其中exact6与freeze03对应。后续合法修改以其发生时序处理，不倒推为旧执行漂移。
- Root报告sessionclosed；RESULT证明owned Job已停止，sessionclosed是父任务报告，未由单独session记录复核。

Reviewer未运行测试、Node/Vite、App、browser、Native、CLI或model；读取Root既有证据，不重复执行。

## 非阻塞待验

真实geometry待验：两主题1440×1000与390×844初始页，权限阻止、长历史/标题、小高度、输入聚焦、发送命中、横向溢出及底栏遮挡。新层级源码合理、composer仍为static，尚不能称常驻或首屏已实测通过。此项不阻止SOURCE_FIXTURE_ONLY范围合入。

Vite构建实际证据尚未接收，后续只读补审。完整模型旅程、只读隔离、取消live资格及正式验收均没有增量；不由unit结果代替。