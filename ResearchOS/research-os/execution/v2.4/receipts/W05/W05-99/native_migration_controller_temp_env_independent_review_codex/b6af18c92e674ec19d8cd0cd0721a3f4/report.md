# Independent CTL3 Source review

Decision: SOURCE_ACCEPTED_PENDING_ROOT_FRESH_CONTEXT_AND_ACTUAL. Authority NONE; formal acceptance false. Reviewer is independent of CTL3 author.

CTL3 HDF/MF、31 个本包成员、CTL2 的全部 13 个成员及 EnvSource 的全部 27 个成员均已固定并以实际 SourceReadGuard 读取。总计 79 个唯一公开文件。复核结束无 SHA256/bytes 漂移，三组 guard 均 PASSED、closed=true、retained_handles_count=0、errors=[]。公开内容副本已留存。CTL2 原 MF 使用 manifest-relative key 定位，原 declared path 字段另行保留，不改写旧包。

候选 root_native_migration_controller.py SHA256 a1f53e223f47c5d8ecdb7edc5f94fec0bcc36beae9774d16ad9d0002b6ef638a / 42696 bytes。独立 diff 只有三处插入：ENV_KEYS 增一个 proof key、新增一个 helper、context 增一次可选调用。独立 inverse 完整恢复 CTL2 原始字节；其他 30 个顶层定义源码和 AST 不变，去掉该可选 guard 后 context AST 与 CTL2 相同。Python compile-to-code/AST 检查通过，但没有导入或执行 controller/context/helper/observer。

提供 proof key 时，helper 要求非空绝对 canonical 存在目录，proof/TEMP/TMP 字符串完全相等，严格位于固定 R/.local 下。原 trial 的词法双向包含在 proof resolve/stat 前拒绝；local/proof 的 canonical 判定排除 resolved alias，随后再次校验物理包含与 trial 边界。SystemRoot/WINDIR 要求 canonical 存在目录，并拒绝与 proof 双向重叠。helper 只访问目录 metadata，不读文件内容，不枚举目录。没有 proof key 时保留旧 context 路径；这不代表可使用新 broker 启动缺少 proof 的 native 流程。

Root worker 仍从固定 cfg.Environment 复制环境，没有 os.environ 继承。EnvSource 对 broker request 和 command.Env 仍只转发 SystemRoot/WINDIR/TEMP/TMP。12 个固定 cfg fields、8 个 public refs、7 个 harness RawPins 与 compiler/test/embed/product/runtime resource 的完整 FrozenInputs 映射符合源码，均为后续 Root 实际前置，不是已通过的 context 证据。未知键/NUL/type、Source identity、compiler provenance、Owner grant、private pipe、4 分钟 grant、manual signing、atomic publication、specific release 和 Job closure 原有代码均保持。

16 个 boundary expectations 全部 NOT_RUN；本轮没有 context/helper/native/SQL/sign/model/network 执行，没有 private key/DPAPI 或原 trial 内容读取。Root 须使用独立新固定 cfg、执行路径对应的 ControllerSource、完整 retained guard 和资源闭合，进行授权的 fresh context 与实际检查。随后 fresh compile 和 EnvSource 两个测试父/28 leaves，才可按现有 Root 权限启动单个 fresh positive；实际 native/正式结果仍须独立复核。

835 的原错误时间与 native 原始观测保持区分：Go 错误报值 134359787460741280，原始 invocation 精确值 134359787460741284；此次 CTL3 rehearsal 134359787476336016 仅保留为 Root-reported actual，未读取 child invocation。不会以 Source 元数据或 CP361 更正代替产品证明。

本复核新错误 850 原样保留：初版脚本把 835 ref 的正斜杠路径与 pathlib 的反斜杠输出直接作字典比较。79 文件 SHA/bytes 均相同，不是真实 Source 漂移。原命令 outer1/marked Python1，两个 marker 均为 1；原脚本和完整 IO 未覆盖，新 revision 分列内容漂移、canonical path 差异和等价拼写，outer0/marked Python0。失败与修订 guard 均全部关闭，没有计数重置。

STOP。只写当前独立复核 namespace，Main/canonical/作者包/旧 Source 未改；没有自签 actual/native/formal 接受。
