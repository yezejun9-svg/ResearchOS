# Native folder path entry: 最小只读实施建议

状态：READONLY_PROPOSAL；2026-11-05。当前未写 D、未运行测试/GUI/App/model、未安装。源文件已读取，不读取正式评测、旧 DB、凭据或 cache DB。等待 Root 登记新隔离 worktree 与 exact lease 后才能施工；此文件不是写 lease 或接受回执。

## 基线与范围

- parent 提供 HEAD `71396f932d0ccc7035f3fdb4896e3c7ecc8f6343`；本次 rev-parse 相符。
- `internal/host/native_folder_windows.go` SHA256 `e79f977b5d7b21a6cc93034120984110816a6fdfdd9148a6a4e13dbc9f4e5433`。
- `internal/host/native_folder_windows_test.go` SHA256 `ed131f838beaefe76fcf0a6354b28568a98bd1de0bb97f87cc4dd4916ed87759`。
- 仅这两个现有文件建议纳入新 lease；不改 native protocol、Host registration、schema、contracts、依赖、CLI 或 Desktop renderer。
- 已读根 `AGENTS.md`；internal / internal/host 无额外 AGENTS。已读 product-v1 plan/leases/state：独立 owner/worktree、Root 串行整合、独立审查、保留失败。当前没有此新 slice 的 lease。
- 本次 `git status` 包括显式 work-tree 参数均报 `this operation must be run in a work tree`，不能把它当 clean 证据；源文件 hash 已单独核对，Root 创建新 WT 时应再核验状态。

## 真实代码接点

1. `native_folder_windows.go:27–31`：增加 `bifEditBox=0x0010`、`bifValidate=0x0020`、`bffmValidateFailedW=4`。
2. `:43–61`：现 global Windows callback 新增 Unicode validation 消息分支。用 `MessageBoxW(hwnd, fixedUTF16Text, fixedUTF16Title, MB_OK|MB_ICONWARNING)` 明确提示；之后无条件返回 1 保留选择器。失败消息的第三参数完全不读取、不解引用、不保存、不回显；第四参数仍只供 INITIALIZED 预选使用。
3. `:89–91`：flags 改为 `bifReturnOnlyFileSystemDirs | bifEditBox | bifValidate`（0x31）。保持现老样式，不加 NEWDIALOGSTYLE/USENEWUI/STATUSTEXT。
4. 保持 `:47–59` 原 INITIALIZED 预选/ShowWindow/foreground 行为，`:68–76` 锁线程与 STA S_OK/S_FALSE/失败关闭，`:92–108` 的真实 PIDL、取消空结果、SHGetPathFromIDListEx 及 CoTaskMemFree。

确认之后仍走原 `native.go:337–405`：Shell chosen path → Abs/EvalSymlinks/reparse 检查 → RootRegistry.Register（含 fileIdentity）→ SelectionStore.Issue。selectionRef 仍绑定 principal/client/TTL/single-use；编辑文字不进入新的授权捷径。

## 最小有意义测试

先做无需 GUI 的实现验证，再由 Root 单独授权并运行真实窗口验证；两者分开记账，不以单元测试宣称真实选择成功。

- 在同一 test 文件调用生产 callback handler 的小型 reporter seam：独立以数值 4 输入，断言提示一次、owner 等于 callback HWND、返回 1。lParam 用 null/非可解引用哨兵，断言无需读路径指针；ANSI 消息 3、SELCHANGED 2、未知消息不提示且返回 0。seam 只在进程内传固定提示函数，不增 wire API/feature flag。避免为测试改 COM/选择/PIDL 边界。
- 用已有 `firstUseHost(t)` 的 fresh disposable store 验证 chooser 取消/错误时无 reply、Roots=0、Outstanding selections=0；已有 confirmed selection/nullable path/single-use 测试继续复用。
- 保留现 `TestNativeFolderHiddenProcess` opt-in 测试及其隐藏启动/连续两次/COM 配平/Cancel 语义。无 GUI 的本阶段不设置 `RESEARCHOS_NATIVE_FOLDER_GUI_TEST`，不能把 skip 算 pass。
- scoped 命令建议：`go test ./internal/host -run 'TestNativeFolderValidation|TestNativeFolderCancelled|TestNativeWorkspaceChooseNeedsConfirmedHostSelection|TestNativeWorkspaceChooseRequiresExplicitNullablePath|TestNativeWindowsFolderChooserAPIsPresent' -count=1 -v`。Root 在新 WT 确认工具链/缓存/输出路径后执行；不得下载新依赖。额外 build/vet 仅按 Root 精确登记。

后续真实 GUI 的决定性验证（需另行 Root owned scope，不在本只读阶段运行）：

1. 新鲜合成 Unicode 目录（中文、空格、非 BMP 可作为有价值覆盖），确认唯一 owned chooser 与实际暴露的 Edit/ValuePattern 后输入；点击实际 Shell OK，返回 PIDL 路径，再走原 selectionRef。不能伪造 selection 或借新测试函数直接返回 typed path。
2. 输入不存在的目录 → OK：同 PID、owner 为 chooser 的固定提示出现；提示关闭后同 chooser 仍在，native 请求仍未完成、无新 workspace grant/selection。更正为存在目录再 OK，得到实际选择结果。
3. 无效输入 → 关闭提示 → owned Cancel：空 chosen、原取消错误、无 workspace grant/selection，COM 平衡。
4. 提示仍显示时的受控收尾：owned warning 和 chooser 都消失，原 Job owned tree 归零；不能因新增 modal 遗漏窗口、扩大取消目标或改变权限门。

窗口驱动只依据本次实际观察到的 owned Edit；不重新猜 Tree selector，不向其他进程发送带指针的 WM_USER 消息。可复用现 test executable 的 owned helper 做后续 opt-in GUI 增量，不需产品 test hook。

## 风险边界

- W/A 常量混淆会让验证分支失效；必须 W=4，ANSI=3 不应误当 W 消息。
- VALIDATEFAILED 返回 0 会关闭 chooser；无论 MessageBox 成功或失败都应返回 1。提示失败时也不得输出路径或授权。
- 新 owned modal warning 需纳入取消和进程收尾验证；MessageBox 以 callback HWND 为 owner，不用 0/global owner、不跨回调保留 HWND。
- lParam 没有长度参数，读取它会扩大 unsafe UTF-16 扫描边界；固定提示直接消除此需求。固定 UTF-16 buffers 只在同步 API 调用期间使用并保持存活。
- 取消返回 NULL；转换失败、空路径、非文件系统对象保持 fail closed，不能回退为编辑文字。现 filesystem canonical/reparse/identity gates 全部保留。
- 不新增新样式或 IFileDialog，以免扩大 COM/OLE 和窗口结构变更。

## 官方依据

- [BROWSEINFOW](https://learn.microsoft.com/en-us/windows/win32/api/shlobj_core/ns-shlobj_core-browseinfow)：EDITBOX 0x10；VALIDATE 0x20 需与 EDITBOX 同时启用；无效或不存在输入触发失败回调。
- [BFFCALLBACK](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/legacy/bb762598(v=vs.85))：`int CALLBACK(HWND, UINT, LPARAM, LPARAM)`，不同消息第三参数含义不同；失败返回非零保留对话框。
- [Microsoft SDK header](https://github.com/microsoft/win32metadata/blob/main/generation/WinSDK/RecompiledIdlHeaders/um/ShlObj_core.h#L1078)：`BFFM_VALIDATEFAILEDW=4` / A=3，W lParam 为 wzPath，返回 1 keep、0 end。
- [MessageBoxW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-messageboxw)：已有对话框时建议使用其 HWND 作 owner。
- [SHBrowseForFolderW](https://learn.microsoft.com/en-us/windows/win32/api/shlobj_core/nf-shlobj_core-shbrowseforfolderw)：COM 初始化、NULL 取消、返回 PIDL 释放要求；本 slice 不改变现 STA 或样式。

本建议的 formal_increment=0、product_acceptance_increment=0、model_runs=0。旧22/42保留，新V1 journeys0/13与 model0 状态不由此提升级别。
