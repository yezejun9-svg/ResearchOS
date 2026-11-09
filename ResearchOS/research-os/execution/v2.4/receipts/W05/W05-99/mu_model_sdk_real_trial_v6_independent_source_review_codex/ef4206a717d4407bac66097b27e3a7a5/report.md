## Review Summary

**Verdict:** REQUEST CHANGES

**Overview:** v6 修正了原单行 JSONL 假设、DRAFT 引导和 ordinary session.send 新建 Goal 的身份关联。独立静态复核仍确认两处证据关联缺口，源候选需窄修后复审；本轮没有产品、SDK、模型或正式接受。

### Critical Issues

无已确认的 Critical 问题。

### Important Issues

- [mu_sdk_trial.v6.graph.proposed.py:243] 末 Session 未绑定 execution.goal_id 与 execution.run_id。仅改末快照 goal_id 或 active_run_id 的纯数据反例都被接受。按真实 producer546/591的守卫补逐值关联，保留 DRAFT 分支；测试各字段 foreign/missing。
- [mu_sdk_trial.v6.graph.proposed.py:345] AVAILABLE artifact_ref 只投影 id，[同文件:781] DB Artifact 只校 id。错误类型/布尔 revision/错误 hash/不同 DB 版本均被接受。保留完整 EntityRef 并通过现有 object_by_ref/exact_ref 绑定同项目的实际版本；拒绝同 id 的矛盾引用。

### Suggestions

本轮不建议旁支重构。先完成两处数据关联及相应负控。

### What's Done Well

- --draft 使用真实 DRAFT admission snapshot 与成功保存的 context，且实际 DB 读取明确要求 Task/Run/BudgetLedgerEntry/resource_effects 均为零；没有用非 DRAFT 回合冒充 provider0。
- 连续事件 cursor、scope/protocol/build、唯一末 summary、最新 SETTLED RUN_STATE、实际 saved_context/postimage 都保留严格检查，EVENT_RESYNC_REQUIRED 拒绝成功资格。
- ordinary 新 Goal/Task/Run 与原 execution、Task.active_run_id、有效 UNLIMITED 链及 UNKNOWN 原 MODEL 账本进行了关联。
- 46 个成员与 7 个外部输入 hash/bytes 全相等；整份 forward/reverse diff 独立再生与双向 byte restore 成立。30 个原定义 byte/AST 未变，四份 Go 与 CLI producer 原字节保持。

### Verification Story

- Tests reviewed: yes。阅读作者 27+18 个纯数据控制；终态测试省略真实目标字段，Artifact graph 正例仅 id，不能独立证明完整关联。
- Independent verification: 10 个有限纯 AST/data 观测，两个正向基本路径与剩余拒绝缺口均记录在 audit.json。只执行选择的纯数据函数/内存 stub，没有导入候选模块或运行 main。
- Build verified: no；Go/CLI/SDK/provider/Node/native 执行均 0，不能声称编译或运行资格。
- Security checked: 原 Root registration/review/grant/lease/Job、consumed bytes/argv/env、绝对 deadline 与 first_cause 代码未被本轮改动。剩余问题影响证据完整性；真实 Root producer、Job/阶段授权及当前 Main source 采用仍 OPEN。
- Performance: JSONL 65537 records、raw 限额与 finite 3 requests/8192 requested tokens/300s 保留；实际 token、费用及 internal attempts 未知保持 NULL。
- Readability/architecture: 新 helper 明确分开 DRAFT 与普通执行；剩余修复应保留完整原引用，避免 caller 到 graph 的信息丢失。

原 v5 R01 多行处理已修，但终态目标关联仍 REQUEST；R02 DRAFT 源实现 CLOSED_SOURCE_ONLY；R03 新 Goal/Task/Run 与账本修正已实现，完整 Artifact 关联仍 REQUEST。真实 bootstrap/provider0 与 qualification/normal MODEL→TOOL→MODEL 的有效接受尚 NOT_RUN。

本轮唯一新的只读 metadata 失败为 cae826（rg no match，outer1，Python/native NULL），原输入及完整空输出各保存一次。不重计作者既有 001–004/Root653，不修改任何冻结 cut/计数。
