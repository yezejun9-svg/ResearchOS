# ADR-002: W04 决定历史与提前实现的基础能力

状态：实施决定；W04 独立验收仍需实际证据。

C03 使用“决定 D revision 2”描述变更，而冻结 schema 的 `DecisionReceipt.revision` 固定为 1，回执不可变。因此第二版决定采用新的回执 ID、`revision=1` 和 `supersedes_id`，由同一事务替换 `ProjectState.current_decision_refs`。证据分别记录决定谱系的第二代、两个实际 VersionRef 与替换事件；不修改同一个回执，不修改冻结 schema 或验收断言。

W04 最终负责 C03、C04、A01，不能用阶段子门替代这些完整用例。为此提前实现后续阶段会复用的三项基础能力：

- ChangeProposal 的独立接受检查：由不同主体真正复算冻结输入、检查和产物，保存不可变 AcceptanceReceipt；应用变更时在事务内重新校验，不能接受客户端自报 PASS 或夹具预置的通过结果。
- ADVISORY/SHADOW 决定记录、显式 Conflict 和整合 Task，以及决定谱系唯一当前引用；不授予模型自动采用资格。
- 持久事件去重、连续序号与缺号等待/补取，使重复、乱序投递经过真实消费者。复用既有 outbox，不建立另一调度器。

`ImpactReviewRequest.semantic_review_run_id` 必须引用真实 Run。W04 在创建提案的事务内计算确定性的 ImpactLink 闭包；可选语义审查等待真实 Run，不能伪造 Run 或放宽请求 schema。语义审查只能补充影响候选，不能减少确定性的影响集合。

C03 中无关 T2 继续使用有效上下文并执行可核验的任务操作，保留实际成功回执；不宣称尚未实现的 Run 结算或 Task ACCEPTED。W06/W11/W12 的完整能力和验收仍由各自阶段负责。

依据：`spec/v2.0/03_DATA_CONTRACTS.md` 第 6 节、`contracts/domain.schema.json`、`contracts/openapi.json`、`06_ACCEPTANCE_TESTS.md` C03/C04，以及独立的两份代码/合同只读分析。冻结规格保持原样。
