# attach 组合包独立复核

**APPROVE_PACKAGE_FOR_ROOT_CONTROLLED_ACTIVATION**。P1=0、P2=0，无阻塞，无需扩大 Source 评审。

目标包：`C:/Users/yqyyds/.codex/researchos-resource-cache/normal-attach-combined-c465d135-20261014`。58 个成员全部符合封存清单；Main c465d135 与 clean source b955 具有同一 tree 00d44e。三个实际 Go 二进制的 version -m 均为 b955、vcs.modified=false。

6444 个绑定输入重新计算哈希无漂移；digest 8b05bba2053fa3085a6243728b4997ff457951089f60f9817f77be4797a49d8a 同时匹配 descriptor、实际 build ldflags 和新 validator 输出。2225 个引用/编译工作文件哈希核验无差异。6444 是完整绑定输入快照，不冒充实际 compile 输入数量。

14 个 Main/preload 模块、3 个 React 产物、32 个公共 schema/migration 资产与旧批准包和适用源文件相符；Mu 保持 8dfebe36508ac0c2508735bb866756dab9283e74，3 个 runtime 文件哈希不变。复用未变 UI253 和已完成 Core 独立 native 证据。

作者新 validator suite native exit=0、4 个顶层 PASS；复核者实际启动包内 validator 的 5 个合成 packet 均 exit=0 且输出绑定新 digest：attach write 请求、新 COMPLETED、旧 ACK 有效，foreign command 和非法 revision 被拒绝。未启动 Core 或 GUI，未接触真实 DB/API/model。

installer 指向新包绝对 verifier 路径，hash/commit 正确。实时 Get-Acl 为 protected、仅当前 Windows SID 一条 Allow FullControl、无继承 ACE。同一 Windows 用户下的 Agent 不构成隔离 holdout。

审计工具自身两处错误及修正已保留：初始 control 文件名假设错误；generated installer 的 source 表示生成脚本而非复制文件。均未涉及产品修复或包内容变化。

Root 可按既有授权进行原会话受控激活。真实 Desktop 资格 PREPARE/CONFIRM 和产品 Agent 编码仍需运行时证据；formal_increment=0，全部 22/42 正式接受仍开放。本报告不接受任务、不修改 Root Canon。
