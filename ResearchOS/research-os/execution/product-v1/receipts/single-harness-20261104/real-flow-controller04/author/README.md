# 真实 Electron / 单 Codex 用户流程准备包 — 修订四

状态：`PREPARATION_ONLY_NOT_RUN`。修订一至三及旧报告保持原样。Root 的 fullGUI01 已停止，0提交/0模型；本修订没有重试 GUI，只修 helper 的 UTC 入口。runner、UI8 选择器、路径/owner/付款/IDCANCEL 规则不变。

已用正常 pwsh7.6.5 纯复现：原 wire 2026-11-04T21:52:54.266Z 被默认 JSON 转为 DateTime KindUtc，再传 DateTimeOffset.Parse 时隐式字符串丢 Kind 和266ms，以本地+08解析成13:52:54.000Z，提前28,800,266ms。因此实际只过约12.8秒就误报期限。此为 controller 解析缺陷，非产品/账户/模型失败。证据见 date-reproduction/REPRO.json，旧实际回执引用及失败不覆盖。

窄修只给 identity JSON 增加 DateKind String，并用严格原始字符串、Invariant ParseExact、AssumeUniversal/AdjustToUniversal 返回 UTC DateTime；保持毫秒。拒绝非string、offset/local格式、缺/额外精度、空白和非法日期，不再容忍隐式DateTime转换。实际源码函数36项纯日期反例通过，覆盖UTC毫秒、五分钟、过期边界、cleanup加时和5个culture。旧path/node/UI8检查按未变代码引用，不作为新执行或运行资格。未改系统时区/时钟/policy，未导入SDK/执行helper入口/Add-Type/UIA/GUI/模型。

`real-electron-flow.mjs` 是待 Root 审定的 runner；`choose-owned-folder.ps1` 是待实测的真实 Shell 自动化 helper；`scope.template.json` 含未填资源，默认不能执行。初版 STATIC_EVIDENCE 与旧候选保留在同级 product-v1-real-electron-harness-prepare，未重复读取 SDK 或产品源，不代表未来 bundle 的运行资格。

流程使用已有 React 页面：展开“自定义项目名称”→填写“显示名称”→点击“选择目录”→真实 Host Shell 选择本轮新建 C-owned workspace→“打开工作台”→默认 Codex→一次 DOM “提交只读任务”→只读 preload 查询真实 Task/Run/events→核对结果和截图→finally app.close。按钮箭头 aria-hidden，不进入 accessible name。不点击模型配置/资格按钮，不创建 Mu Session，不替换窗口/API，不注入 bearer。不声称限制 Codex 内部调用次数。

真实 chooser 是 Go Host 的 SHBrowseForFolderW，非 Electron dialog。PID、创建纳秒、镜像 SHA/path、nonce、fresh discovery/data root、唯一 HWND/固定 prompt 和 deadline 约束保留。UIA 树名只用于导航候选；每个候选收集 Name、ValuePattern、LegacyIAccessiblePattern 全部可读值，任何绝对路径矛盾或畸形都拒绝。最终必须至少一条 ValuePattern/LegacyIAccessiblePattern 的可靠绝对路径等于 fixture，所有暴露绝对值一致；显示名称或祖先链绝不代替此证明。重复证明后重新取同一 dialog 的 IDOK，核 parent/class/PID/enabled/visible 和 deadline，再正常 BM_CLICK（零指针）。operator_fallback 固定 false。

路径证明失败时不会点 OK。仅仍能重验同一 owned PID/creation/image/HWND/nonce/unique prompt 时，才在 action+close 的有界期限内重新取得该窗口的 IDCANCEL、核 parent/class/PID/enabled/visible 后正常零指针 BM_CLICK。若 ownership/Cancel/之前 OK 结果不确定，不再点击，交 Root outer Job；不停止任何进程。结果明确保存 cleanup 与授权未建立/未知状态。

更早的跨进程 WM_USER/LPWSTR 候选保留在初版目录的 rejected-custom-message/，状态 REJECTED_NOT_RUN；本修订从未复活该调用，无 remote memory、注入、全局键盘或伪造 selection ref。固定的标准 BM_CLICK 只有零参数，不改变 Go 同进程 callback。

未来执行前由 Root 填充并冻结 scope：完整整合 source head/pins、source-bound 新 bundle 清单及 Electron/control SHA、真实 SDK 完整 111 文件清单、runner/helper SHA、唯一 nonce、新的尚不存在 `run_root`、Root 外层控制器及 launch contract SHA 和期限。模板中的路径必须改为实际新 build 路径，不能指向旧 bundle。所有路径检查/manifest 验证先于 SDK 导入与 launch；无 install、PATH fallback 或 legacy smoke 模式。

Root 已审定的**现有未命名 Windows Job**拥有唯一监督责任：原句柄 `AssignProcessToJobObject`、对该 exact Job 的 `IsProcessInJob`、无 breakaway、before-Resume、外层 deadline 和最终 accounting。runner 不创建 named Job，不用 `IsProcessInJob(NULL)`，也不把 nonce/JSON/bool 当成内核归属证明。**只有 Root 实际执行这些前提后，才能从该控制器启动 runner。** Root 必须在最终证据中保留 Job 原句柄侧的真实结果。runner 自己的 flow/close deadline 留出外层关闭余量；任何 launch/close 不确定都交 Root 收束，不伪称已停。

SDK 边界：所 pin 的 Playwright 在 Windows 内部通过 cmd wrapper 启动；launch 超时或 driver 清理有其自身的新 child 强制清理路径。这不是成功的 Main 优雅 shutdown，也不能替代 Root Job 的最终证明。runner 不自行调用 kill/taskkill，不能把 SDK 返回或 `app.close()` 单独写成全部后代停止。

进程环境逐项构造：正常 Windows `USERPROFILE/APPDATA/LOCALAPPDATA` 供原生 Codex 自己认证；PATH 仅锁定 Codex/Node 目录及 Windows；固定 PATHEXT/COMSPEC；独有 TEMP/TMP、data、Electron userData、discovery；禁 shared locator。没有读取/复制认证目录，没有继承 API keys、proxy、NODE_OPTIONS、CODEX_HOME 或既有 ROS 配置。Root 也应以同样净化的环境启动 runner，避免 SDK 自身在 import 前受到其父环境影响。

付款边界硬编码在实际 Host capabilities 读取后，并在唯一 DOM submit 前再次真实读取复核：authentication.state 必须 LOGGED_IN 且 kind 必须 chatgpt。api_key/other/UNPROBED/LOGGED_OUT/ERROR 均资源阻塞；scope 声明无法替代，不登录、不读配置、不降级付费。此检查不声称防御同 OS 用户并发更改原生凭据。

helper 承载仅 Root 本轮明确批准的已安装正常 pwsh7.6.5（路径及 SHA 见 scope），不加 ExecutionPolicy override、不改策略/注册表、不 IEX。原 PS5 sandbox -File 在脚本前 AuthorizationManager 拒绝；一次 escalated PS5 确实进入纯测试后在 helper AST 阶段失败，未执行 helper。当前 pwsh7 以既有效策略正常 -File：Machine/User/Process Undefined，CurrentUser 既有 Bypass，LocalMachine RemoteSigned，均未修改。PS5 历史错误与 pwsh7 第一轮纯夹具预期错误码不符均保留；该预期被纠正为同样安全拒绝的准确 .NET 语义。

结果写入新 run_root：公开 Task 与分页事件 DTO、精确十进制 project-outbox sequence/event ID/Run refs、真实 renderer route、截图、bounded/redacted console errors 与原字节 digest、单次 DOM 提交次数、finally 关闭状态。Main HTTP URL 未被改写或拦截：`transport_routes` 明确区分 pinned typed-preload route 映射与实际 socket 观测；不能把它写成抓包证据。fixture 标记仅正向证明实际读到了该新目录，文件清单未变不能替代 Windows 越界/写入强制隔离验证。

UNKNOWN、NOT_FOUND、断网、超时、模型失败或未发现真实 Task 都不会产生第二个 POST、新 request ID 或自动取消请求。Main 自己的 pending journal 保持原业务规则；只读 `pending/list/get/events` 可继续核对。未知状态或未确认退出不接受为成功。`app.close()` resolved 也不是 Core/全部后代已退出的证明，最终必须合并 Root exact identity/Job accounting。

未来命令形状（当前不要执行）：

```powershell
# 仅 Root 既有 Job 控制器 before-Resume 后启动，非直接运行：
C:/nvm4w/nodejs/node.exe real-electron-flow.mjs --execute --scope <已审定绝对scope路径> --scope-sha256 <Root已审定SHA256>
```

本包可独立 review、静态 pin、Node `--check`、PowerShell AST parse；以上都不是 GUI、Native、模型、provider 或 V1 journey 接受。

已知安全阻断：SDK launch 完成后才可注册 Main console/stdio listener；如果 READY 在此之前发出，runner 会因缺少真实身份报告超时，绝不凭 discovery 标签补造 READY。当前未做 GUI 实测，不能排除该 race。Root 可用外层原始 stdout 捕获定向核对，后续调整须单独保留原失败。
