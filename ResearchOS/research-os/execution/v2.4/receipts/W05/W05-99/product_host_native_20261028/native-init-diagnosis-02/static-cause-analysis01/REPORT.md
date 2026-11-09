# native-init 单次失败的静态归因（2026-10-28）

范围：只读分析 `execution-cp569-01`；候选源码为干净 worktree `desktop-installed-delivery-20261025` 的 `5c4c9402`。本报告没有启动 native、GUI、Core、CLI，也没有改变产品、既有回执或检查点。以下是诊断结论，不增加正式验收。

## 已能确定的边界

`native-request.raw` 是合法形状的 `NATIVE_WORKSPACE_CHOOSE_REQUEST`，带有已创建的中文路径提示。`native-reply.raw` 是 Core 返回的 `NATIVE_ERROR / INVALID_REQUEST / "folder selection cancelled"`。`exchange-result.json` 记录请求和回复文件均存在，客户端和确认器各以 1 退出。文件时间显示请求 07:28:47 UTC、回复 07:28:48 UTC、确认器错误 07:29:12 UTC；因此回复发生在确认器 25 秒搜索结束之前，且没有确认路径。`folder-confirm.stderr.raw` 的 `EXACT_OWNED_FOLDER_DIALOG_NOT_FOUND` 只证明确认器未看到 **可见的** Core 进程 `#32770` 窗口：确认器在 `driver-v2/choose-owned-folder.ps1:34-50` 先筛 `IsWindowVisible`，再筛类名；它不能证明从未短暂创建窗口。

源码路径是确定的：`apps/control/main.go:229-234` 在 goroutine 中运行 `ServeNative`；`internal/host/native_pipe_windows.go:76-83,127-154` 在同一 Core 进程处理 pipe 帧并调用真实 chooser；`internal/host/native.go:262-288` 把请求路径仅作提示，chooser 错误直接返回；`internal/host/native_folder_windows.go:67-96` 在锁定 OS 线程后初始化 STA、传入提示、调用 `SHBrowseForFolderW`，把其 **所有零返回** 统一映射为 `folder selection cancelled`。因此可以定位到 Shell 调用零返回，但现有回复不能证明是用户按了取消。若 `CoInitializeEx` 返回不兼容 apartment，源码会在 73-75 行返回含 `HRESULT` 的另一条错误，和现场回复不符。若路径验证、reparse、注册失败，则都在 `internal/host/native.go:289-316` 的 chooser 返回之后，也和现场回复不符。

`PIPE_SERVER_CHANGED_AFTER_REPLY` 是客户端后置验证的单独现象。`preparation/revision01/choose-once.ps1:42-51` 在发请求前核对 pipe 的 Core PID 和 witness；第 68 行已写下原始回复，74-76 行才再次查询 server PID。服务端 `internal/host/native_pipe_windows.go:104-107` 每个连接只处理一帧，写完回复即 `FlushFileBuffers`、`DisconnectNamedPipe`、`CloseHandle`。故回复后 PID 查询与正常断连竞争，失败不表示回复来自另一 Core，更不是 chooser 零返回的原因。当前记录没有保留后置调用的 Win32 错误，不能断言究竟是查询失败还是 PID 不符。

`root-window-cdp-observation.json` 证明 Electron 的 `ResearchOS` 主窗口和 CDP 页面存在，但主窗口 `visible=false`；这不是 Core 文件夹对话框的观察。后续 `reconcile-cp569/execution01/RESULT.json` 记录受控正常关闭、Electron/Core 均 exit 0、witness 退役，说明现场进程已收尾；它不改变本次 native 失败。

## 候选原因，按当前证据支持度排序

| 顺位 | 候选机制 | 当前证据与限制 |
| --- | --- | --- |
| 1 | Core 的精简环境使 Shell 对话框初始化或命名空间解析立即失败 | `preparation/revision01/diagnose_once.py:381-384` 只保留 `SYSTEMROOT/WINDIR/COMSPEC/OS/PATHEXT/PATH` 加隔离用户目录；`apps/desktop/main/lib/desktop-management.js:430-442` 再只向 Core 传 `SystemRoot/WINDIR/TEMP/TMP/USERPROFILE/APPDATA/LOCALAPPDATA`，没有 `SystemDrive`、`HOMEDRIVE`、`HOMEPATH` 等通常继承的变量。隐藏 GUI 测试却用 `os.Environ()`：`internal/host/native_folder_windows_test.go:55-57`。这是明确的测试/现场差异；**没有证据证明某个缺失变量就是根因**。 |
| 2 | 现场提示路径触发 Shell 预选失败或异常关闭 | 现场提示是深层、含中文和空格的路径，`native_folder_windows.go:81-92` 在 `BFFM_INITIALIZED` 回调里用 `BFFM_SETSELECTIONW` 预选；测试的提示来自 `t.TempDir()`（`native_folder_windows_test.go:55-57,216-238`），未覆盖同一真实路径。路径在现场已创建（`diagnose_once.py:375-379`），所以“路径不存在”缺乏支持；是否由长度、Unicode 或 Shell 命名空间行为触发，尚无回调记录。 |
| 3 | 实际 Electron→Core 启动及窗口状态与独立测试不同 | 现场 Electron 由 `diagnose_once.py:313-318,394-395` 以 `STARTF_USESHOWWINDOW/SW_HIDE` 启动；Core 又由 `desktop-management.js:440-442` 以 `windowsHide:true` 启动。独立测试是单层 Go helper `HideWindow:true`。生产 callback 已尝试两次 `ShowWindow(SW_SHOWNORMAL)` 并设置前台（`native_folder_windows.go:43-60`），降低“只因首次 SW_HIDE 而完全不可见”的可能性；但现场没有 Core `GetStartupInfo`、callback HWND/可见性记录，不能排除窗口创建后即隐藏或失败。Electron 主窗口隐藏不能直接证明 Core dialog 隐藏。 |
| 4 | Core pipe goroutine 的 COM/thread 上下文与 helper 不同 | 现场调用在 Core pipe goroutine（`main.go:229-234`）；helper 在测试线程中直接调用且显式锁线程（`native_folder_windows_test.go:203-238`）。函数本身也锁 OS 线程并初始化 STA（`native_folder_windows.go:67-76`）。不兼容 MTA 会给明确 HRESULT 而非现场文案，因此“简单的 apartment 不匹配”与现有回复相反；其他线程/消息队列差异仍未被现场观测。 |
| 5 | pipe 传输、认证或 wrapper 后置检查导致 chooser 失败 | 原始回复已到达且精确对应 chooser 零返回，源码在认证、读取后才调用 chooser（`native_pipe_windows.go:127-154`）。后置 PID 查询发生在回复写盘之后，不能解释先前的 `INVALID_REQUEST`。这一项对**主故障**支持最弱。 |

## 最短区分实验（下一次新 scope 才执行）

1. 在**独立测试进程**中复用现有隐藏 GUI 测试的 chooser 和确认器，保持同一个已创建中文提示路径、同一 `SW_HIDE`、同一 OS 会话；先以正常继承环境运行，再以现场 Core 环境运行。两次都记录 `GetStartupInfo`、实际环境键名（不要输出值）、`CoInitializeEx` HRESULT、`BFFM_INITIALIZED` 是否触发、dialog HWND/线程/可见性、`SHBrowseForFolderW` 返回值与耗时。若正常环境可见、精简环境迅速零返回，再逐个补 `SystemDrive` 等缺失变量以定位；若两者相同，再看第 2 步。只记录窗口元数据和结果，不保存凭据或用户环境值。
2. 若独立进程在现场环境仍正常，使用**新诊断构建和新回执目录**在实际 Electron→Core pipe 拓扑做一次受控请求，记录同样的 Core 端探针，确认器只操作身份核对后的自有窗口。`CoInitializeEx` 失败会直接显示 HRESULT；未触发 `BFFM_INITIALIZED` 且立即零返回指向 Shell 建立阶段；触发 callback 但始终不可见指向窗口显示/桌面阶段；可见后消失则检查具体关闭消息来源。一次实验后按既有受控流程正常关闭，失败仍保留原始回执。
3. 如果需要进一步隔离提示路径，保持环境和拓扑不变，只比较 `requested_path:null` 与同一个中文路径（各用新的单次受控 scope）。只有“null 成功显示、提示路径立即零返回”才支持路径/预选因素。不要把这两次诊断计作产品正式用例。

优先执行第 1 步，因为它只需要可丢弃测试进程，并同时检验当前最明显的环境与路径差异。任何实验都应保留原始 `execution-cp569-01`，不能把静态推断记为已修复。
