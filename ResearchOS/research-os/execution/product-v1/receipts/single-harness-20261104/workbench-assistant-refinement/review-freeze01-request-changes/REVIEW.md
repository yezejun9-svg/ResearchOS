# UI exact6 freeze-01 独立源码复核

结论：**REQUEST_CHANGES（源码回执边界需修订）；真实 geometry PENDING。**

审查对象：`product-v1-workbench-assistant-refinement-20261105-freeze-01/manifest.json` 的 exact6，base `8fa407dbf393f94424e1612748d9e6041db35fcd`。父任务报告 Main 已到 `1ac01a6`；本审查核实这 6 个 Main 文件仍与冻结 baseline 逐文件 SHA256 相同，不将它解释为全仓 HEAD 相同。只读取指定源码、补丁及既有相关代码；仅写本 C 盘新目录。未改 D 盘/旧审查/冻结包，未运行 Node/Vite、测试、应用、浏览器、Native、CLI 或模型。未签发功能或产品验收 PASS。

## 需要修订

**R1 / P2：同项目切换历史任务时沿用前一次提交的 ACK。**

位置：candidate `apps/web/src/workbench.jsx:420,472–479,487`；`apps/web/src/harness-progress.js:37–39`。

触发路径：提交 A 得到 accepted → `acknowledgedProject=projectId` → 点击同项目历史 B。现有 controller.select 会先清空 Task 并开始读取 B；候选不清空 acknowledgement。因此读取过程中出现“请求已接收，正在读取当前任务”；若 B 的 get 失败，则显示“请求已接收，但当前任务读取失败”。B 只是被查看，页面借用了 A 的提交证明。项目 key 能隔离项目切换，不能隔离同项目任务切换。

最小修复：确认用户执行历史选择后，清除当前视图的提交 acknowledgement，再 select；或将 acknowledgement 绑定真实请求/任务身份。保留取消确认、draftVersion 和 controller 身份防护。测试需覆盖 A accepted→选择 B→B read error，断言仍保留新草稿、无新 submit、无来自 A 的“已接收”。此问题不限于文案快照：它错误描述了所选任务的请求来源。

**R2 / P2：已有 Task 时，UNKNOWN 原请求的身份被遮掉，操作错误被当成读取错误。**

位置：candidate `harness-progress.js:31–38`；`workbench.jsx:494–497`。

触发路径：已显示终态 A，提交 B 得到 outcome UNKNOWN。现有 controller 在未拿到 accepted ACK 时保留 A，并发布 error/pending B。helper 优先 `if(task) return`，只返回 A 的 Task 信息，完全丢掉 B 的 request_id/kind/state。主回执继续显示 A 已结束，B 仅剩“原提交请求待核对”的通用行。错误被标为“最近一次状态读取失败/读取错误”，但实际是提交结果未知。取消操作失败也可能被这样误标。

边界没有失守：`canSend` 仍受 pending 禁止，`reconcile()` 仍针对 controller 持有的原请求，未发现自动重发。但用户无法从技术回执辨认待核对请求，并被错误归因为读取失败。

最小修复：独立显示 pending 请求回执和身份（即便还展示旧 Task），明确旧 Task 与原请求分别对应什么；不将所有 state.error 无条件标作读取错误，可用“操作/状态核对错误”的中性描述，只有已知 read 阶段才称读取失败。无需改 DTO/controller。补充 production controller 驱动的旧 A + UNKNOWN B、旧 Task + cancel UNKNOWN 两个组合，断言 pending 身份、禁止再提交和仅核对原请求；测试不能只调用 helper({pending})。

**R3 / P2：禁用发送的原因仍远离输入区。**

位置：candidate `workbench.jsx:499–503`；`workbench.css:84,115`。

`HarnessPermissionNotice` 与执行/范围/取消 UNVERIFIED 摘要仍排在完整 ActivityRail 之后。ActivityRail 可以呈现 12 条事件，移动端 context 又整体位于对话之后。输入区发送被 canSubmitHarness 禁用时，输入区附近没有当前阻止原因；能力尚未读取也只在下面显示。折叠长能力清单的方向正确，但将必要阻止信息与清单一起留在后方，未达成首轮提案的关键层级。

最小修复：将简短权限摘要及实际 submission blockers 放在 composer 附近/上下文栏；详细安装、登录和 capability 表继续留在 ActivityRail 后的 disclosure。保持真实 verification 值及 fail-closed；不增加新授权机制。真实渲染检查应确认禁用发送时原因与发送入口共同可见，且不会被折叠详情藏住。

## 已确认的正确边界

- manifest exact6 的 baseline/candidate 哈希均吻合；candidate 与指定 worktree 的 6 个哈希吻合；forward/inverse.patch 哈希吻合 manifest。补丁仅这 4 个生产文件 + 2 个测试文件；未改桥接、controller、后端或合同。
- 原 FAILED 后永久等待提示已移除：`projectHarnessReceipt` 优先实际 Task；generic HARNESS_UNAVAILABLE 不被单凭 code 解释为模型未启动；明确 preparation 文本才触发对应总结。COMPLETED 仍声明结果需核对，CANCEL_REQUESTED 没被说成已停止。
- ACK 后立即 get 失败仍保留 accepted；send 未改变草稿版本、controller 替换/卸载保护。pending 的禁用与手动只读 reconcile 仍存在，没有自动重发。Task/Run/epoch 进度筛选及现有事件投影未变。
- `NativeMuWorkbench` 起至文件尾的文本与 baseline 完全相同。WorkbenchLayout 新参数默认值延续原 `!hasSession` 展开策略；新增 CSS 都在 assistant variant 或包含该 variant 的路由下生效，未发现直接影响 Mu 的新增选择器。此为静态无回归判断，不是 Mu 运行验证。
- Harness、Codex 工作区、Codex 任务输入及记录等既有 aria-label 保留；原生 details/summary、input label、焦点规则保留；无 Task 时无取消/暂停/恢复操作噪声。键盘 Enter/Shift+Enter/IME 使用原有函数，未改 native picker/submit/cancel 参数。
- workspace 已移出默认收起的历史，任务进度移至侧栏，工具/项目近况复用真实数据；只读建议项不再建议运行测试；源码已实现与 execution verification 文案分开。

## 测试质量与实际覆盖

现有 `tests/ui/desktop/harness-workbench.test.mjs:68–102` 新增测试通过生产 createHarnessController + fake bridge + 生产 projectHarnessReceipt，确实覆盖 ACK→立即 FAILED 和 QUEUED→tick→FAILED 两条数据流，不是复制业务算法。既有草稿测试仍提取并执行真实 send/edit/cleanup 代码，新 acknowledgement 断言能保护卸载和 controller 替换。

但测试标题中的 “renders” 实际只调用纯投影，没有挂载 React、更新 DOM 或读取样式；这只能证明 controller→投影结果。`tests/ui/harness-progress.test.mjs:63–96` 的状态/消息用例有价值，但状态循环主要断言 kind 透传及旧文案不存在，不覆盖同项目选择、task+pending、submit/cancel error 分类、组件是否展示了正确字段。没有新增历史/工作区/权限区层级的真实渲染断言，也没有 geometry 检查。不能将这些测试描述为“完整 UI 或首屏验证”。

建议补验集中在 R1/R2 的真实状态转换与实际回执展示，不新增镜像测试；R3 和可见性用真实组件/几何检查完成。Root 的 Node/Vite 结果尚未收到，本报告不声称其通过或失败。

## 首屏与可访问性：源码合理性及待验证内容

新 CSS 减少空态 min-height，取消空任务进度条和控制行，移动端欢迎语缩小，历史默认关闭；从源码看能显著降低首屏输入位置。真实的首次进入可见性仍待证据。

注意 `workbench.css:58` 将桌面/移动端 composer 都改为 static；conversation 只有 max-height，主列无与可用视口绑定的固定内容/输入行。展开历史、长标题、权限提示或视口高度下降时，输入区仍可能随 main-area 滚出；不能宣称“常驻/始终可见”。这作为必须实测的风险而非未经截图证明的布局失败。建议 Root 的 geometry 覆盖初始 1440×1000、390×844，两主题，长 Task/history、展开技术详情、blocked permission、窄高度以及输入聚焦；检查输入和发送按钮可见/可命中、无横向溢出、底栏不遮挡、阻止原因可发现。若产品仍要求常驻，需基于实际容器高度安排 scroll region 与 composer。

移动端 shortcut 按钮降至 36px、submit 至 40px；不据此声称合规或违规，需真实键盘/触控检查。未进行正式 Product Design audit 或 WCAG 合规审计。底层 focus 与 reduced-motion 规则未被本次覆盖，源代码未见显式移除焦点可视性。

## 本轮状态

源码审查完成；R1/R2/R3 待修订。真实 Node/Vite 结果、组件交互和 geometry 均 PENDING。完整模型旅程、只读边界、取消实际资格与正式验收不在本轮，不因 UI 源码改进转为通过。