# Native folder 环境 A/B 探针：准备回执

状态：`PREPARED_ONLY`。本轮只复制源码、编译可丢弃 helper、准备受封 scope 控制器；**未运行 helper、未打开 native UI、未启动产品或 provider，正式验收增量 0**。Root 需先独立审查并封新的 run scope；当前 preparation scope 的 `native_execution_authorized=false`。

## 固定输入与源码一致性

- Root preparation scope：`execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp570/Native-folder-environment-preparation-scope.json`，SHA256 `433ea19532a2804e3d9fb8666561f227e42cd30e08aec48f2e4cc9c97cf9e792`。实读后四个绑定文件的长度和 SHA256 均核对通过。
- 候选 worktree：`.local/worktrees/desktop-installed-delivery-20261025`，`HEAD 5c4c94022bd92da68ef544f2779527bfe065c428`，`git status --short --untracked-files=all` 为空。产品源码没有改动。
- `artifact_root/native_folder_windows.go` 从 `internal/host/native_folder_windows.go` 按字节复制，只把唯一的 `package host` 行改成 `package main`；其余字节完全一致。原件和副本均为 4203 字节，哈希见 `PREPARATION.json`。
- 新 `main.go` 定义 `ErrFrameShape = errors.New("INVALID_REQUEST")`，在收到控制器的 `open` 握手后直接调用原 chooser 一次。没有额外 COM 初始化、回调替换、Shell flag 改动或第二次 chooser 调用。它只输出 `GetStartupInfo`、耗时、所选路径或原始错误。

## 实验控制器的边界

`controller.py` 在获得**另外封存的** run scope 后才会执行。scope 必须绑定本准备回执、控制器和 helper 二进制的 SHA256，授权精确 `A,B` 两次、状态与回执新目录。启动前重新核对产品 worktree commit/clean、二进制哈希、目录不存在、Windows 系统目录和 `SystemDrive` 的一致性。

两个 case 使用同一个隔离 `LocalAppData/Roaming/User/Temp/项目 空间`、同一个中文路径提示、同一个 `STARTF_USESHOWWINDOW/SW_HIDE` 和同一个 helper image。A 的环境精确为 `SystemRoot, WINDIR, TEMP, TMP, USERPROFILE, APPDATA, LOCALAPPDATA`；B 只加当前已核对的 `SystemDrive`。控制器不继承 provider、credential 或项目环境，只记录键名及非秘密的系统盘符。helper 用 stdin 握手，使控制器先持有进程句柄并开始观察，再触发 Shell 对话框。

控制器每 50ms 枚举 helper PID 的顶层窗口，记录 HWND、线程、类名、可见性和矩形；只有唯一、可见、可用矩形的自有 `#32770` 对话框稳定 500ms，并再次核对进程句柄/创建时间和 HWND 后，才投递 `WM_COMMAND/IDCANCEL`。记录投递结果以及 helper 的实际返回错误、耗时和 exit code。快速 `SHBrowseForFolderW` 零返回作为诊断结果记录，不冒充确认成功。若对话框始终不可见但 helper 仍活着、读写失败或身份变化，控制器写 `UNRESOLVED` 和 `WAITING_FOR_ROOT`，持续持有 Popen handle；只有 Root 已让 helper 退出并写精确 release record 才释放。脚本没有 Kill/Terminate、90 秒自杀、自动重试或产品启动。

枚举采样可能漏掉短暂存在于两次采样之间的窗口；若 A/B 都快速零返回，下一步应使用新 scope 的 Core 端 callback/WinEvent 元数据探针，不能把“未枚举到”解释为“从未创建”。若 A/B 差异出现，也仍需独立复核和限定后续产品验证，不能由此直接宣布产品修复。

## 离线验证

使用本地 `go1.27.1`、`GOTOOLCHAIN=local`、`GOPROXY=off`、`GOSUMDB=off`、`GOENV=off` 执行 `gofmt` 与 `go build -trimpath -buildvcs=false -ldflags=-buildid=`，生成 `artifact_root/native-folder-environment.exe`。`controller.py` 通过 Python AST 解析。副本与原件的精确单行转换校验通过。未运行该 exe，也未执行 controller 的 run 分支。

`RUN-SCOPE-TEMPLATE.json` 是不可运行模板，`native_execution_authorized=false`；Root 后续应另写真实 scope，并显式给出独立的 state/receipts 目录和最多 2 次 helper 调用。
