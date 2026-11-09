# M1-02 Core 累计源码独立审查

结论：**LIMITED_CUMULATIVE_SOURCE_ACCEPTANCE**。可以接受当前冻结候选中相对最初 Core 基底的完整 M1-02 累计源码变更，范围为 **21 个不同文件**。这是累计源码接受，不是仅接受最后 exact2，也不是 runtime、安装包、实际产品或正式用例接受。没有新增阻断此源码范围的问题。正式状态保持 **0/42，22 个父任务全部 open**。

## 精确身份和范围衔接

最初 Core base：`60f8c81a7529081eb51d525ab913d63102148a46`，base tree：`01c9969cc34296b0e8978c2276d69cad29e9759f`。

当前 HEAD：`8f50cb57ff821554aef17e9a9bd5208935489d50`，tree：`361ead86ee812d5e040fe1d2cde2a92297eb639f`。工作树及所有21文件当前字节均与 Git blob 一致，最终 clean。

| 阶段 | 冻结终点 | 精确改动 | 独立结果如何衔接 |
|---|---|---|---|
| 原始 Core | ff5ac2047566a52388188b84f267217d8582c571 | 17文件 | 初次原生流程/取消/未启动恢复通过，R1 阻止当时接受 |
| R1+共享预算修订 | 36b2634bfebe6201a14b7661f2dce32b7f1a5098 | 9文件 | 普通两轮暂停及预算回滚通过，新增R2跨心跳失败 |
| R2修订 | 8f50cb57ff821554aef17e9a9bd5208935489d50 | 2文件 | 当前暂停心跳修复；独立17秒旧复现、模型/工具路径和撤销通过 |

17与9有5个文件重合，exact2全部位于此前范围内，因此联合差异为21，不是28个文件。原17中其余12个文件至今逐字节未变。三个阶段的 Git diff 文件表、每份 source manifest、scope 白名单及其架构引用均实际核对；9个 schema25 依赖与基底及原冻结哈希完全一致。6份历史证据 manifest 的241个成员重新核验通过。完整逐文件哈希和阶段归属见 cumulative-files.md；机器可读范围、三份完整 requirements、依赖及引用见 current-inputs.json。

## 旧问题的累计闭合

- **M1-02-R1**：第二次暂停曾因旧 activation 强制 Task RUNNING 而失去检查点。当前操作目的在同一 gate 事务内验证精确当前 pause intent，保留历史 activation 全部验证；普通 BLOCKED 不获得权限。第二轮模型和实际 Host 工具分别完成 PAUSE→confirm→RESUME→epoch3，保持 Run/attempt、四条队列各一次消费。
- **共享 local-launch RELEASE 幂等缺陷**：只在 reserveRuntimeLocalLaunch 校验规范旧 RESERVE 与确切 RELEASE 并保留原账；没有改全局 appendBudget。独立四epoch/同epoch重放、错误hold/release、四条原生轨迹各六行账本及完整successor回滚均通过。
- **M1-02-R2**：周期心跳每次在同一 admission 事务读取当前 intent，继承完整 Owner/Goal/lease/manifest/session/queue 门禁，15秒周期不变。上一轮逐字节未修改的17秒失败overlay现通过；模型与工具第二轮均实际等待17000ms且heartbeat_at推进。HTTP取消、Owner撤销与隔离Goal/lease故障均取消Bridge，无epoch3及额外队列消费。

此前两份 NEEDS_CHANGES 报告仍原样保留。这里通过明确的源码与证据闭合其 finding，不改写旧 verdict，也不把各层 PASS 简单相加冒充全产品通过。

## 累计架构约束与实际证据

已逐项追踪 HTTP 元数据→canonical pause请求→effect cutoff→captured bytes/seal/use→顺序typed ACK→native stop→显式RESUME→原子successor→required activation→初始化确认的生产调用链。独立 invariant-matrix.json 将原scope17、scope9、scope2各项要求按13组映射到当前源码位置、实际证据和测试局限。

关键边界保持：公共 Task 状态图不变；窄Task例外只接受当前事务内新准备的同Run successor。sealed-pause-activation 是固定内部证明类别，要求schema25、非legacy/非bootstrap完整资格、原capability/init receipt、sealed bytes/use/principal、STOPPED/drain/cleanup、SDK输入/session/queue证据及当前权限；没有把 supports_resume=false/null 改成通用恢复资格。缺marker/activation不能退回普通启动。PREPARED恢复仅限没有worker/identity/journal/effects的同epoch；STARTED/UNKNOWN不盲重跑。CANCEL、restore fence及当前权限失败阻断。effect新key拒绝，原PREPARED只能按cutoff原sequence开始一次，物理工具发布仍复核当前权限。预算全局语义、permission门禁、SDK、Bridge和公共合同未在累计范围中改动。

复用当前HEAD已独立完成的4次命令/25个顶层PASS；没有重跑刚通过的暂停测试。本次仅补此前尚未在后续broker/model/tool修订后运行的普通队列集成组：3个顶层PASS（同进程Mu队列、取消UNKNOWN effect、Goal取消与claim前后顺序），21.336秒，0skip。当前候选合计5次独立命令、28个不同顶层PASS、0FAIL、0SKIP；历史其它候选测试不重复计入。完整argv/cwd/环境、输出和前后21文件guard在01-current-native-queue目录。

## 接受边界与保留问题

真实执行部分是隔离 Windows Host、普通HTTP产品API、canonical DB、AppContainer、broker、verifier和冻结Mu worker；模型回应全部为本机synthetic，未访问真实provider。Owner撤销使用Service接口；Goal/lease/预算负例为隔离DB注入。未启动lease恢复是原生前置流程加故障模拟，不能称作完整OS崩溃验证。未对每个文件/API/SQL cut和每个immutable字段做穷尽原生故障注入；已测夹具与静态门禁证据在矩阵中明确区分。

**冻结M1-01 Bridge的两个旧inline checkpoint兼容回归在本次仍开放**：TestRuntimeCoordinatorCheckpointResume、TestRuntimeCoordinatorCheckpointCrashRecovery。原作者已在冻结依赖定位，累计21文件不包含Bridge；本次没有把另一张兼容卡结果并入，也不宣布所有runtime回归通过。legacy-checkpoint-compatibility.md及失败日志已随原manifest重新核验。此限定接受只评估Core累计差异，不能解除依赖兼容门。

schema25依赖只核验冻结身份，没有对已安装schema24产品数据升级、验证实际Desktop/真实模型或签发正常package/Main集成许可。构建中的其他package不属于这份候选或证据。原作者18/7、原独立5/2、修订作者23次(11PASS/11FAIL/1SKIP)、修订独立5/2、R2作者7次(6PASS/1编译FAIL)均保留；历史清理拒绝未重试或更改。本次无源码、Main、共享状态、产品数据或私钥写入。
