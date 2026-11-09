# bridge checkpoint compat exact2 独立审查

结论：**SOURCE_ACCEPTED_LIMITED**，无 findings。接受限于本次源码分流修复、原有 legacy Core 路径回归及实际隔离 Native fixture 验证。未进行 Main 整合、安装包验证、产品模型调用或原产品 pause/resume；formal increment = 0。

## 冻结身份与输入

- Worktree `D:/作品集/ResearchOS/research-os/.local/worktrees/bridge-checkpoint-compat-20261014`；HEAD `0f9a870aed72785297a9999396fc8c760b296e13`；tree `fa071c9be7e39628c0b86ad43f77d5c50be63c7c`；base `a7ec7ebf2d53848ea163b6115667b3e3761a6bd2`。
- Scope CP475 SHA256 `b6af6ed6677b524673885a7b290022880045398b93c92420d28c620b21f25504`。exact2：`adapters/runtime/bridge_windows.go` SHA256 `71555893e2f4793acdd2ebc83ef57e98c6a5c84cf1742dbec00b42ea4581c224`；`adapters/runtime/bridge_legacy_checkpoint_windows_test.go` SHA256 `c7d8af8bc1e2d7b7cf5e988cce0075cd2ff025fae2b7ec0724392ec13a8cd575`。
- 作者 evidence-manifest SHA256 `e6f11bbf42a5f605106720dbdfba63a5873714ee98d1d5c58cf201f8e9194d35`，12成员逐项校验；report.json SHA256 `046e800454d9085a0c71302a1afca221d5e57cb08a4044c60611c3748604d4da`。包括 manifest 自身共13份作者文件已保存。
- 锁定 Go1.27.1、modules、compiler/toolchain、编译依赖及 Node/worker bundle共3772个输入文件在审查结束再次核验无漂移；raw go-list覆盖354 package条目。前后 Git clean、diff --check通过，原有两份 Core legacy test和worker/host setup依赖与base逐字节一致。

## 生产路径判断

1. `StartBridge` 在接收 worker输出前，从 Host给定的 immutable manifest 与 request 选择三种 mode。request 的 task/run/epoch必须对应manifest；显式协议只接受 RESEARCHOS_PAUSE_V1，包括 null/空字符串/布尔/unknown/重复键均拒绝。无协议的 Mu选择disabled，普通turn仍可执行；只有无协议的非Mu profile选择legacy。worker不能通过输出帧选择或切换mode。
2. checkpoint ingestion、ACK、turn.paused都按已冻结mode分流。V1保留原capture校验，<=64KiB元数据frame与<=12MiB checkpoint文件分别受限；要求绑定process/manifest/epoch、输入hash、native stream drain和完整typed Artifact/use/journal seal。缺元数据、inline fallback、弱ACK、空paused payload不能降级。legacy只允许有限inline JSON、空或checkpoint.json标签、无V1 key；ACK保持Core原有Artifact响应；paused不接受typed payload。未协商Mu不能走legacy checkpoint。
3. 离线恢复从Host原始dispatch input/request.json重读mode，与InputHash和外部传入的manifestHash绑定，并重核原task/run/epoch。journal mode擦除/改值、typed字段残留与disabled checkpoint均拒绝。原dispatch目录由Host私有ACL保护，worker只拿只读staged input；此边界没有把worker可写output当成模式来源。request reader复用实际句柄路径核对、final reparse拒绝、祖先路径解析、FILE_SHARE_READ与大小上限，目录junction负例已fresh通过。
4. 恢复继续要求原进程已停止、结束事实、stream drain、cleanup；paused新增context/protocol/全部ACK/exit0/outputCopied/非cancelled检查。V1恢复仍核checkpoint原始字节hash和durable seal。legacy Core保留 `native_resume=false`，未将旧context rebuild伪装成SDK原生恢复。

## 独立执行与原始观察

采用同一锁定工具链，mod=readonly、count=1、网络modules禁用，D盘共享cache和本审查唯一D盘temp。所有原始stdout JSONL、stderr、argv/cwd/environment/native exit均保留。

- 原始 V1 Native test及process/epoch绑定负例：2顶层、6子测试通过。为保留可复核原件，仅以Go overlay在原测试两条日志旁增加复制观察，原断言未改。实际运行生产Node+Mu bundle的两个AppContainer，暂停checkpoint **89066 bytes**（大于64KiB），sequence6→paused7，同Run epoch1→2，新旧PID不同，恢复消费原队列2条，模型计数累计3，原prompt未重放。
- 暂停、恢复、普通Mu各保存原始bridge journal、stdout/stderr、request；暂停另存checkpoint bytes和journal fact，恢复另存result。独立再次核对raw hash、frame序列、receipt身份、空capabilities、exit0、children stopped、streams drained、cleanup complete及output copied。记录来源为本轮实际sandbox执行，不仅引用作者报告。typed seal仍使用synthetic Core-shaped receipt，未宣称完整Core数据库Artifact/use接受。
- 原始 `TestRuntimeCoordinatorCheckpointResume` 和 `TestRuntimeCoordinatorCheckpointCrashRecovery` 未改，fresh 2/2通过；日志保存实际checkpoint_durable子进程exit86与新恢复子进程exit0，lease未延长、不完整terminal禁止resume。
- 完整跨模式/大小/重解析/离线降级负例，加两个独立测试：8顶层、47子测试通过。独立附加explicit null/false/duplicate protocol、非Mu及Mu V1 journal字段擦除拒绝；另以真实AppContainer完成**未协商V1的Mu普通turn**，1次合成MODEL响应、无checkpoint、exit0、原输出可读，证明旧Mu正常运行没有被整体拒绝。
- 总计12顶层、53子测试，全部native exit0，无skip。初始runtime精确名称过滤只选中了两项native测试，后续单独按prefix补齐负例，未重复native pause/resume。作者6次attempt及2次失败完整保留，未改失败计数。

## 边界与交付

本轮reviewer只写独立证据目录，Go overlay不修改源码。没有读取/修改原产品数据库、控制原产品进程、调用真实provider/model、构建安装包或写Main。临时测试目录已由测试清理，剩余空目录移除；正式原始观察和复现脚本保留。Root可据此整合本exact2；后续组合Core、最终包及真实产品资格/暂停验收需使用对应的新证据。作者与reviewer均未为本次增加正式用例接受。
