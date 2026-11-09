# Independent Source review

Decision: SOURCE_ACCEPTED_WITH_ROOT_EXECUTION_PREREQUISITES. Authority NONE; formal acceptance false.

候选 SHA256 eaa745bb2ea461a875bda13bef2495e7a8fb3375446a687e15108021b883ae90 / 35845 bytes。三处 broker 环境替换与新增两个 helper、两个测试父之外，精确 inverse 恢复整个 T7 原始字节。原 84 断言、九个原场景、15 分钟 credential、4 分钟 grant、180 秒 broker timeout、CWD、Schema、source/private-stdin pins、manual Root sign 和 release 均保持。

helper 检查所有五个目录非空、绝对、存在且为目录，以 EvalSymlinks 与大小写归一后的 Windows Rel 同时检查词法和物理边界；proof root 与 SystemRoot/WINDIR 任一物理路径的双向包含均拒绝。请求 Environment 和 Python command.Env 只传 SystemRoot/WINDIR/TEMP/TMP，不传 proof key，不继承 os.Environ、credential、provider 或 USERPROFILE。

18 个本地文件系统/环境 leaves 与 10 个纯 Windows 路径比较 leaves 在两个精确测试父下可达。alias labels 只代表 resolved path comparison，没有执行真实 junction。此次没有运行 Go、gofmt、编译、SQL、native、model 或网络，也没有读取 private key/DPAPI 数据。

Root 执行前必须另行审查新 controller 对 proof key 的精确白名单加入与 fixed frozen Environment 来源。旧 controller ENV_KEYS 缺少 proof key，不能直接复用。Root 必须冻结并持有隔离目录资源、提供真实系统目录值；helper 的即时路径检查不等于目录资源持续持有证明。完成 fresh compiler/input/resource pins 和 28 leaves 实际结果审查后，才能按 Root 已授权边界进行一个 fresh positive native case。actual/native/formal 接受均留给独立后续审查。

835 只证明失败执行和已审查 SQL cleanup；原报告 harness FILETIME 134359787460741280、rehearsal FILETIME 134359787476336020 为失真报值，不予接受为原生观测。原生回执分别精确为 134359787460741284 和 134359787476336016，使用 Python int 读取并输出十进制字符串。原件保留，843 资格说明仅用于错误报值限定，不提升产品证明。841 outer1/marked Python NULL/inferred Python1 与 native NULL 分开。

本审查脚本失败 846 已保留旧脚本与完整 IO：误用历史 rehearsal result 小写字段，actual outer1/marked Python1；两条 marker 原样保留。原失败未重试，新 revision 用 Result 大写字段，actual outer0/marked Python0。两次三组 SourceReadGuard 均验证成功、全部关闭、retained0/errors[]。修正版固定 53 个公开输入并复核无漂移。Main/T7/作者包/canonical 均未写入。

STOP：仅交付 Source 复核证据；没有持有 canonical lock，没有接受实际 native 或产品交付。
