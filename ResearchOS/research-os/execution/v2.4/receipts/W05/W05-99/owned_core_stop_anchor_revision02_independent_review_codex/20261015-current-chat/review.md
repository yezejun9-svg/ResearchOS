# STOP-r2 全19 Source 独立审查

**NEEDS_CHANGES。f5db4a9639f1a50380eb5929ee6295887baeb756 不接受为 LIMITED_SOURCE_ACCEPTED。**

候选 tree `f6d44526df9f03abf1a5544cf4e7762be3d89208`；审查 Main `4f4023c9` 到候选的完整19文件（含8个继承路径），非只审11个修订文件。1204项引用文件、19个Git blob、275 captures、16个case refs均核对一致；全19及修订补丁逐字节匹配。

独立重建的正常双grant CLI 正例成功：schema24、87表、35行非空SQLite，online backup、一次原始句柄native terminate/wait、real lease及相同postflight成立。随后两组新fixture各自删除 worker/verifier synthetic receipt 的 `native_exit_code` 或 `native_wait_result`，原harness重新计算hash并真实编译双grant，两组仍返回 `STOPPED_LEASE_VERIFIED`、`terminate_calls=1`。这是必须修复的证明字段存在性漏洞。没有触碰当前Core/Desktop/Ollama、原产品DB、旧Run或私钥；synthetic证明不代表实际历史native closure。

## STOP-R2-F01 P1 缺失 native wait/exit 数值字段被当成零并授权 native stop

worker_native_exit/verifier_native_exit 的 native_exit_code 或 native_wait_result 缺失时 Go uint32 默认为0；NativeExitCode根本未作存在性校验，NativeWaitResult的!=0也无法拒绝缺失。两组独立真实CLI均进入STOPPED_LEASE_VERIFIED并调用一次TerminateProcess，违反原始严格native Wait/数值exit证明要求。这里只证明新synthetic fixture校验缺口，不证明原产品历史worker/verifier已关闭。

证据级别：fresh real two-compiled-grant CLI reproduction on two separate new synthetic fixtures。

最小修复：使用presence-aware uint32表示或显式required字段解码；worker/verifier两类均要求字段存在且非null。native_wait_result必须明确等于WAIT_OBJECT_0；native_exit_code允许明确的0或非零合法uint32，不能把缺失当0。保持原proof classes及完整原生capture要求。

位置：internal/ownedcorestop/proof_windows.go:158, internal/ownedcorestop/proof_windows.go:160, internal/ownedcorestop/proof_windows.go:286。

必要复验：

- worker与verifier分别测试missing/null/native_exit_code=0/native_exit_code=非零合法uint32
- native_wait_result missing/null/非零拒绝，明确0才满足此字段
- 负数/越界/小数拒绝；字段存在于另一proof类不能替代本类字段
- 真实双grantCLI重跑本次两个畸形fixture，必须在STOP_ATTEMPT/TERMINATE_INTENT/native action前拒绝；正常非空正例仍成功

## STOP-R2-F02 P1 最终 native signal 边界丢失调用者取消和更早的 context deadline

Commit创建继承caller deadline/cancel的ctx供SQL使用，但在最后一次Host查询返回后只调用g.checkAction检查grant墙钟；传入native层的是最初grant截止时间，未取ctx更早截止时间，native方法也没有ctx。调用者在TERMINATE_INTENT flush或native pre-wait期间取消，或CLI45秒deadline先到而grant仍有效时，最终检查仍可进入TerminateProcess。已消费intent不应退款，但必须零signal。

证据级别：source control-flow proof; no dynamic cancellation injection performed in this review。

最小修复：把有效invocation deadline取grant monotonic预算与caller ctx截止的较早者，最终intent前和原生call前都检查ctx取消及墙钟/monotonic时间；将context传入retained native边界，在pre-wait后紧接调用前检查。消费后的取消写出零signal/UNKNOWN并永久保留消费；一次signal后的有限完成流程仍不得retry。

位置：internal/ownedcorestop/stop_windows.go:193, internal/ownedcorestop/stop_windows.go:285, internal/ownedcorestop/stop_windows.go:294, internal/ownedcorestop/stop_windows.go:297, ops/supervisor/owned_core_handle_windows.go:337。

必要复验：

- caller已取消、caller deadline早于grant、取消发生在intent flush后和native pre-wait后，各自零native call
- 持久intent后取消跨进程重入不能重试；grant expiry after intent同样零signal且consumed
- 已有单次terminate失败与wait deadline tests保留，不把seam结果称为真实OS耗时证明

## STOP-R2-F03 P2 Core/parent映像读取尚未实现要求的祖先句柄固定

ownedNativePath通过EvalSymlinks按名检查，然后ownedNativeImage另行按名打开最终文件；ownedNativeProcess只保留进程和最终image句柄，没有逐级祖先句柄、逐级non-reparse/owner/ACL验证与生命周期。最终image身份hash匹配能挡普通替换，不能替代SA-D04明确要求的检查到打开之间路径稳定性证明。现有heldDocuments祖先保护不覆盖任意Core/parent image路径。

证据级别：source contract gap; no live ancestor race exploit claimed。

最小修复：在现有supervisor文件内逐级打开并保留image祖先native句柄，拒绝reparse/不符合授权边界的owner/ACL；从同一最终句柄计算image hash/ID并在ownedNativeProcess.close逆序关闭祖先。不要用一次EvalSymlinks作为稳定性证明，也不要新增放宽的proof类。

位置：ops/supervisor/owned_core_handle_windows.go:62, ops/supervisor/owned_core_handle_windows.go:72, ops/supervisor/owned_core_handle_windows.go:79, ops/supervisor/owned_core_handle_windows.go:138。

必要复验：

- Core及parent image路径祖先在validate/open/action边界的swap/reparse变化被阻止或拒绝
- 最终image写共享冲突、hardlink alias、错误parent身份均零signal
- 祖先保护测试必须覆盖supervisor image路径，而非只复用authority文件的heldDocuments测试

## 修复范围与未证明范围

三项源码缺口最小文件集：

- `internal/ownedcorestop/proof_windows.go`
- `internal/ownedcorestop/proof_windows_test.go`
- `internal/ownedcorestop/stop_windows.go`
- `internal/ownedcorestop/stop_windows_test.go`
- `ops/supervisor/owned_core_handle_windows.go`
- `ops/supervisor/owned_core_handle_windows_test.go`

永久消费崩溃矩阵如需补辅助测试，可在原允许路径 `internal/ownedcorestop/journal_windows_test.go` 内追加；真实CLI负例应在新隔离证据harness执行，不能修改冻结f5或注入生产validator批准。

- COV-01 SA-D02 SA06/SA07 S215：不能声称已执行完整grant-aware进程在claim/BEGIN/intent/native call各崩溃点、torn/missing journal及第三grant替换后的永久消费测试。
- COV-02 SA-D04 SA08/SA15 S202：缺少parent image祖先TOCTOU实测、foreign SID/Host/Owner完整cuts；不得把wrong index等同于全部native边界。
- COV-03 SA-D05 SA05 S211：缺少intent flush到native call之间到期/取消及caller较早deadline全路径证据，F02源码也未闭合。
- COV-04 SA09 S209：CP508要求full S209 dangerstate经true CLI Commit尚未全部具备。
- COV-05 SA01 SA-D03：现有parser单元测试并不等于所有畸形compiled grant经CLI的零side-effect计数证据。

## 诊断与边界

作者63条非零记录为54条预期拒绝/阻断与9条错误记录：1环境工具错误、2查询工具错误、1测试源码编译错误、2测试环境错误、2harness错误、1冻结工具错误。3条harness修正摘要仅链接原始记录，不追加失败数。6个capture含 `[no tests to run]`，仅表示编译/空选择，不计执行通过；未见显式SKIP文本。所有原始错误、作者初始capture gap均保留。

本审查初始发现读取未预写recipe；早期PowerShell只读合并捕获缺逐命令状态/env；自身递归引用审计先发生相对路径解析错误，第二次过宽递归被主动取消，实际logger保留native_exit1与RuntimeError stderr，最终有界审计成功。早期draft把仍在运行的本报告writer误记为缺after、把被取消审计误述为无after，已核对更正，draft保留。这些缺口未补造或用重跑覆盖。build/fresh CLI 均有执行前argv/cwd/env及完整stdout/stderr/native exit。

Formal仍0/42，全部22父任务OPEN；不授予Main、package或actual接受，不修改原始proof classes。
