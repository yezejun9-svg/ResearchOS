# CP558 冻结实现独立审查矩阵

状态：`CRITERIA_FROZEN_AWAITING_IMPLEMENTATION_FREEZE`。判据依据 CP558 scope、已验证 design seal 及两个 addenda；这是本地 source/build 审查矩阵，不替换 v2.4 正式验收。当前所有实现最终判定均 `NOT_RUN_ON_FROZEN_INPUT`。准备期发现见 `PREPARATION-REVIEW.md`，其失败不会被后续成功覆盖。

冻结输入进入条件：Root 提供最终 worktree、40 位 commit、exact14 diff、最终 build output/receipts。逐项实读 Git HEAD/gitdir/common-dir、tracked/untracked 状态与 source.before/source.after；构建来源、14 文件 hash、Go/Mu/client-wire 闭包应与 frozen commit 相符。若提交发生在 build 之后，必须证明 build 对应精确相同内容并如实记录 commit provenance，不把旧 source_commit 标签当新 commit 构建证明。读前后 hash 漂移则停止该输入的接受，保存诊断。

禁止本矩阵的本地检查启动 Electron/Core/native host；禁止读取/写入正常用户数据、破锁、删除旧 discovery、终止进程或改 shared state。所有 mock/temp/log 仅写本独立 receipt 子目录；native 行只定义未来 Root 单独授权范围。

| ID / 层级 | 设置与执行方法 | 必须观察到的结果 | 依据 / 相关缺口 |
|---|---|---|---|
| S01 / 静态 | 比较 frozen base→commit 的路径，核对 exact14 清单与受保护文件 hash；读 before/after source/dependency receipts。 | 仅授权 14 文件改变；desktop-management.js、Core、Native3、contracts、registry、锁及原 devmanifest 均未被改；来源可重现。 | CP558 not_authorized；08§7 |
| S02 / 静态+构建 | 遍历 final inventory，实算全部 bytes/hash，核对五个 executable 与 installation_id；检查缺项、重复、大小写冲突与顺序。 | JS、Go、Python 定义一致；实际 Electron 混合大小写 inventory 可加载；变更任一 file/hash/root/version 拒绝。 | design 路径与闭包；F01 |
| S03 / mock | 源码开发树无 marker；复制产品树移除 marker；损坏、截断、超长 marker。 | 合法开发模式可用；产品缺失/坏 marker fail closed，Core start/data write=0；不给出 fresh fallback。 | marker 完整性；F06 |
| S04 / mock | 安装根、data、userData、config、discovery 含相对路径、..、junction、symlink、大小写别名/重复条目；测试中文空格绝对路径。 | 恶意/重定向路径拒绝；正常中文空格路径规范一致；不从 cwd 推导另一数据根。 | design 规范路径；22§2.1 |
| S05 / mock | 注入 RESEARCHOS_*/ROS_DESKTOP_*/NODE_*/ELECTRON_* 覆盖及 CLI credential/config/discovery env。 | 产品根、凭据、Core 路径不被 env 偷换；受限环境进入 child；日志无秘密，普通用户 LOCALAPPDATA 正确保留。 | CP558 共享布局 |
| H01 / Electron API mock | 两个同时入口竞争锁，分别 CLI-first/GUI-first；记录锁前后所有 Core start。 | userData 在锁前确定；只赢家启动管理；只有一个 Core；输家不注册第二套启动链。 | design 单例；22§2.1 |
| H02 / Electron API mock | 故意延迟 management READY，在 STARTING 投递多个 second-instance show/ensure 意图，然后释放 ready。 | show 请求排队并幂等聚焦一个窗口；ensure 不额外窗口；一个 IPC/host boot；不能把 second-process exit0 当 READY。 | CP558 STARTING |
| H03 / mock | 同/异 installation ID 与未知 intent，注入附加字段、任意 argv/cwd/token。 | 只接受同 installation 的 show-ui/ensure-host；不执行任意命令、不采信意图为身份授权。 | design 有限转交 |
| H04 / CLI mock | 表驱动枚举正常 host-bound verb、slash alias、合法 interactive flags；观察 launch 次数。 | cold host-bound 启动/等待一次；已有可信 READY 不再启动；help/version/doctor/commands/无效命令不启动、不续凭据。 | CP558 CLI；F05 |
| H05 / CLI mock | 依次提供 ABSENT→STARTING→READY，fake clock 控制超时；spawn failure、一直 STARTING、第二实例退出0。 | 只有完整 identity+native+host.status 成功才返回；有界超时、非零与明确 reason；无第二 Core/重复自动 launch。 | design bounded READY |
| H06 / CLI mock | 同安装 binding、非空数据、dead old discovery；新可信 parent STARTING 后新 Core 写 READY。 | 正常旧→新身份窗口等待并成功；旧数据未清除；live foreign/orphan 仍拒绝。 | F02；close addendum |
| H07 / CLI mock | 对 parent/Core 分别改变 PID、creation time、image hash、image path、SID、Core parent PID、host ID、data root、inventory/build/protocol/schema。 | 每种不匹配明确拒绝；不能用 HTTP200/CoreBuildID/同 SID 单独替代完整身份。 | CP558 精确 identity |
| H08 / CLI mock | READY witness 无 discovery；发现 live Core 无 witness；坏 JSON、未知文件权限、PID 已复用、陈旧 witness。 | FOREIGN/UNCERTAIN 与 ABSENT 区分；不 launch、不 adoption、不 kill、不清文件、不破锁。 | private ownership/orphan |
| H09 / Native3 mock | named pipe server PID 不符、token bootstrap 回显 host/client/protocol 不符、credential_exposed=true、读前后 snapshot 变化。 | 拒绝跨进程/跨 host/泄露响应；凭据不输出；无授权扩大。 | 22§2；CP558 Native3 |
| H10 / Native3+HTTP mock | HTTP200 但 typed response REJECTED/ACK、host not READY、错 client/host/protocol；Native3 未就绪；缓存合法 token。 | 仅真实 typed COMPLETED 正确信息成功；首次 readiness 在总预算内处理瞬态；已有合法 token 不无谓轮换。 | design READY |
| H11 / Electron API mock | 启动 READY timeout、Core spawn失败、unconfirmed child；再投递 show 和 before-quit。 | 即使没有正常主窗口，也有可见诊断与可用控制；不变成永久 invisible singleton；未知 child 不被强杀。 | F04；tray requirement |
| C01 / CLI mock | 空 cfg/无 credential 裸 interactive、首个 init 中文空格路径；记录全部请求序列。 | 先 Native3 bootstrap/status，再受控 workspace choose/register/project bootstrap；裸交互有明确项目引导，无空 session.create。 | F03；22§2.3 |
| C02 / CLI mock | 已有 project/workspace/session/model cfg；过期 token；多项目切换/缺项。 | 同用户续凭据，保留 cfg、项目、历史与选择冲突；不重新初始化 OWNER、不自动重选目录；headless 2/3 区分。 | 14§4；22§2.3 |
| C03 / CLI mock | `product-cli` readiness 后真正 CLI clientID 使用缓存 token，并执行受控 workspace selection。 | principal 认证可共用；selection_ref 仍 client-bound；读取/接续不抢已有 writer epoch。 | token 疑点源码已消除；22§5.1 |
| C04 / 纯编译+非 host CLI | 编译 frozen CLI；在隔离环境运行 version/help/commands，分析 stdout。 | 每行 JSON 可解析或已声明 help 格式；无 host 进程/目录写；exit 正确；日志不混入结构化输出。 | 14 CLI JSONL |
| C05 / mock | stdin 多行与 EOF；host readiness 前后的取消信号；已有 session 事件与 owner 恢复。 | 客户端不杀共享 host；Ctrl+C 不伪称业务已 settle；原 JSONL/输入/取消链未被重定向。 | 14§4；22§5.2 |
| X01 / helper+main mock | 同时 window close、tray exit、before-quit；延迟一次 shutdown。 | 共用同一 promise，shutdown 只调用一次；只在同 owned PID/creation/image/host 已 STOPPED 且 exit confirmed 后退出。 | close addendum |
| X02 / main mock | shutdown busy/unresolved/refused；无窗口与有窗口各一次。 | 保留或打开可操作窗口，显示拒绝；不 cancel/pause/settle，不 retire witness、不 app.exit。 | CP558 busy refuses |
| X03 / main mock | shutdown child非零、signal、timeout、确认 identity 不符。 | 不声称正常退出；原失败保留；诊断可用，未知状态不导致新 Core 或数据清理。 | CP558 failed shutdown |
| X04 / helper+main mock | 精确 witness retire 成功与 nonce/identity 变化、unlink failure；再尝试重开。 | 只移除自己精确见证；不得清 foreign record；失败不被隐藏为可正常重开。 | marker/witness 完整性 |
| X05 / 文件+mock | 同绑定 data 下加入非空项目/session fixture，safe exit 后新 parent/Core identity重开；改 installation binding 作负向。 | 正常保持 data/project/session；进程 identity 更新；异安装不覆盖旧数据。 | close addendum；H06 |
| B01 / 构建静态 | 核对 real CLI/Electron/Core/worker/node/validator/verifier、contracts、migrations、web、licenses；解析 packaged descriptor。 | 闭包完整，main/lib/product-layout.js 纳入 client-wire，validator 来源当前；无源码 cwd 依赖。 | design fresh product builder |
| B02 / 构建静态 | 核对最终 owned 路径的 verifier installation manifest 与实际 exe；移动布局、改 exe/manifest 作 copy fixture。 | 绝对真实路径/hash/arguments=[] 正确；移动/篡改失败；旧 devmanifest 未改。 | private verifier binding |
| B03 / 构建静态 | 比较 tool pins、Go compiled inputs、Mu 5083 vendor/public/compiled inputs、client-wire before/after。 | 无漂移、真实重建 CLI；source commit/digest 与输入可追溯；缺闭包不接受。 | CP558 build evidence |
| B04 / 文档 | 对照 README 与实际包/已跑测试。 | 只称 owned location-bound layout，明确不是 installer；不宣称 close-background、overnight、C57、live/provider 或正式完成。 | 08/14 + scope retained gates |

以下为必须保留的后续真实门，**此矩阵不授权执行，均 NOT_RUN**：

| ID | 另行登记后执行的真实场景 | 最小回执 |
|---|---|---|
| N01 | 同一 owned 隔离用户根中真实 CLI-first / GUI-first / 同时启动 / STARTING 二次启动。 | 两个 parent/Core 的 OS PID/creation/image/path、host/data/install/build identity；一份调度/DB；真实 GUI/tray可操作。 |
| N02 | 普通 CLI init→受控项目选择→project/session 创建→写入非空历史→Desktop读取→CLI接续。 | project/session/workspace/model/owner/event watermark 全链；Native3 实际响应；不手抄 token、不另起 host。 |
| N03 | 同一 host 重复打开保持 Core；正常关闭走 safeExit→确认同 Core退出→再次打开同非空 data。 | 旧/新 PID/creation/image 均记录；同 project/session/事件/结果保留；不能只做 empty smoke 或 version/status。 |
| N04 | 实际 busy/unresolved 操作时关闭/托盘退出，保持 UI；用户授权 settle 后退出。 | 拒绝与成功两条原始回执；未伪造 cancel/pause/settle；stdin/JSONL/物理 Ctrl+C 共存。 |
| N05 | 干净 Windows 用户、两种 per-user installer、shortcut/CLI包、非空升级备份、migration失败rollback、uninstall留数据。 | installed release identity、实际操作证据、数据前后比对、入口注册；owned layout 不能代替。 |
| N06 | foreign/orphan、故障/睡眠/重启/隔夜、C57真实distinct-identity恢复、provider/业务与全部22父任务/42例。 | 各自原合同的当前有效证据与独立接受，不借本 source/build 审查升级范围。 |

冻结后建议有界命令（先检查最终测试源码仍为 hermetic，不执行全仓库测试）：

```powershell
# 使用 execution/toolchains/locked.json 的实际 path + hash，所有输出写本 receipt 的新子目录。
& $PinnedNode --test "$FrozenWorktree/tests/ui/desktop/product-host.test.mjs"
& $PinnedPython -B -X utf8 "$FrozenWorktree/tests/ui/desktop/product-layout.test.py"
# Go 仅运行已审查的 TestProduct 前缀；GOCACHE/GOTMPDIR/TEMP/TMP 均为独立 owned 目录。
& $PinnedGo test ./apps/cli -run '^TestProduct' -count=1 -timeout=60s
& $PinnedGo build -mod=readonly -trimpath -o "$ReviewOutput/researchos-review.exe" ./apps/cli
& "$ReviewOutput/researchos-review.exe" version
& "$ReviewOutput/researchos-review.exe" help
& "$ReviewOutput/researchos-review.exe" commands
```

测试名称通过不代表矩阵覆盖：每一项须引用具体断言和实际输出。补充 main API mock、Native3/HTTP mock 与 build inventory 检查应单独记录命令、hash、退出码。最终报告只可接受已满足的 source/build 范围；N01–N06 与正式增量始终单列。
