# W16 control business fixture independent review

结论：`PASS_BOUNDED_CONTROL_FIXTURE_MECHANISM`。评审源 `104b83f0f4a6634a1367938da2bbf7b496483da2`，证据 `7801a5e28dff3b8c854db688c537764baf1d981e`；没有发现本次限定夹具范围的新阻塞代码问题。公开 replay 和普通 Task/Run/Experiment 回流证据可复算；私有分数通过一次受控的历史回执重算。两套公开数据及私有数据均为 baseline 2/2、candidate 2/2、gain=false，候选 REJECTED、stable 不变、resource/release operation 均为 0。本结论不接受正增益候选、当前 authority 或真实切换资格。

## Source boundaries

早期 `runFixtureControlReplay` 位于普通 flags/data/provider/coordinator/listener 初始化前。重放要求 AppContainer token，只接收单个 case、只读投影 snapshot 和固定的 20 SQL/2 contract 文件；协议校验限制同一研究周期 GET 与 false COMPLETE POST。程序在新 output clone 内取得 share-mode-zero lease 后打开 SQLite，实际调用 domain.Service.Handler，checkpoint 并关 DB，再关 lease。无网络 listener、provider、release 能力或原用户凭据输入。

投影从 caller-frozen snapshot bytes 创建全新数据库，枚举普通研究对象与已选择版本之间的引用；不复制原 auth、uploaded content、Artifacts、release state 或旧文件空闲页。ProjectProfile 引用凭据、复杂/报告/monitor cycle 均被拒绝。仅加入公开的 fixture principal/credential 与单项目 grant。反序列化 bundle 在可信注册时再次校验 schema20、默认系统行、对象/引用范围与唯一 fixture credential。它当前只覆盖 running manual cycle 的读取和拒绝行为，不支持成功关闭或 monitor/experiment 丰富状态。

新 profile 通过可信本地注册选定，不由 candidate 请求字符串选定。control BuildInfo 要求真实 apps/control 模块、Windows/amd64；允许变更仅三份 research business 文件，排除 replay/oracle/labels/acceptance/sandbox/release/SQL。普通 candidate 冻结 input refs、policy/suite/protocol、build/source hash 与 snapshot binding；旧 calculator 注册/执行/acceptance 分支保留，control record 明确拒绝旧 pair/proof profile。

Host 每 case/build 新建零 capability AppContainer。现有 sandbox 在 resume 前提供 native identity；新 runner 在 BeforeResume 比较 PID、creation、实际 image path/bytes。继承句柄只含 stdio，环境仅 SystemRoot 与新 staging 的用户/temp 路径。Host 在进程停止后读取输出 DB 的逻辑状态；评分不接受候选自报分数。case ID、请求、原 stdout/receipt、SID/job/argv/cwd、build/source、snapshot/protocol/policy/suite、退出/stream drain/cleanup/output-copy 均绑定。语义归一化仅删除根错误对象 correlation_id；状态、error、revision、权限/coverage/cost 等字段保留。要求零 DB 逻辑变化、零必需回归且至少一个新增正确 case 才有 gain。

私有 inputs/labels/proof 经新 CanaryStore 保存，公开 record 仅保留 summary/hash/ref。normal regression acceptance 重算公开 proof 与私有 verdict，绑定普通 Task/Run lease/inputs/experiment。current verifier 复用当前 principal、restricted grant、remote issuer intersection 和与 author/release 不同 authority root 的检查，冻结及消费时重新校验。原测试实际撤销 verifier 后，私有 verdict 和 regression record reuse 都拒绝；没有把该过去测试当作现在仍有授权的证明。

## Independent recomputation

完整读取 15 个相关源文件、测试及依赖，manifest 的 32 个 source/evidence hashes 和 native build inventory 的 170 个源文件 hash 全匹配。pinned Go hash `d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490` 匹配；contracts/SQL 无修改。source 到 evidence 为 18 份 receipt 文件；观察时 worktree clean。`104b83f` 对 `76b1bef` 只增加保留公开重算输入的 13 行测试输出，因此两项 confinement 与唯一一次旧 C09 selector 仍归其原 source，不伪称本次重跑。

最终 JSONL 包含 2 个 named PASS 与 21 条全部 PASS 的断言。前一 `76b1bef` combined run 保留 control no-gain 因非 canonical private path 失败的原结果，同时 legacy TestW16C09 一次 PASS/3 条断言；只纠正环境路径后的限定重试保留。两次更早开发失败（AppContainer 下 EvalSymlinks 无法枚举 C:\Users、普通 canonical root lease 不适用）也保留 tool-output transcript。没有擦掉失败或把零测试 compile 当业务 PASS。

独立 Python 脚本 `recompute_public.py` 读取两份公开 bundle/suite，重新计算原 snapshot 字节 hash、22 个 release 文件、projection schema/rows/credentials/objects hash；检查 public inputs/labels/suite/policy、每次请求/raw stdout/hash/native receipt 内部绑定和独立 SID。按真实响应与冻结标签逐字段重算，两套公开分数均为 [1,1]/[1,1]、gain=false；普通 flow 的 candidate plan、REJECTED/STABLE 与零 effect 字段也一致。此过程没有运行 control。Python 内存 deserialize 对 WAL 文件起初失败；仅内存副本的两个 journal header 字节改为 rollback 格式后读取，并按 modernc 的零长度 BLOB=nil 编码复算逻辑 hash；原始文件未改，原 snapshot bytes 另行核对。脚本与结果保留，便于复现。

本次 native executable 的作者观察 hash 为 `4276dc5b6c8ac7d0f18026dc6d39140bf20a94fbf1d030f3872e5162a15ba24a`，public 与完整 private/public flow 使用同一 binary。独立审查没有重编译或重跑 native；receipt 的历史 OS 属性可核对内部绑定，不能据此声称现在仍存在相同进程。

## Controlled private historical score

后补只读工具 source `aeaba8494ccde4b58c704d9007461e0dbbb215ee`，compile evidence `0e1aff046ab1c1ff8759e77f0362675e2a0d93db`，只有新增一个 helper 源文件。独立审查确认 OpenCanary(false)、Boundary、Describe、Read 只打开已有只读 handles，检查既有 ACL/root/metadata，不创建 key/index/file 或修复 ACL。工具只允许指定的新 store；public receipt/suite bytes 有硬编码 hash pin；private 数据只在内存。期待值来自公开 flow、外部 candidate plan 和已复算 public proof，未用 private 自述替代外部期待。stdout 为固定 summary schema，不输出正文、case、对象 ID、token 或路径；所有错误枚举化。

核对 helper source SHA256 `1c510d4a3275e56bde7fea3f7569b474d38435f318a6cd85128863a38f230b15` 与 executable SHA256 `0827e186a74a82a60f40fd21c1cd1c71e8af5efaff4ea83e620e87c80f3f93b0` 后，审查者按 root 的单次授权实际执行一次，exit 0、stderr 0 bytes、`RECOMPUTED`。proof hash 为 `bdb60068a9ed7b675a9ef3cb6c35c0429664c8211ae25a3223b7c31ba0a34c7f`；唯一匹配三份 protected metadata，inputs/labels/proof byte integrity 与 CheckControl 全部通过；私有结果 total=2、baseline=2、candidate=2、required=true、outcomes_equal=true、gain=false，external/historical/summary binding 全 true。原始 summary-only stdout 与 audit 已保留；没有 private payload 复制到普通目录或 Git。

## Remaining gates

- 私有重算 scope 严格为 HISTORICAL_RECEIPT_ONLY。当前 authority、current verifier/grants、当前 OS、已删除输出 DB、原 authority log authenticity 均为 UNVERIFIED；没有重建已清理 authority 或伪造 fresh grant。
- AuthorityGeneration 与 SourceSnapshotHash 由 PrepareEvolutionControlBundle 对原 snapshot 计算，但原 snapshot 未在本包保留。公开 bundle 只有安全投影，因此原 generation/source provenance 不能独立重算；当前注册与 proof 绑定只能证明冻结元数据一致，尚未对 live authority generation 建立 release-time 校验。
- 每次输出 DB 已清理。可重算公开投影和响应评分，并核对封存 Host 所观察的 output state hashes，不能现在重新读取原输出 DB 验证这些历史读数。
- 同 build 的正确拒绝不证明业务提升。正 gain control START_CANARY 明确 503，实际 R2 五私有动作仍显式 unavailable；更广业务覆盖、不同 build、真实 cutover/rollback、SCM/LIVE 与正式 W16/C20/A16 均保持 OPEN。

本次只读审源码与证据、公开内存重算及一次被授权的 summary-only private 重算。没有运行 native/provider/实际 DB/旧 S2/adversarial/旧 selectors；未修改生产源、SQL、合同、打包或台账。
