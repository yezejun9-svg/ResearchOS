# Native folder path entry 候选交付

状态：`FROZEN_SOURCE_NOT_INDEPENDENTLY_ACCEPTED`。按 CP633 `PRODUCT_V1_NATIVE_PATH_ENTRY` lease，仅改隔离 worktree 中两个登记文件；未提交，冻结后未再修改源码。

- `internal/host/native_folder_windows.go`：flags 为 0x31；W validation 消息 4 显示以 callback HWND 为 owner 的固定 Unicode `MessageBoxW`，随后返回 1 保留选择器；不读取失败 lParam。原 INIT、STA/COM、取消和 PIDL 转路径/释放保持原流程。
- `internal/host/native_folder_windows_test.go`：新增 fake UI effect 的 W/ANSI/其他消息分流、owner 与单次提示、INIT 显示顺序，以及 chooser 错误/取消不颁发 root/selection 的断言。未弹真实窗口。

最终 warning text：`文件夹路径无效或不存在。请输入已有的文件夹路径后重试。`；caption：`ResearchOS`；flags：`0x30` (`MB_OK|MB_ICONWARNING`)。

验证：Go 1.27.1，现有离线 module cache，C fresh build/temp 目录，`GOPROXY=off`、`GOSUMDB=off`、`GOTOOLCHAIN=local`、`-mod=readonly`。聚焦测试通过 7 个顶层测试、9 个子测试（无选中测试 skip）；vet 通过。最后只替换固定提示为中文后，额外 compile-only（不计测试通过）及 vet 均 exit0；gofmt 和 diff check 通过。原始日志、精确 argv/cwd/exit code 见 checks.json 与对应 *.stdout.log / *.stderr.log。

最终 prod SHA256：`1d52e52aa2c4bbc2653156fd3602c6f6ab9fd208342a154f0e1c2ac6a2ebef6a`。

最终 test SHA256：`58af41b689dde86b629788e940133ec6c75970f4562400c0234784a6d751dc52`。

冻结包：`freeze/manifest.json`、`freeze/candidate.diff`、`freeze/status.raw.txt`、`freeze/internal/host/` 两个源码副本。最终 Git status 只有登记 exact2 的 M；起始 HEAD 为 `71396f932d0ccc7035f3fdb4896e3c7ecc8f6343`，起始 status/diff 为空。默认 sandbox 的 Git 假 bare 失败已保留为环境观察，使用 Root 指明的 require_escalated 只读核验后正常，未改 Git 配置。

Microsoft 语义依据及建议实测矩阵见 proposal.md。子 agent 对最终文案替换前的 Win32 调用结构做过只读核对，未发现具体语义阻断；该核对不是独立接受。

待 Root 独立源码 review、fresh 完整 build，以及真实 owned GUI 范围中的 Unicode 路径确认、无效输入后更正/取消、warning 与 chooser 的窗口树收尾。UI fake 不能证明真实 Shell UX。作者 GUI=0、model=0；未打开旧 DB/凭据/cache DB，只用新测试夹具数据；未读正式评测。formal_increment=0、product_acceptance_increment=0，新 V1 journeys0/13 与旧22/42映射均不由本候选提升级别。
