# CP573 条件分支探针准备

状态 `PREPARED_ONLY`；Root preparation scope SHA256 `f43998c1617d0e7596b7ef9f05b618e8b30f7de789511b295d66be992af7bb7a`，明确 `native_execution_authorized=false`。本轮只写本目录，未启动 helper/native/产品，未改旧证据、产品源码或 CP572 自有 state。冻结 helper SHA256 `92573aacf6f2caab9baead612a13cf0eef688fc1e5a4177ac6bf5b1cbfa7a463` 原样复用，未重建。

`controller.py` 从已接受的 prep02 复制，变更见 `controller.diff`。保留原有 Popen 句柄持有、`BaseException` 后保活、严格 Root release、唯一自有可见 `#32770` 的 IDCANCEL 机制。新增的 case 计划最多两次：先 C（原 A 七键及值、同一 CP572 自有 D 盘 synthetic profile/中文 hint、补 scope 列出的非敏感 OS 键，并从 synthetic USERPROFILE 派生 HOMEDRIVE/HOMEPATH，保持 SW_HIDE）；仅当 C 可见且正常 IDCANCEL 后跑 A2（原七键、SW_HIDE）；仅当 C 无 IDCANCEL 且在 2 秒内 Shell-null 后跑 D（C 同环境，仅清 STARTF_USESHOWWINDOW）。其他结果停止，不重试。D 启动后在 `open` 前核实 helper 的 `GetStartupInfo` 只比 C 少该 bit；A2 应与 C flags 相同。

只允许复用 `old_probe_state_root` 指定的 CP572 synthetic state。preflight 核 Root scope、旧 controller/preparation/helper/CP572 环境与 spawn 引用哈希、候选 clean commit、新回执目录和 synthetic state 无 reparse；A 的七键、中文 hint 与 CP572 回执一致。`BASELINE-INPUTS.json` 是本轮对该自有 state 的只读快照：8 个目录/文件条目，manifest SHA256 `e137a9c455e4ae06a27d18e1c8aa05077374e711dbd9d390a5b4aa49fa8269a0`。C 只新增当前存在的 `ComSpec,HOMEDRIVE,HOMEPATH,PATHEXT,Path,ProgramData,ProgramFiles,ProgramFiles(x86),SystemDrive,USERDOMAIN,USERNAME`；当前 `OS` 不存在，运行时若环境变化会因固定环境哈希拒绝。当前 A env SHA256 `70d638420b1ba210ce8bef5f3edcbfdc8179285008647d0bdef516cd9271457e`，C 为 `af8e86d4e4c767d24852e8df933276f6a911213eb204be7a7b735062c94e3a99`。Root 运行 scope 须逐个固定这些哈希并在启动前复查。

每个 case 在 Popen 前后分别扫描旧 synthetic state，记录所有目录/文件的相对路径、类型、大小/哈希与修改时间，拒绝 junction/reparse，另写变更路径；只读扫描不清理缓存。helper stdout 改为字节读取并保存完整 `stdout.raw`，仍解析 `ready/result` JSON；失败时尽力写 `stdout.partial.raw` 并进入原保活路径。stderr 保持原始字节文件。C 若可见而 A2 不可见，只支持“补充环境组在这一自有 profile 中影响显示”；两者都可见提示固定顺序/残留状态影响，需要新 scope 的反向确认。C 不可见而 D 可见只支持隐藏启动影响；都不可见则 profile/hint/session 仍开放。任何一例都不是产品正式选择证明。

`test_controller_mock.py` 是纯模拟 8 项：C→A2/D/异常分支、七键环境与批准新增键、隐藏位差异、原始 stdout 字节、state manifest 变化、首个 postspawn 回执故障保活、内层 I/O/中断/过期 release、`python -O` 拒绝。原始测试 stdout/stderr 与 exit=0 在 `mock-tests.*`。未执行 helper 或 native；旧 prep02 测试未全面复跑。

Root 须另封最多 2 次、精确路径/哈希/条件分支的 run scope，并用普通 Python 执行。`RUN-SCOPE-TEMPLATE.json` 保持 `native_execution_authorized=false`，不能直接运行。
