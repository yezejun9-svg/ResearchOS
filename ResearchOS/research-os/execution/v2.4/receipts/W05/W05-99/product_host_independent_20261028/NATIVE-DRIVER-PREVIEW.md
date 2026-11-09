# Root native lifecycle driver 只读预审

结论：`DRIVER_PREVIEW_NEEDS_FIXES_NOT_EXECUTED`。本轮应 Root 请求，只读 `product_host_native_20261028/lifecycle.mjs` 与 `choose-owned-folder.ps1`，没有启动 Electron/Core/native、创建 scope 或写入该目录。输入 hash 见 `NATIVE-DRIVER-PREVIEW-INPUTS.json`。

| ID | 发现 | 建议与验证 |
|---|---|---|
| D01 / P1 | PowerShell 把 `StringToHGlobalUni` 分配的本进程 pointer 作为 BFFM_SETSELECTIONW(0x0467) 的 lParam 发给另一进程的 folder dialog。该值大于 WM_USER，系统不会自动跨进程 marshal pointer，不能据 SendMessageTimeout 非零认定成功选中目标路径。 | Core `native_folder_windows.go:43-49` 已在目标进程的 callback 中使用 CLI init hint 预选。移除跨进程 pointer 消息；只确认精确 owned chooser，随后核对 init 回执中的实际规范目录。不要为了驱动而新增进程内存写入。Windows 边界见 [Microsoft SendMessage 文档](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendmessage)。 |
| D02 / P1 | `session.create` 更新 Desktop 内存 sessionState，但没有持久保存 desktop context；driver 随后直接 close，重开读到的持久 context 只有 selectProject 保存的 project、无 session。 | 现有 `desktop.openSession(sid)` 会先核对真实 session.get，再 contextStore.save。调用并断言该受控入口后再 close。证据：ipc.js:210-219 更新内存；:251/:267 才保存 context；registerV2:331-337 没有额外保存。 |
| D03 / P2 | folder helper 自己首次读取 PID/path 后建立 creation 基线，而非核对 witness 中预期 Core PID/creation/image。 | 在操作前与点击前，核对独立 OS observer 得到的精确 expected PID/creation/hash/path。至少把预期创建时间/image hash 作为固定输入，明确 Windows 时间表示转换。不能把同路径 PID 复用当仍是原 owned child。 |
| D04 / 范围 | first/reopen 都通过 `_electron.launch` 启动 GUI；未覆盖 CLI-first 及 CLI 驱动的正常 cold reopen。 | 可保持此 driver 的有限 GUI-first范围，但 F02 与真实 CLI-first保持 NOT_RUN；如需补验由 Root 单独登记。版本/help/doctor 或 ready 后两个 status 不等于 CLI-first。 |

已确认可用的部分：selectProject 接受 project ID 字符串；CLI init 的 COMPLETED 顶层含 project_id/workspace_ref；配置使用 https loopback 且不调用 probe 的形状可进入既有配置保存链，session.create 本身不调用 provider。Native3 token 绑定 principal，不因 readiness 的 product-cli 与实际 CLI clientID 不同而天然失效。

驱动在失败后不杀进程、不自动重启，保留已知句柄的方向与授权边界一致。它依然只提供受控新数据根下的生命周期证据，不覆盖 busy 真实拒绝、provider 调用、安装升级卸载、C57 或完整正式门。上述建议尚未执行；后续 Root 修改驱动后需用新 hash 复核。
