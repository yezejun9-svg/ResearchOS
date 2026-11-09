# 当前 Main24 Source：W09 开发回归交接

执行者：`/root/resume_audit`。状态：`DEVELOPMENT_REGRESSION_PASS_WITH_PRESERVED_SETUP_FAILURE`；正式接受 `NOT_RUN`，formal accepted delta = 0。需独立 Verifier 审查。

当前 HEAD 为 `549ad6924ad43d27bbe533f4ba020ef383a0888f`，保留原有 W09 dirty。依赖完整快照共 581 文件，原始字节保存在 `current-source-snapshot-v2.zip`，清单为 `source-snapshot-v2.json`。执行副本位于 `.local/w09-main24-20261012-src`。结束时逐项检查 Main 和副本都未漂移。本执行者没有修改 Main 产品、ops 或 Canon。

## 实际结果

15 个目标顶层用例全部通过，含子用例共 21 个 pass；原始输出包含 19 条 W09 断言和 22 条 W18 断言，586 个 owned 原始导出均已固定摘要。直接调用原有 `verify_a06` 检查这些实际文件通过；未调用 `verify_native`、`verify_mode` 或 dispatcher。

| 边界 | 原有精确 Go 入口 | 结果 |
| --- | --- | --- |
| A06 权限/修改/移出/删除/撤销/上下文；FTS 故障回退 | TestW09A06HTTPInvalidationAndContext；TestW09A06FTSFallbackAndDuplicatePath | PASS |
| 路径逃逸、根身份替换 | TestW09RootReadRejectsEscape；TestW09RootIdentityRejectsReplacement | PASS，首轮完成 |
| Unicode locator、替换根不泄漏、陈旧正文、旧根迁移撤权 | TestW09UnicodeLocator；TestW09RootReplacementCannotFeedProduct；TestW09TaskInputCannotRematerializeStaleLocalBody；TestW09LegacyRootMigrationRevokesUnidentifiedRoot | PASS |
| 跨项目正文/搜索隔离、撤销根拒绝已封存正文 | TestW0901SameNameFileStaysInsideItsOwnProject；TestW0901RevokedRootCannotServeSealedBodyAgain | PASS |
| 恢复原始封存源、旧凭据失效、备份无明文凭据、受保护内容拒绝 | TestW18RestoreNative；TestW18Boundaries | PASS |
| 恢复源别名冲突、相同字节不同文件身份 | TestW18SourceAliases；TestW18SourceReplacement | PASS |
| 新 handoff 仍要求普通公共备份策略 | TestPreparedHandoffKeepsOrdinaryPublicBackupPolicy | PASS（策略单元断言） |

完整实际 argv、cwd、选中测试、工具摘要、开始/结束时间、环境覆盖和 exit 在 `invocation.json` 与 `attempt-002/invocation.json`。对应 stdout/stderr 与全部断言、文件摘要在 `assertion-map.json`。直接运行使用锁定 Go executable，`-count=1 -json -run` 精确名字正则，没有缓存成功替代。

首轮 exit=1：独立快照遗漏本仓库 Go 依赖，domain 包未编译；两个 adapter 用例已完成。原失败不改写。补齐本地依赖后，新输入向量仅运行尚未执行的 13 个 domain 用例，exit=0，没有重跑两个已成功入口。首版不完整源码快照、stdout/stderr 和 invocation 均保留。

## 影响与边界

`source-delta.json` 对比原 Context：9 项摘要变化（包括已通过 v3 兼容的 profile，因此仍有 8 项产品/测试源码变化），另有 12 个新增 domain Go 文件。主要变化是 schema24/PreparedAbandonment backup handoff、公共策略、恢复协调器及 Service authority 字段。检索、origin、原导出/closure/router 本体仍与旧 pin 一致，因此未重复运行 C19；能否复用旧 C19 须由独立审查判断编译依赖影响。

本次复用已有真实 Go 测试。没有增加一个“撤销根 → 备份 → 恢复 → 搜索”的端到端专用用例；不能把分别通过的撤权与备份测试说成该组合已验证。此回归也没有执行历史版本进程 handoff 或正式模式资格链。

## 正式链仍需的工作

当前 profile 对原 Context 的 source_files 严格验 hash，并要求收录当前 domain/retrieval 全部 Go 文件。本报告不会自动解除该门槛。Root 需要明确且独立审查的新 Source 补验证据合同，或建立完整的新正式链；原 Context、旧 verdict、issuance 不应改写。

若选择完整新正式链，需新的 Root owner/lease/Scope 及当前 Source/Input 向量，不能使用已消费 Scope。授权后由原有 Native producer 产出 exact roster/argv、same-run 原始导出和 tool-run；独立非作者 mode reviewer 绑定该实际 run。Windows 模式还需实际 host/junction witness。再由 dispatcher 消费，原 profile 要求如下 6 路及两个 GLOBAL case manifest：

- `test.retrieval / W09 / W09-G01 / empty`
- `test.retrieval / W09 / W09-G02 / empty`
- `test.research.fixture / W09 / empty / C19`
- `test.retrieval / W09 / empty / C19`
- `test.retrieval / W09 / empty / A06`
- `test.security / W09 / empty / A06`

此处混合 DEVELOPMENT 选择器不等于任何一条 exact Native，不能更名后冒充正式产物。上述正式路径说明不构成执行授权，也未生成额外审批 runner。执行者不能自签正式结果；当前交接后停止写入，交独立 Verifier。
