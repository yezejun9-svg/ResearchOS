# 原会话模型资格独立复核

**APPROVE_OBSERVED_LIVE_RUNTIME_QUALIFICATION_ONLY**，P1=0、P2=0。

CP453 在确认前绑定请求 `f04497200c9825ee55142fbb45a6c21d`，17 字段及 canonical hash 一致。正常 GUI 的一次确认在有效期内消费该请求，唯一绑定 Run `58293e8f129a4dd00be67e35019004fc`、epoch 1。PREPARE 前后均无 dispatch/effect；确认后原 Run 为 SETTLED，dispatch 为 OBSERVED，children_stopped/queue_empty 为 true。

证据支持真实 **1 MODEL / 0 TOOL**：同一个 effect key 具有 PREPARED→STARTED→CONFIRMED 三阶段，模型传输记录为真实、响应 HTTP 200；封存输出 7773 字节重新计算 hash 匹配，声明 model_calls=1、tool_calls=0。三条阶段记录不能算成三次调用。费用账本保持 UNKNOWN/null，未把未知金额当零。

Acceptance `3026a505dd3ce146de282d5cec53301f` 为 LIVE / DETERMINISTIC_SERVICE / PASS。另核验 1197 字节服务检查 Artifact 的原始 hash，以及 Run/Task/epoch/contract/output 绑定；检查报告明确只验证有限 Mu turn、dispatch 和 effects，不证明语义修复正确。

已亲自查看 `06-qualified-desktop.png`：原请求一致，界面显示确认结束及最近复核的用途授权。原 Session 的旧 core_build_id 是保留的历史元数据，不作为此次新包启动身份。该结论基于截图时点，不声称后续配置变化后用途仍有效。

以下仍为 **NOT_OBSERVED**：private management stdout frames、native verifier stderr、native verifier numeric process wait。Run exit_code=0 和服务 check exit_code=0 均不替代这三项。

本复核只通过 URI mode=ro、query_only、只读事务核验原请求和封存 Artifact，没有操作 GUI/API/model、没有写产品 DB 或 Canon。Root 后续正常创建 coding 配置属于另一条授权动作，不按整库漂移否定本次冻结证据。

范围仅为实际原会话本地模型运行资格；不替代工具执行、文件修复正确性、W05 formal 或全部 22/42 正式接受。formal_increment=0。
