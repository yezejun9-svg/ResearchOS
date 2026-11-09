# Legacy migration fixture independent Source review

**Verdict: REQUEST CHANGES**

本审查仅覆盖冻结 Source、资源指纹、静态调用链及合同映射；authority=NONE，formal_acceptance=false。发现一个会阻止回滚用例到达其断言的 Important 问题。ordinary 历史升级仍然 BLOCKED，Source 审查没有把 restore 子例或 SQL9 组件提升为产品升级接受。

## Critical Issues

未发现新的 Critical 问题。

## Important Issues

- **LEGACY-ROLLBACK-001 — rollback fixture 缺少 Project，提前终止。** candidate-root/internal/domain/client_session_bootstrap_test.go:117 使用 `f := setup(t)`，随后 :119 调用 `useLegacyTranscriptFixture`。固定 T5 的 internal/domain/domain_test.go:141–167 只初始化服务和 principal/token，返回 fixture 时没有赋值 project；项目创建发生在 :205–208 的 `createProject`，而该用例没有调用它。新的 helper legacy_migration_fixture_test.go:121–140 按空的 `f.project` 查 Project/Profile，并在 copied==0 时返回 `historical transcript fixture lacks Project identity`。因此该用例在 bootstrap_test.go:119–120 停止，无法到达 :122 的 Begin、:127 的 fence 安装及 :134 的 rollback。这里是确定的静态前置条件冲突，未伪称已执行失败。**建议修复：**该用例直接用 `legacyTranscriptFixtureDatabase(t)` 创建所需 schema，然后继续原事务/列可见性/回滚断言；或者显式创建 Project 后才调用复制 helper。在新不可变 Source namespace 修正，并重新进行独立审阅；通过后由 Root 在授权集成环境中运行该组件。

## Suggestions

无额外建议；当前应先解除回滚测试的前置条件错误。

## What's Done Well

- 真正的历史 pre-transcript DDL 保留原始字节；独立重算 Git blob 为 `9efc768f8f4cfb6ac31e1f88a78ad095877328af`，20 numbered SQL 均匹配冻结历史对象。
- migration helper 先核对实际 ledger，再在同一事务应用真实 SQL 与记录版本；原 gap 输入作为单独拒绝测试保留，未关闭 production safety gate。
- 两个旧测试文件的 12 个原测试名、126 个原 t 断言调用都保留；9 个无关测试函数体完全相同。ordinary 原 New 正向调用也保持，且作者明确承认它仍被安全门拒绝。

## Verification Story

- Tests reviewed: yes。先读测试及 fixture helper，再沿 setup/contextFixture/New/safety gate 核查；词法检查是独立 Python 静态检查，不是 Go AST 或编译认证。
- Build verified: no。没有运行 Go、gofmt、compiler、native product、SQL 或 model。
- Security checked: yes，静态范围。没有 production Source 修改或弱化迁移/身份/ledger gate；测试资源均为明确的 fixture。没有处理 private credentials。
- 作者 MANIFEST 的 28 members 及 Source refs 去重后共 63 个 pinned refs 均匹配，另 pin 2 个发现问题必需的 setup/contextFixture Source 文件。静态核验总记录 65 条。
- 历史 commit 的 40 selected Git entries 与作者保留的原始 ls-tree 输出一致；独立计算当前资源 Git blob 匹配。没有在此审查重新执行 Git，也没有据此声称 historical installed program、完整编译依赖闭合或 release authority。
- 作者 postseal-tool-io 明确排除于作者 manifest；本审查单独复制并 pin。其 seal_revision 原始工具输出 exit_code=0，输出中的 HANDOFF/MANIFEST refs 在封装时另与实际文件核对。这只证明 Python Source 封装返回，不证明候选 Go/SQL 行为。
- 作者失败 833 的原始命令/失败脚本/输出保留；本独立审查没有新 mechanical failure，旧 826 与 FULL 1261 PASS/25 FAIL/4 SKIP 不 reset。

## Remaining boundary

ordinary 用例使用 populated historical20 时，当前 CheckMigrationSafety 正确返回 MIGRATION_PREBACKUP_REQUIRED。它需要匹配历史程序、真实 backup/isolated restore，以及明确支持的升级路径；本包未完成这些资源。restore、caller rollback 和 frozen SQL9 只能获得各自组件证据，不能让整个原 parent 获得 PASS。Main/T5/T6/T7、canonical 没有被本审查写入；所有新写入限定于此独立审查 namespace 和已归档后移除的自建临时脚本。

