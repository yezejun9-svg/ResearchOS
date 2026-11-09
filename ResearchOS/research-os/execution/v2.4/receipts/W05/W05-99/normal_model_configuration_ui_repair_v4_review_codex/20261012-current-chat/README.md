# W05 UI repair-v4 独立审查

结论：**REQUEST_CHANGES**。候选 `57ec9b4408835483bf0c4c30397968d7a11a0b2c` 的原 v3 跨主机终态反例六变体已修复，但新增 P1 `W05-UI-V4-001`：原主机 A 配置完成后，对账的 `host.status` 已发往 A，若此时 discovery 切到 B，A 返回的旧来源标签仍通过界面的三项比较。界面清除 pending 并确认保存，尽管 B 是空配置主机且没有收到任何请求。

独立三条实际 Chromium DOM 反例均复现，包括原样最终编译 React UI + 最终绑定 IPC + Go validator：正式编译界面显示“配置已保存（修订 1）”并移除首次配置表单。见 `status-race-results.json`、`status-race-http/`、`compiled-ui-status-response-switch.dom.html` 和同名截图。`status-race` 命令 exit 0 表示成功断言缺陷，不能算产品 PASS。修复需要可信 shell 在异步状态读取结束后重新核对当前 logical host/data_dir；不能把 A 的回执重新标成 B，也不能清除 A 的未对账意图。

冻结作者 manifest 为 `ece814f27447a2ec1e23acb2fcd2d18e214e858117b16206c51ee5aff448a0be`。收据/源码/资源核对 1408/1408，完整绑定输入 6424/6424；输入摘要 `392035ec6070865a2613ddbc43e777bbd732d9a1e31e46910a67419f837dcd77`，validator SHA256 `b894eb2d6f5c67f49b491df92b01c5c03d7eb4bfc831437b422053359dc9ed7e`。这是独立核对作者最终构建，未另行声称独立重编译。

独立测试：选定边界 28/28；新增来源伪造与 host/data-root 分别切换 4/4；组件生命周期 5/5；v3 原反例回归 6/6。边界覆盖同主机换端口/PID 的原 envelope 重放、ACK/possiblySent 单调、写所有者和 CAS。最初 copied baseline harness 带有作者旧 build-5 路径；该轮原样保留在 `baseline-legacy-build5/`，最终合格重跑明确断言 build-6。

累计 `292ad860` 到 v4 的七个文件已从 Git object 核对并封存。候选 sparse worktree 缺少的 `tests/ui/continuity/surfaces_driver.js` 只读取 Git 对象到本目录，未补写候选。该最终 driver 实跑表23一致、拒绝11/11、合法 envelope 66/69；基线64/69、拒绝10/11。剩余三条 goal.start/project.bootstrap 不一致是遗留观察，driver exit 0 不等于整体 PASS。详见 `surface-comparison.json`。

Main 基线 HEAD `5c1add9a9ce709a468e0ecd37f5d61de507ac40c`，CP410 / OW200 / CM40；既有 dirty 状态保留。只写本独审目录，未改 Main、候选、Canon、冻结合同或旧收据。0 actual model、0 external、0 public tunnel，formal/parent acceptance 均 +0。

证据属于 SOURCE + FIXTURE。最终编译页面由 localhost 原样提供，通过测试 bridge 调用真实绑定 IPC；主机、凭据和 HTTP 是公开夹具，旁支 REST 有意返回404。没有真实 Electron/native/Core 整流程或运行时资格接受。两处新独审缓存的定向 PowerShell 删除被自动审批审查以 `blocked by policy` 拒绝，因此保留，未换工具绕过。
