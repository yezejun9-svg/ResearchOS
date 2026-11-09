# B3 最小源码租约补正：无模型资格 producer + 固定 helper

状态：SOURCE_LEASE_PROPOSAL_ONLY。只供 Root 登记下一源码 lease；没有生产源码修改、执行 scope、helper binary、fixture、listener、Native/model/probe 或测试执行。旧 Echo 2/2 与旧 FAILED Task 保留。原 a58d 合同的有限操作/正控/失败保留/不放宽权限条款继续适用；以下仅修正具体接线和 CLI 事实。

## 1. 当前接口：两个 Ensure 阶段，不能保留旧 bool

当前 B1 rev3 的 CodexQualificationProvider 是 Ensure(context.Context, CodexTurnEvidence) error，不是 Qualified(...) bool。以 Root 最终批准的 B1 rev4 接口冻结为编译基线，不能覆盖 B1 文件。

B3 新文件定义生产 constructor NewCodexRPCWithNativeQualification(options, qualificationOptions)，只接受可信 Host composition 的固定授权/根目录/helper身份/预算；不接受 provider/function/PASS bool/receipt JSON。同 package 内调用普通 NewCodexRPC，再安装 B3 私有 concrete qualifier，不走 ForTrustedGoTest。旧 constructor 保持 nil closed。

包装 driver 的 Start 在**任何 RPC child 创建前**调用私有 ensureLaunch(ctx, launch)。一次合成 qualification 停止并完成收据后，才允许 delegate B1.Start。B1 随后调用接口 Ensure(ctx,e)：此时仅验证已存在的活体观察与这次 Task/Run/epoch/source/template/binary/home/HostBoot/expiry 绑定，绝不在这个回调里再启动 Native。Ensure 本身不 mint B1 permit。

包装 handle 的 Cancel/Wait 必须涵盖资格和后续 RPC 两阶段；后台准备仍属于原 run context。若采用异步包装，必须在两个阶段交接处再次检查 cancel，不能取消后继续 spawn RPC。观察单 consumer、失败/UNKNOWN 消耗一次、并发调用不重复 spawn。没有权威注册时直接 QUALIFICATION_REQUIRED，capability GET 无副作用。

## 2. 确认 CLI：不加 windows 子命令

旧 actual Echo05 的冻结 wrapper 与实际 launch-plan 完全一致：-c windows.sandbox=mxc sandbox --include-managed-config --permission-profile :workspace -- C:\\Windows\\System32\\cmd.exe /d /c echo MXC_OK。这只验证已发生的命令形状，不转移其权限/环境或可用性结论，也不允许重跑。

官方 rust-v0.166.0 的 SandboxCommand 将 HostSandboxArgs flatten；Windows 编译直接选 WindowsCommand。SandboxSubcommand 只有 Uninstall，Windows dispatch 由 cfg 完成。**B3 模板没有漏 windows；加入 windows 反而会进入命令部分。**

冻结资格 argv 的结构应是：

    <pinned Native exe>
    <B1 canonical security -c pairs with fresh qualification nonce and S>
    sandbox
    --include-managed-config
    --permission-profile <qualification nonce>
    -C <QW>
    --
    <S>\qualification-helper.exe
    --plan-v1 <bounded encoded fixed plan>

-C 需要显式 permission-profile，include-managed-config 同样需要它。目标 exe 使用 canonical Windows 反斜线，shell=false。无 cmd/interpreter、ignore-user-config、sandbox-state、额外读写 grant、setup/admin、fallback command 或 retry。

B3 可以在同一 runtime package 调用 B1 固定 builder，严格核对并替换末尾 app-server/--listen/stdio:// 为上述 sandbox 后缀；若不匹配立即失败，不能盲切片。或者使用 Root 后续串行提取的共享纯 projection。前一种不需要修改 B1 所有文件。资格 projection 比较 -c 语义/有序数组；B1 完整 RPC config hash 还含 thread/start 字段，不能要求它与 sandbox 全 argv hash 相等。记录 B1 template identity + qualification rendered argv hash，两者关系由 builder 和测试证明。

## 3. 不与 B1/B2 重叠的八个新文件

仅建议下列文件；本次只读确认 Main 中均不存在。无 go.mod/go.sum/锁文件改动，无新依赖。

1. adapters/runtime/codex_qualification_windows.go — concrete producer、私有观察、包装 constructor/handle、Host 正控与阶段绑定。
2. adapters/runtime/codex_qualification_capture_windows.go — 资格 Job/流收集/耐久 partial/界限与终态 proof，复用现有原生进程 primitives。
3. adapters/runtime/codex_qualification_windows_test.go — 绑定、一次性、取消、正控/评价器和组合 fake。
4. adapters/runtime/codex_qualification_capture_windows_test.go — 真正本地 fake-child 的输出/超时/Job/硬停证据测试。
5. internal/qualificationprobe/plan.go — 小型纯数据协议/固定 case 集/大小界限/结构验证；不含 READY/authority/进程代码。
6. internal/qualificationprobe/plan_test.go — schema、路径布局、固定 case、错误码/bitmap反例。
7. cmd/researchos-qualification-helper/main_windows.go — 独立 helper，只依赖窄 plan package、标准库与已存在 x/sys/windows；不得 import 整个 adapters/runtime 或 Core。
8. cmd/researchos-qualification-helper/main_windows_test.go — plan 拒绝和合成系统调用边界测试，不运行 Native。

helper 不接受任意 command/URL/可选操作列表。固定 S/QW/D 布局和文件名，从受限 plan 还原测试目标；Host 原始 authority 不来自 plan JSON。helper 只输出事实/数值错误/读取 digest，不输出 PASS；Host 评价器与正控决定有限观察。构建产物与打包/Host constructor 接线由 Root 另行串行集成，不在此 lease 改 B1/B2 拥有的八文件。

## 4. 必须解决的接线细节

- **目录冲突：** B1 Start 使用 os.Mkdir(launch.Directory)，要求它尚不存在。B3 必须使用独立、固定 Host-owned 资格收据目录，不能提前创建 launch.Directory/cwd 来放收据。S/QW/D 与资格收据不嵌入该目录。否则资格 PASS 后 B1 仍必然失败。
- **源绑定顺序：** 第一 synthetic Task 的 S 必须在项目/Task source binding 之前由授权准备步骤建立；lazy ensure 验证该精确 S，不能为已有 Task 换成另一个新 source。只在明确授权的合成布局里准备固定 fixture/helper；不修改真实项目。
- **cwd 结论边界：** QW 是资格子进程的独立 cwd；B1 后续创建的 owned RPC cwd 是另一路径。报告不得称后者已被直接 probe。其请求权限由 B1 固定构造与逐次屏障约束。若 Root 要求同一路径实测，须另行串行改 B1 创建边界并审查，不能在 B3 偷改。
- **预 RPC 失败结算：** 资格失败时没有 model PID，也不调用 model BeforeResume。Root 必须与 B2 明确“已消费准备、RPC child=0、prompt=0”的既有 failure/UNKNOWN 映射；不可把资格进程 identity 冒充模型进程。使用现有结果 reason 与受控 artifact；需要 DTO 变更则由 B1/B2 owner 串行实施，不在此 lease 修改 shared codex.go。
- **真实预算：** 现有 newJob 只设置 KILL_ON_JOB_CLOSE，不能把它描述为已施加 16 processes/2048MiB。B3 新 collector 必须用受审 SetInformationJobObject 在该资格 Job 上实际设置所需硬限制并保留原标志，或者证明 Root 外层已严格承担相应界限。设置失败禁止 Resume；不得改 f13/Kernel。
- **总时限：** 资格 <=60秒包含前后正控/清理；后续 B1 的 Timeout 只能使用原 Task 总预算剩余部分，不能重新给完整300秒。单次 Native qualification、单次 RPC process、最多一 model turn 分开计数。
- **环境：** Echo05 whitelist 与当前 B1 Environment 不完全相同。B3 绑定当前批准 B1 的环境策略/normal home，而不是复制旧 Echo 环境后宣称等价。禁 CODEX_HOME 注入，home 无分号，实际 launch 前复核。D03 正常 Native context/auth/cloud 行为仍在范围内；本次不读私有配置。
- **有限探针：** 仍只承认合成 S read、D denied read、S/QW write/create denied、一个 IPv4 TCP tuple；不是全路径隔离或当前 managed graph 的完整证明。已知 fallback/warning/异常诊断不得悄悄忽略。B1 当前进程 nonce barrier 和 B2 最终 fence 始终独立必要。

## 5. Root 串行 handoff 与放行条件

先完成 B1 rev4 源码修复/审查及新 f13 fake 测试，再 pin 共享 Ensure/context/evidence、builder 和新 constructor 所需类型；B3 可先实现独立 plan/helper/collector，不抢改 B1/B2。

Root 后续串行改 Host composition 使用 B3 constructor、固定 helper build/hash/shipped identity，完成 pre-RPC failure settlement 接线审查。未集成时默认 nil/无授权仍 closed；不能用 test constructor 暂时接通。生产 build/packaging 若缺新 helper 要明确失败，不加下载/安装/用户手动设置步骤。

作者只准备源码和 fake 测试计划；所有真实测试需 Root 新 scope。优先新增反例：precreated launch.Directory、S mismatch、Ensure 回调误启动第二次 Native、取消阶段交接、超时预算重置、Job limits 设置失败、未同步诊断硬停、原始Native错误码与bitmap伪造、正控失败/网络拒绝假阳性。保持旧 Echo 2/2 和 Task 失败记录。

## 事实与来源

- a58d 原合同 SHA：a932a1c84652dc3a9af78ae5299701e74da2dc70e4749a94906e321ae012b9e7。
- 当前 B1 rev3 codex_rpc_windows.go SHA：b6553811324fbec142ae7073b0eb6b4a1a0576e145ae305e3719f527e24d3b7b；Ensure 签名33–39、Start mkdir155、生产 nil qualifier392–398。此版本仍 BLOCKED，不作为最终可用基线。
- Echo05 wrapper SHA：b37e098a338114088bf587b21d77c24eccee0a4f9019b5078d610754067faea4；实际 launch-plan 为 product-v1-owned-verification-20261104/runs/mxc_availability_20261105_f602/mxc/launch-plan.json，本次仅只读。
- [CLI host flatten 与 Windows 类型](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/cli/src/main.rs#L465)，[Windows dispatch](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/cli/src/main.rs#L1807)，[WindowsCommand flags](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/cli/src/lib.rs#L151)，[Windows sandbox handler](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/cli/src/debug_sandbox.rs#L132)。

没有发现必须增加 windows 子命令或放宽权限才能实现的要求。真正待接线点是 current Ensure API、fresh directory 生命周期、pre-RPC failure settlement、硬预算与 Source/Host authority。formal/product/native/model/test 增量均0；D writes=0。

