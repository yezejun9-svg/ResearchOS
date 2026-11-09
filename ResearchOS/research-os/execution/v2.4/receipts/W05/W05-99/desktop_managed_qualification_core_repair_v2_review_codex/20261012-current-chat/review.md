# Desktop managed qualification Core v2 独立复审

结论：**ACCEPTED_SOURCE_AND_FIXTURE_ONLY**。候选 `0df32ed4eeeba3b9714477ccfae759ef90b633ee` 关闭原两处 P1；本次范围未发现新的阻断问题。

- **DMQ-P1-001 已关闭。** 退出失败和 release abort 保留先前、活动资格及持久资格封锁。原反例通过；真实 V2 `session.send` 在拒绝 SHUTDOWN、abort、Scan 后均被封锁。
- **DMQ-P1-002 已关闭。** 构造器在返回前同步恢复持久封锁，`ManagedStartupHold` 同样关闭入口；观察/恢复失败关闭入口。普通无资格启动及正常 abort 保持原有开放行为。独立补充验证构造失败释放自主取得的锁，已有回归验证 borrowed lease 归还。

独立测试合计 **49 个顶层、109 个子用例 PASS，0 FAIL、0 SKIP**：原 overlay 3/0；domain 35/86；host 7/12；verifier 2/9；新增 reviewer 2/2。新增测试覆盖 Run 已终态但原 MODEL effect 仍 UNKNOWN，分别叠加及不叠加 ManagedStartupHold，使用真实 session.send 事务检查入口封锁与证据不变。原 overlay 字节不变。

82 项来源核验通过：14 个累计来源文件、62 份作者证据、4 份冻结输入、2 个实际二进制。候选工作树审查后干净，来源及二进制哈希匹配；实际 Go build metadata 指向该候选且 modified=false。

实际 control 生命周期、host synthetic qualification、实际 verifier 均已独立重跑。它们仍是不同证据层，不代表真实 Desktop + control + Ollama 完整流程已完成。真实模型调用和正式父任务接受增量均为 0。**UNKNOWN ledger 拒绝退出仍 OPEN，生产发布仍 NOT_PUBLISH_READY。**

原始命令、环境、退出码和输出见 `*.invocation.json`、`*.stdout`、`*.summary.json`；机器可读结论见 `independent-review.json`。保留旧版失败及原审查包。
