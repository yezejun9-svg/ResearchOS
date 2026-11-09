# 真实 Electron / 单 Codex 用户流程准备包

状态：`PREPARATION_ONLY_NOT_RUN`。尚未导入 Playwright、启动 Electron/Core/Codex、打开目录选择器或调用模型；没有产品验收增量。只进行了公开源码读取、元数据记录、语法检查，以及提取两个纯函数后的 12 项假数据脱敏/环境构造检查。首次提取夹具缺少依赖的原失败另存，没有运行真实 runner。

`real-electron-flow.mjs` 是待 Root 审定的 runner；`choose-owned-folder.ps1` 是待实测的真实 Shell 自动化 helper；`scope.template.json` 含未填资源，默认不能执行。`STATIC_EVIDENCE.json` 记录本轮读取的实际源码、行号与工具 SHA，不代表未来完整 bundle 的构建或运行资格。

流程使用已有 React 页面：填写“项目显示名称”→点击“选择本地项目目录”→真实 Host Shell 选择本轮新建的 C-owned `workspace`→点击“配置模型并打开工作台”→默认 Codex→一次实际 DOM “提交只读任务”→只读 preload 查询真实 Task/Run/events→核对文件读取标记、UI 展示、事件及截图→`finally app.close()`。不需要调用旧模型配置/资格按钮，不创建 Mu Session，不替换窗口或 API，不向 renderer 注入 bearer。仅一次用户任务提交；不声称这限制了 Codex 内部的模型/工具调用次数。

真实 chooser 是 `internal/host/native_folder_windows.go` 的 `SHBrowseForFolderW`，并非 Electron dialog。helper 只找 READY 报告中该新 Core 的 PID、创建纳秒、镜像 SHA 和路径所匹配的唯一可见 `#32770`；检查固定 instruction label（它未必是窗口 caption）、本轮 nonce、fresh discovery/data 路径和未过期 action deadline。当前 chooser 没有启用 BIF_EDITBOX，因此新候选只使用真实树的 UIAutomation ExpandCollapse/SelectionItem，按 drive、直接子目录逐级定位 fixture；节点 ValuePattern/LegacyIAccessible.Value 仅只读辅助路径证明。只有能证明选中项完整路径或逐级完整路径链时才点击真正 IDOK（标准 0xF5 BM_CLICK，零指针参数）。不使用跨进程 WM_USER 指针、remote memory、注入或全局键盘。语言化 Shell 名称、UIA 属性或权限可能导致拒绝；这是尚未实测的明确缺口。不能证明就不点 OK，保存原因，只有 scope 明确允许时等待操作员在同一真实窗口选择同一 fixture。不会取消、终止或操作其他窗口。

Root 在准备静审中发现旧候选的跨进程 BFFM_SETSELECTIONW/LPWSTR 不具备自动封送，已在任何 GUI 执行前禁止。旧四文件及 SHA 原样保存在 `rejected-custom-message/`，状态 `REJECTED_NOT_RUN`；新 helper 已删除该调用和带字符串 lParam 的声明。依据由 Root 核过的 [Microsoft SendNotifyMessageW 文档](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendnotifymessagew)：系统自动封送仅限 WM_USER 以下的系统消息。本次不改产品 Go 同进程 callback 的现有代码。

未来执行前由 Root 填充并冻结 scope：完整整合 source head/pins、source-bound 新 bundle 清单及 Electron/control SHA、真实 SDK 完整 111 文件清单、runner/helper SHA、唯一 nonce、新的尚不存在 `run_root`、Root 外层控制器及 launch contract SHA 和期限。模板中的路径必须改为实际新 build 路径，不能指向旧 bundle。所有路径检查/manifest 验证先于 SDK 导入与 launch；无 install、PATH fallback 或 legacy smoke 模式。

Root 已审定的**现有未命名 Windows Job**拥有唯一监督责任：原句柄 `AssignProcessToJobObject`、对该 exact Job 的 `IsProcessInJob`、无 breakaway、before-Resume、外层 deadline 和最终 accounting。runner 不创建 named Job，不用 `IsProcessInJob(NULL)`，也不把 nonce/JSON/bool 当成内核归属证明。**只有 Root 实际执行这些前提后，才能从该控制器启动 runner。** Root 必须在最终证据中保留 Job 原句柄侧的真实结果。runner 自己的 flow/close deadline 留出外层关闭余量；任何 launch/close 不确定都交 Root 收束，不伪称已停。

SDK 边界：所 pin 的 Playwright 在 Windows 内部通过 cmd wrapper 启动；launch 超时或 driver 清理有其自身的新 child 强制清理路径。这不是成功的 Main 优雅 shutdown，也不能替代 Root Job 的最终证明。runner 不自行调用 kill/taskkill，不能把 SDK 返回或 `app.close()` 单独写成全部后代停止。

进程环境逐项构造：正常 Windows `USERPROFILE/APPDATA/LOCALAPPDATA` 供原生 Codex 自己认证；PATH 仅锁定 Codex/Node 目录及 Windows；固定 PATHEXT/COMSPEC；独有 TEMP/TMP、data、Electron userData、discovery；禁 shared locator。没有读取/复制认证目录，没有继承 API keys、proxy、NODE_OPTIONS、CODEX_HOME 或既有 ROS 配置。Root 也应以同样净化的环境启动 runner，避免 SDK 自身在 import 前受到其父环境影响。

结果写入新 run_root：公开 Task 与分页事件 DTO、精确十进制 project-outbox sequence/event ID/Run refs、真实 renderer route、截图、bounded/redacted console errors 与原字节 digest、单次 DOM 提交次数、finally 关闭状态。Main HTTP URL 未被改写或拦截：`transport_routes` 明确区分 pinned typed-preload route 映射与实际 socket 观测；不能把它写成抓包证据。fixture 标记仅正向证明实际读到了该新目录，文件清单未变不能替代 Windows 越界/写入强制隔离验证。

UNKNOWN、NOT_FOUND、断网、超时、模型失败或未发现真实 Task 都不会产生第二个 POST、新 request ID 或自动取消请求。Main 自己的 pending journal 保持原业务规则；只读 `pending/list/get/events` 可继续核对。未知状态或未确认退出不接受为成功。`app.close()` resolved 也不是 Core/全部后代已退出的证明，最终必须合并 Root exact identity/Job accounting。

未来命令形状（当前不要执行）：

```powershell
# 仅 Root 既有 Job 控制器 before-Resume 后启动，非直接运行：
C:/nvm4w/nodejs/node.exe real-electron-flow.mjs --execute --scope <已审定绝对scope路径> --scope-sha256 <Root已审定SHA256>
```

本包可独立 review、静态 pin、Node `--check`、PowerShell AST parse；以上都不是 GUI、Native、模型、provider 或 V1 journey 接受。

已知安全阻断：SDK launch 完成后才可注册 Main console/stdio listener；如果 READY 在此之前发出，runner 会因缺少真实身份报告超时，绝不凭 discovery 标签补造 READY。当前未做 GUI 实测，不能排除该 race。Root 可用外层原始 stdout 捕获定向核对，后续调整须单独保留原失败。
