# UI exact6 freeze02 独立源码复核

结论：**REQUEST_CHANGES：仅剩 R2-cancel-ACK 一个具体源码问题；geometry 待验不构成源码合入阻塞。** 本轮不签发 actual UI/Native/model 或正式验收通过。

审查 pin：freeze02 manifest 实测 SHA256 `3e050b28badb353fa96f59a0b46badafa59e65f34bf45d6d982d55436f9cb467`。父任务解释先前通知的 `101905cf88448c91f712a0c7f24f862f3635d96c1534302264ffa5bb66ed6257` 是加入 diagnostics/patch_checks 前的过早值；本报告只 pin 实测最终 manifest，未将早值用于批准。6 个 baseline/candidate 文件哈希与 manifest 一致，候选也与指定 worktree 一致；forward/inverse patch 哈希匹配。完整 source_sha256 在 review.json 与文件选择清单中。

## 已修复

- **R1 closed（源码）**：`workbench.jsx:432–435` 的生产 selectTask 在历史选择前清空 acknowledgement、恢复 read context；历史按钮实际调用该函数。ACK 另外绑定 project/controller/task。新增测试提取实际 selectTask，配合生产 controller 走 A accepted→选择 B→B get 失败，检查清 ACK、仅一次 submit 和 READ_ERROR 无“已接收”。草稿 edit/cleanup 和 controller 替换保护继续使用原生产 handler。测试未挂载 React，但是真实 handler/controller 边界覆盖，非业务算法重写。
- **R2 pending 身份部分 closed（源码）**：`harness-progress.js:31–36` 将不同 request_id 的 pending 放在旧 Task 前，保留 requestId/kind/state/previousTaskId。`workbench.jsx:512–515` 明确旧任务不是待核对请求结果，原请求身份与只读核对入口独立保留。新 submit UNKNOWN 和 cancel UNKNOWN 用生产 controller、受控 bridge 验证 pending、一次操作、禁止第二次提交与原请求 reconcile；不是只构造 helper 的孤立输入。
- **R3 closed（源码层级）**：`workbench.jsx:517–518` 将真实 verification 摘要及 HarnessPermissionNotice 放在 composer 紧前方，离开 ActivityRail；详细能力表继续在右栏 disclosure。无 capability 时也有附近阻止提示。`workbench.css:58–62` 保留原因并设可滚动上限；其可见性、触控、键盘及小屏高度仍须真实 geometry，不能由 DOM 顺序断言替代。

## 剩余问题：R2-cancel-ACK / P2

位置：candidate `workbench.jsx:483–496,513`；`harness-progress.js:37–44`。

确定的源码路径：用户本页成功提交 A → acknowledgement 绑定当前 A，acknowledged=true → 点击取消 → cancelTask 设置 errorContext='cancel'，但没有使旧 submit acknowledgement 失效。若 cancel 失败且未返回 pending（如 STATE_CONFLICT，controller 读取最新 A 后仍保留冲突错误），helper 的 `error && !acknowledged && errorContext !== 'read'` 不成立。返回当前 Task 并给 readError 赋值，页面输出“最近一次状态读取失败”，技术详情因 `errorContext === 'read' || acknowledged` 输出“读取错误”。实际失败的是取消；旧提交被确认与这次取消错误无关。cancel UNKNOWN 有 pending 时，主 pending 回执正确，但技术错误同样会因旧 ACK 被误称读取错误。

这不会产生自动重发，controller 的精确 cancelIntent、STATE_CONFLICT 不自动重取消和 pending 锁均保持；问题是操作回执归因不准确，属于 freeze01 R2 修复未覆盖的真实分支。

**最小修复方向**：取消开始时清除用于当前操作提示的旧 submit acknowledgement，或使明确 cancel context 优先于旧 submit ACK；同时 JSX 技术错误标签应使用同一分类规则。已知 accepted submit 后 get 失败仍需保持 read failure。若无法可靠追踪后续轮询 error 的来源，使用“操作或状态核对错误”比把所有错误确定归到 read/cancel 更诚实。

**必要测试**：从生产 send/submit 得到 accepted A（acknowledged 必须真实为 true），再经实际 cancelTask/production controller 产生 cancel error；断言 OPERATION_ERROR/取消原因、无 readError/读取错误、无重发；另覆盖该路径的 cancel UNKNOWN，主 pending 身份与技术错误分类都正确。当前新增 cancellation 测试从 load→select 开始，直接给 helper `false,'cancel'`，只证明没有本页提交 ACK 时的行为。它本身不是假测试，但遗漏最常见的本页提交→取消路径，不能证明此问题已关闭。

## 副作用及边界

NativeMuWorkbench 起至文件尾与 baseline 文本完全相同；WorkbenchLayout 的 Mu 默认值不变。新增 CSS 仍限制于 assistant variant。Native picker、DTO、harness.js/controller、草稿版本/卸载保护和 canSend pending 禁用未改。既有 aria-label、input label、details/summary、IME/多行输入路径仍在。未发现新增重发、伪造进度、模型输出或取消已验证宣称。

现有测试还保留 ACK→立即 FAILED、QUEUED→tick→FAILED、ACK 后 get 断开、结果未知与非终态 cancel 的语义。测试中 “renders” 仍指投影输出，不是实际 React DOM/浏览器渲染；不将之作为几何或无障碍验收。R3 DOM 顺序已从源代码确认，真实组件焦点与首屏布局未执行。

## pending 与批准边界

- R2-cancel-ACK 实际源码缺陷待修订，这是当前唯一源码批准阻塞。
- Root 新 f13 tests02 实际结果已只读审计：stdout 为 71 tests / 71 pass / 0 fail / 0 skipped，RESULT root_exit_code=0、job_total_processes=6、job_active_zero=true、stop_proved=true、无 timeout/terminate/input_drift，scope SHA256 9839c06caacfdc786313f0a7523b075e84726e16048983257bb958491b9369a1。stdout 实际 SHA256 5d4668635ab31b78d2b93c4247076a2dd2c01ba17b3fcbef6cd277399d598160、空 stderr SHA256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 均与 RESULT 一致。未运行复测；测试通过不覆盖本文指出的 accepted-submit→cancel 缺口，因此决定仍为 REQUEST_CHANGES。Root 另报告 session closed，此项未从 RESULT 独立验证。证据目录：product-v1-owned-verification-20261104/runs/product-v1-workbench-refinement-tests-02/。本 reviewer 未运行任何测试、Node/Vite、App、browser、Native、CLI 或 model。
- 真实 geometry 待完成：两个主题的初始 1440×1000/390×844、权限阻止、长历史/标题、输入聚焦、底栏遮挡及横向溢出。composer 仍为 static，不声称常驻。这项待验独立于源码合入，不单独阻止 source/fixture 范围批准。
- 模型回答、只读隔离实际资格、取消 live qualification、完整旅程与正式验收不在本报告的批准范围。

本目录为新交付；freeze01 报告、两个冻结包和 D 盘均未修改。
审计时序补充：worktree 与 freeze02 的一致性是本轮初次读取时的观察。Root 在 tests02 Job active0 后授权作者修订 freeze03；旧执行的输入身份以 freeze02 candidate 的 SHA、RESULT.input_drift=false 与实际 raw hash 为准，后续合法 worktree 修改不视为旧执行漂移。本审查未重跑或要求回退后续修改。
