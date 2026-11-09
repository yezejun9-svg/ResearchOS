# CP572 原生文件夹对话框：A/B 后的只读因果定位

状态：静态分析。未运行 helper、native GUI、Core 或产品，未修改源码、既有回执或检查点；正式验收增量 0。

## 结论与证据边界

`SystemDrive` 单独缺失**不足以解释**这次失败。CP572 的 A（Core 七键环境）和 B（仅加 `SystemDrive=C:`）使用同一 SHA256 `92573aacf6f2caab9baead612a13cf0eef688fc1e5a4177ac6bf5b1cbfa7a463` helper、同一 D 盘中文提示、同一隔离 profile、同一 `SW_HIDE`。两者 `startup_flags=257/startup_show=0`，分别在 113.4ms、96.2ms 返回 `INVALID_REQUEST: folder selection cancelled`，helper exit 0，控制器均未发 IDCANCEL（`execution-cp572-AB01/{environment-contract.json,A,B,RESULT.json}`；`RESULT.json` SHA256 `48d7f1eaee0633db097aad03ac1ec1e4d445826d87418cfdfda7268d286d0ebc`）。这只是“单变量补充未使对话框存活”，不能推断 `SystemDrive` 对 Windows Shell 永远无用。

A 在约 104ms 枚举到了 helper 自有、`visible=false` 的 `#32770` 窗口，矩形 `[660,285,1047,734]`，随后约 113ms chooser 返回零；B 的 `windows.json=[]`。A 窗口矩形与 2026-10-12 成功组件测试中四个**可见** `#32770` 的矩形相同（`native_folder_visibility_codex/.../native-dialog-observed-facts.json`，SHA256 `eb027f1cd03c6475e061200c6311390de541fb4c918501bcc71df8b88392fee9`）。这是“Shell 至少创建了同类顶层对话框，但很快结束、未显示”的直接线索；没有 callback 事件记录，不能断言 `BFFM_INITIALIZED` 已触发、`ShowWindow` 失败或是谁关闭了窗口。B 仅做间隔约 50ms 的枚举，96ms 内的短暂窗口可以漏采；`[]` 不是“B 从未创建窗口”。

CP572 不经过 Core pipe、Electron 或注册流程，却重现了“迅速零返回、无人工取消”的故障形态，因此 pipe 身份校验、客户端后置 PID 查询或 Electron 主窗口隐藏不是**该形态发生的必要条件**。源码 `internal/host/native_folder_windows.go:67-96` 中 COM STA 初始化失败会返回含 HRESULT 的不同文案；现场进入了 `SHBrowseForFolderW` 的零返回分支。`SHBrowseForFolderW` 零返回被统一称作“取消”，现有日志没有 Shell 内部错误码、callback 或关闭消息，不能把它定为用户取消。

## 与成功组件测试的逐轴对照

| 轴 | 2026-10-12 成功组件测试 | CP572 A/B | 可得结论 |
| --- | --- | --- | --- |
| chooser 源码 | `native_folder_visibility_codex/.../native_folder_windows.go` SHA256 `e79f977b5d7b21a6cc93034120984110816a6fdfdd9148a6a4e13dbc9f4e5433` | worktree 同 SHA；helper 副本仅 `package host→main`，其余字节相同（`preparation02/PREPARATION.json`） | chooser 算法/回调源码变更不能解释差异。成功测试 exe 与 CP572 helper **不是同一二进制**。 |
| 隐藏启动 | 测试 helper `HideWindow:true`，观测 `startup_flags=257/show=0`；四次 dialog 可见且稳定 ≥500ms | A/B 同为 `257/0`，A 短暂不可见 | `SW_HIDE` 本身不足以解释；二者的启动栈仍不完全相同。 |
| 环境 | `native_folder_windows_test.go:55-57` 使用 `append(os.Environ(), ...)`；测试 runner 只覆盖 Go/TEMP/TMP 及 opt-in 键（`attempt06-frozen-native-tests.invocation.json`） | A 精确 `SystemRoot,WINDIR,TEMP,TMP,USERPROFILE,APPDATA,LOCALAPPDATA`；B 仅加 `SystemDrive`（`environment-contract.json`） | 成功测试继承了更多用户/系统环境。历史回执没有完整环境键和值快照，不能指定单个缺失变量为根因。 |
| profile | 测试沿用实际 OS 用户 profile/AppData；`run-evidence.ps1:7-12` 只覆盖 Go 构建和 TEMP/TMP 等测试键 | `USERPROFILE/APPDATA/LOCALAPPDATA/TEMP/TMP` 指向新建但未登记为 OS 用户 profile 的 D 盘隔离目录（`preparation02/controller.py:366-375`） | Shell 的用户已知目录/配置与环境路径是否一致未被检验；这是独立于缺键的假设。 |
| 提示路径 | 空提示及 C 盘长 ASCII `t.TempDir()` 都可见；示例提示长约 191 字符（`native-dialog-observed-facts.json`） | 相同 D 盘中文提示长约 132 字符 | 单纯路径长度解释较弱；D 盘、Unicode、预选路径是否参与仍未隔离。 |
| 线程/调用上下文 | `native_folder_windows_test.go:203-238` 在 test helper 进入前锁 OS 线程，直接调用 chooser；第一次为 fresh STA | `main.go` 直接调用 chooser，chooser 自身在 67-76 行锁线程并初始化 STA | 简单 apartment 冲突与现有错误文案不符；测试提前锁线程与 helper 主函数时序不同，未被环境 A/B 检验。 |
| 人工取消 | 成功测试先见到可见自有 dialog，再投递 IDCANCEL；四次均正常返回相同“cancelled”文案（`native-dialog-observed-facts.json`；独立 replay exit 0） | A/B 无可见稳定 dialog，均未投递 IDCANCEL | 相同文案涵盖两种不同过程，不能用文案证明人工取消。 |

源代码还显示，真实产品 Core 由 `apps/desktop/main/lib/desktop-management.js:430-442` 只传上述七键并设置 `windowsHide:true`；CP569 外层 launcher 虽保留 `COMSPEC/OS/PATHEXT/PATH`（`preparation/revision01/diagnose_once.py:381-384`），这些键在 Core spawn 时又被剔除。当前会话只读列出的 OS 环境键还包括 `ComSpec,Path,PATHEXT,HOMEDRIVE,HOMEPATH,ProgramData,ProgramFiles,ProgramFiles(x86),USERNAME,USERDOMAIN,SystemDrive`；这只是 2026-10-28 当前快照，**不是**历史测试进程的完整记录，也没有证据证明其中任意单键是 Shell 的必需输入。七键缺失与隔离 profile 值同时变化，现有 A/B 只能排除“单补 SystemDrive 即可恢复”，不能在两类原因间裁决。

成功组件测试发生在 10 月 12 日，CP572 在 10 月 28 日；现有回执未把两次的 Windows session/window station/desktop 身份绑定为相同。后续若所有环境、profile、提示路径对照仍失败，应检查当前会话状态这一时间性变量，不能将旧测试成功直接外推为当前系统必然成功。

## 下一次最小有区分力的对照

优先做**一例 C**，复用已接受的同一 helper 二进制及相同中文提示、D 盘隔离 profile、`SW_HIDE`、同一控制器观察与正常 IDCANCEL 规则；只把 A 的七键环境扩展为“继承的非敏感 OS/Shell 键”。C 保持 `USERPROFILE/APPDATA/LOCALAPPDATA/TEMP/TMP` 五个值与 A **逐字一致**；从当前 OS 进程仅补当时存在的 `ComSpec,Path,PATHEXT,OS,ProgramData,ProgramFiles,ProgramFiles(x86),USERNAME,USERDOMAIN,SystemDrive`。再补 `HOMEDRIVE/HOMEPATH`，但两值由同一隔离 `USERPROFILE` 派生，不能指回真实 profile；只记录键名和非秘密系统路径，不继承 `RESEARCHOS_*`、`ROS_DESKTOP_*`、`ELECTRON_*`、`NODE_*`、provider/credential/token/proxy 键。C 对 A 只改变环境完整性，保留隔离 profile 的主要值和路径提示。运行前需 Root 另封单次 native scope、固定全部源和启动参数；本报告不执行它。

判读 C：若出现稳定可见的自有 `#32770` 且由控制器 IDCANCEL，缺失的 OS/Shell 环境**这一组**足以恢复直接 helper 显示；随后把新增键分组缩减才能定位必要键，不能直接认定某一键。若仍在约百毫秒内零返回，单纯补安全 OS 键不足；下一例 D 才保持 C 的其余键/提示/隐藏 flags，仅将 profile 相关值（`USERPROFILE,APPDATA,LOCALAPPDATA,TEMP,TMP,HOMEDRIVE,HOMEPATH`）切到当前 OS 用户真实、互相一致的值。D 可见而 C 不可见，会支持“伪隔离 profile 与 Shell/已知目录状态不一致”；D 仍失败，则再做空提示对照，区分 D 盘中文预选路径。空提示需要另封带小幅 `main.go` 参数变更的新 helper；不能把现有 helper 的路径校验绕开后称作同一二进制实验。

若 C 可见，应同时记录 `BFFM_INITIALIZED`/可见过程的采样局限：50ms 轮询不能证明失败 case 没有短暂 UI。若 C/D 都失败，优先增加**诊断专用** callback 与窗口关闭事件观测，再判断线程或 Shell API 行为；任何此类探针都需新源码/构建审查，不能把 CP572 静态判断写成产品修复或正式接受。
