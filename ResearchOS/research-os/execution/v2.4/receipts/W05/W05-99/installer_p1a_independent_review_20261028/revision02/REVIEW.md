# Installer P1a revision02 — ACCEPTED_SOURCE_STATIC_P1A_ONLY

本轮接受固定提交 `69f91b72e919c01a2297da31109e59bf7a54ccbf`（tree `f7cbb41dfc4cf5a5ef730161bc58afc1ec44c599`）的 **P1a 源码与静态构建范围**。R1–R4 均已关闭，未发现新的阻断项。正式增量 **0**，不表示 W05、父任务、22/42 正式验收或实际安装完成。

R4 修复已独立验证：临时 cp570 路径/hash 常量已移除。CLI 要求显式 `--scope` 与外部 `--scope-sha256`，先比对摘要，再解释 schema/owner/worktree 与授权根。当前 Root 给定 cp571 摘要可准入；同字节 scope 换位置、两份不同 scope/授权根无需改源码均可准入。真实 CLI 使用有效 fixture scope 已进入后续 frozen-source 检查，缺少摘要则由 argparse 拒绝。fixture 故意为空，没有构建或运行产品。

本轮 7 个 Python 回归测试通过；新增独立检查覆盖空/错误摘要、错误 schema/owner/worktree、缺失或非字符串根、dotdot、重叠及不存在的根，均未写 output/receipts。畸形 JSON 配错摘要时先得到摘要错误，确认 hash-before-parse。R2 路径/junction 和 R3 已有回执保护无回退。R1 的 Go no-replace 代码和测试摘要与 revision01 相同，沿用前轮 Windows 实际提交/竞争保护证据，不重复跑 Go。

已核对 exact2 clean、提交 blob 和本地源码摘要；finalizer 源码、Go 测试及 payload schema 均未变。revision02 的 manifest 摘要仍为 `2e2586650b06de5c52627374337b96da8e382c4cbfd70499ddc6aeb53094091c`，finalizer 摘要仍为 `016a45961612fb1facfebfec316fae9f3d35528087743cab9205a8e8c88d2171`。作者使用新 scope 的完整构建回执已读取并固定引用；本轮独立检查没有重复全量 payload rehash、复制或 relocation。

接受范围仅包含已授权的原五个文件、精确 frozen product marker、受信调用方提供授权 scope 的静态 fresh-stage 构建/finalization。原独立全量 inventory、五角色、跨位置 identity、verifier final path/hash 与只读 JS loader 证据，以及 revision01 的 no-clobber 测试，按固定摘要复用。新目录产物的完整构建属于作者证据，不能表述为本轮独立全量复验。

预期 scope 摘要必须来自已授权调用方或控制面；对任意输入自行计算摘要再传入，不构成授权。本工具是本地施工工具，schema/owner 校验也不是认证签名。

仍未覆盖实际安装、原生产品启动、registry/PATH、用户数据迁移、升级/回滚/卸载、C57、维护门、事务 journal 或掉电恢复。先前 file-symlink 权限 SKIP 保留，不能由 junction/hardlink PASS 替代。Go consumer 兼容性仍是源码合同检查，JS loader 是先前真实只读执行。本轮没有修改共享状态、修复 Git 历史对象或重试清理。

旧封卷和失败记录保持原摘要；scratch 按 Root 要求保留。详细命令、输出和输入引用见 `EVIDENCE-MANIFEST.json`。源码/静态独立审查关卡已满足，任何整合与共享 checkpoint 更新由 Root 单独负责。
