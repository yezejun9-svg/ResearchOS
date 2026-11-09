## Review Summary

**Verdict:** APPROVE — SOURCE PREPARATION ONLY

**Overview:** v7 的两个窄修关闭了 v6 终态 Session 目标关联与完整 Artifact 版本关联缺口。本轮只证明已封存源码可供 Root 准备后续真实输入，未批准执行、整合、实际资格或正式接受。

### Critical Issues

无已确认的 Critical 问题。

### Important Issues

本轮两项指定缺口已关闭，没有新增已确认的 Important 请求。

### Suggestions

保留现有阶段分离与有限 scope。后续独审需使用真实 Root producer、同 PID Job、实际 CLI/SDK 原始 ToolIO 与 DB/账本结果；不要以本报告替代运行资格。

### What's Done Well

- [mu_sdk_trial.v7.final.proposed.py:244] 必须有非空真实 execution Goal/Task/Run；末 Session goal_id 与 active_run_id 精确匹配该 Goal/Run，保留原 project/session/protocol/build/cursor/writer 与 saved_context/postimage 守卫。
- [同文件:350] 同 Run 的 AVAILABLE Artifact 保留完整四字段 EntityRef；entity_type、非布尔整数 revision 和 sha256 形式严格校验，相同 id 的矛盾引用拒绝。
- [同文件:801] 原 stream 引用精确绑定实际项目 domain_versions 与当前 Artifact 的版本/hash，保留 Task/Run 原输出 ID 向量一致；[同文件:1411] 从原 command_once invocation 的 consumed_file_transition/context_evidence 传入同一已验证向量。
- DRAFT admission 与普通新 Goal 执行仍分开。--draft Task/Run/ledger/effects 零条件、真实 new Goal/Task/Run、有效 UNLIMITED ancestry 与 UNKNOWN 原 MODEL 账本未退化。

### Verification Story

- Tests reviewed: yes，阅读作者最终 38 stream +25 graph 控制源码；未运行完整作者 harness。
- Independent verification: 27 个有限纯 AST/内存数据控制全部符合预期。包括完整终态字段的 session.get 正向；foreign/missing Goal/active Run、缺 execution Task、wrong Artifact 类型、bool/float/旧 revision、空/错 hash、矛盾 ref、foreign project，以及历史版本存在但当前 Artifact 不同的拒绝。DRAFT 无终态 Run 分支正向保留。
- Artifact 内存 stub 的历史版本与当前版本分离，以免只用同一字典伪证旧版本拒绝。未执行真实 SQL或打开产品 DB。
- 19 个 Source MF 成员、7 个外部输入 hash/bytes 全部正确；整份 forward/reverse diff 独立再生与双向 byte restore 成立。v6→v7 仅 original_cli_summary_stream、verify_ordinary_goal_graph、main 三个定义变化；37 个其他定义 byte/AST 相同，仅新增 re 标准库 import。
- 原四份 Go 与 v5 CLI producer 的实际字节 pins 保持。复用此前真实 Go producer546/591 对 Goal/active Run 的守卫及原 EntityRef/保存 context 协议证据。
- Build verified: no；Go/CLI/SDK/provider/Node/native/canonical 操作均 0。源码 AST 验证不能声称 Go 编译成功或实际 Job/SDK 生命周期通过。
- Security: Root registration/review/grant/lease/Job、consumed executable/config/discovery bytes、完整 argv/env/cwd、pre-Popen、absolute deadline、first nonzero cause 与 isolated data/vault/reparse 守卫均在本轮未改的定义中。
- Performance: JSONL/raw 限额、3 requests、8192 requested tokens 与300s scope 未扩；实际费用/token/internal attempts 仍未知，不伪造0或可信上界。
- Readability/architecture: 原验证引用沿 invocation→DB graph 传递，修复了此前压成 ID 后丢失信息的接口；使用已有 object_by_ref/exact_ref，无新 public API 或 side effects。

SDK-V6-R01 与 SDK-V6-R02 均 CLOSED_SOURCE_ONLY。真实 Root producer/current Main adoption+binary pins、原同 PID Job/阶段 grant、bootstrap/provider0 原事实、qualification/ordinary SDK 运行与独立资格均 OPEN。Source acceptance 与 formal case 增量 0；新 metadata failure0；旧654/656/657及其它历史失败不重计、不清零。
