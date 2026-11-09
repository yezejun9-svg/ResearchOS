本次独立复核接受的范围是：`HYBRID_REAL_PROVIDER_SYNTHETIC_PROJECT` 中一次真实本地模型调用的证据闭环。冻结 manifest 与 16 个成员一致，53 项最终只读检查通过；审查未调用模型，也未创建正式验收或变更运行资格。

请求、SSE、effect fact、worker stdout/stderr/result 与 Windows 原生观察能相互对应。保留数据库中 v1 没有 Run 或 effect；v2 只有一次 Run，effect 历史为 PREPARED → STARTED → CONFIRMED，无 UNKNOWN 和重试。输出为 `I received this task.`，用量 1402 input / 6 output tokens。0.01 USD 是保留的成本上界，实际费用为 null。

🔴 完整历史失败审计未通过：两次 v1 BLOCKED 仅有摘要，作者确认未保存原始启动命令、退出码和 stdout/stderr。只读数据库能支持“派发前失败”，不能补出原始命令输出；不得把后续复跑当成原始证据。

🟡 `apps/control` 启动与 health200 只有作者摘要。成功调用来自改写后的 W14 harness，经真实生产 coordinator、broker 和 Windows runner；不能据此声明 standalone apps/control、CLI 或 Desktop 正常会话链路通过。model digest 在原包中也只有声明，没有与该次调用绑定的模型存储凭据。

RuntimeRegistration 仍是 REGISTERED，qualification_ids 为空，两个保留数据库都没有 AcceptanceReceipt。正式用例与父任务接受数均增加 0。默认配置与 Canon 未改动只能从隔离路径推断，缺少前后快照，不能作为已验证事实。

审查器首轮有两个自身断言错误，原记录完整保留：数据库 dispatch 终态应为 OBSERVED，observation 中 profile_hash 应对 profile_ref 求哈希。根据生产源码修正后 53/53 通过。这两项不是产品失败，也不抵消两次原始 v1 失败。

补充复核数据来自只读 SQLite 与原隔离工作树，标记为原冻结包之外的独立补充材料。最终结论见 independent-review.json；receipt_manifest.json 封存本审查目录成员。
