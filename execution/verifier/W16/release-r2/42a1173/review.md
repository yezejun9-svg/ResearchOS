# R2 第一段独立审阅

结论：`PASS_BOUNDED_FIXTURE_SOURCE_INTEGRATION`。接受对象为源码 `7be95f139caaca6233b2c137b5a0be89c20f9d3c`，证据提交 `d6deeaac01d0bc99c71b9aaaa328ef6dff6274a8`。本目录名保留初始复审锚点 `42a1173`，不表示该旧源码已单独最终接受。当前限定范围内没有未关闭的阻塞发现。

本次由独立审阅者只读检查源码、原始 Go JSON 回执并重算哈希与测试清单；没有重新运行程序、测试、Windows 服务、S2 对抗审查或旧清理动作，没有读取真实产品数据及 LIVE 受保护正文。作者 worktree 在证据冻结后为 clean；证据提交相对最终源码仅新增回执及索引。

## 接受范围与证据

| 范围 | 已核对行为 | 证据边界 |
| --- | --- | --- |
| HTTP 到 receiver | START_CANARY 仅登记 PREPARED，候选仍 EVALUATING；独立 release_host.exe 读取自身预封存 admission，再核对 current domain evidence | 同机、同用户的临时 fixture；不证明独立 SCM 身份 |
| 当前准入 | 当前 principal revoked/role/grant、remote authority intersection、作者/回归 verifier/release actor root 分离；候选状态、exact acceptance、operation hash/epoch、current policy/conflicts/holdout、deadline | 完整校验位于 Prepare/Switch callback 中，耗时备份恢复前后均执行，Drain 再复查；不是生产并发写入 fence |
| 真实备份 | authority SQLite 的事务快照、AES-GCM 加密、manifest MAC、schema/migration/inventory 校验、隔离目录恢复 | 恢复依赖原 CanaryStore；不是 marker 备份，不宣称跨机或 LIVE 恢复资格 |
| 受保护引用 | 所有历史非 PROJECT Artifact 版本逐一核对 descriptor、Describe/Read、长度与 hash；禁止 ps1 host copy；独立 holdout verifier 当前权限再验 | 仅 VERIFIER_ONLY/FIXTURE/CanaryStore；未将私有正文复制到 public store 或可移植导出 |
| 进程与日志 | journal append/flush、原子 descriptor、exclusive supervisor lock、epoch/admission 绑定、PID/creation time/image 检查；真实串行 fixture child 切换与 last-known-good 回退、失败 digest 冻结 | 进程存活观测不等于真实 control 健康；真实 data-root 排空及生命周期接线不在本次范围 |
| 不确定窗口与投影 | STARTING/DRAINED/SWITCHED 等阶段先持久化；不确定启动不自动重发；raw receipt 在投影前落盘；OBSERVED 到 PROJECTED 与候选/slot 更新在同一 DB transaction；已投影 ACK 重试不重新切换 | 未模拟所有进程崩溃、磁盘故障和中间 ACK 丢失窗口；源层检查与现有定向测试共同支撑限定结论 |
| 私有收益版本 | 新增 private-r2-fixture-v1 的客观 multiply 样本收益；旧 private-c20-fixture-v1 的 add 规则与原语义保留 | fixture 机制收益；不代表真实业务收益或正式 C20 接受 |

## 发现及关闭依据

1. `R2-CURRENT-AUTHORITY`，原源码 `63281dc` 为 NEEDS_FIX。receiver 原先未检查 regression AcceptanceReceipt verifier 与 release principal 当前 revoked/roles/grants，顶部 transaction 结束后的 callback 也未完整复核候选与策略。`42a1173` 新增 current principal/actors/admission 检查；在备份恢复后和 Drain 再检查。三个不同身份分别于 PREPARED 后撤销，独立子进程均拒绝，operation 保持 PREPARED；公开 FREEZE 后 callback/receiver 拒绝，journal 保持 STABLE。源层关闭，14 项组回执支撑。
2. `R2-CURRENT-EXPIRY`，`42a1173` 仍为 NEEDS_FIX。SwitchFixture 的原 deadline 检查早于耗时备份验证，后续完整 current admission 未复查有效期。`7be95f1` 在 current admission 入口拒绝过期，因此覆盖恢复后的 callback 及 Drain。专项测试断言明确 expiry 错误、operation PREPARED、journal STABLE，并保留实际 HTTP→独立进程→receipt→projection 正例。源层与专项回执关闭。该负例直接构造过期 admission，不声称实际等待备份跨越 deadline 的时间故障注入。

## 原始回执复算

| 源码 | 回执目录 | 重算结果 | stdout SHA-256 |
| --- | --- | --- | --- |
| 63281dc | 5cf6ea30-fc5a-4209-b8e2-e9c9e8469bf5 | 历史 13 项 PASS，0 FAIL；不覆盖后续修复 | 5b5b50759b6bc9418558530e923db5b598964baa24232da55d17ccc5a0cad964 |
| 42a1173 | 2e8ff7e2-dad4-481a-80c1-f862b62e94d6 | 14 项 PASS，0 FAIL；有效期缺口由下一版本关闭 | 844d94fb39f3d8bc10cd928e3e4ca78edcb541781bfc46c68d1da0e4a20cde07 |
| 7be95f1 | 0f86acba-975c-4a73-9e76-26658b34f808 | 1 项受影响测试 PASS，0 FAIL | a551e47d5aade64509abbf34a4f7fba1d90e4ed0ed18d71d41d0f26a2e7a3d90 |

所有 stderr 均为空并匹配声明 hash。14 项组中的 release_host package 为 `[no test files]`；实际 host build/exec 由 HTTP integration test 内部执行和断言。最终源码相对 42a1173 仅改变 3 行 expiry guard 及其 17 行测试；未将旧 14 项组描述成在最终源码上全部重跑。源码清单、报告/索引 hash、原始事件与测试名一致性见 `independent-recomputation.json`。

0019 schema 已有独立 PASS_SCHEMA_ONLY；本次不重新审阅或执行该 schema 的测试，作者组合回执内包含该原选择器不改变这一边界。

## 尚未接受

真实 control 停领取/阻止新 effect/worker checkpoint 与排空、durable COMMIT_EXIT、真实 data-root lock 接力、独立 Windows SCM/ACL 身份、真实 canary 周期及连续 6 小时观测、LIVE promotion、生产受保护 verifier 隔离、W16/C20/A16 正式接受均不由本报告证明。现有 fixture Drain 是 idle/current-evidence 观察，不能用于宣称生产原子停机。原 S2 停止状态及旧验证结论不受本报告改变。
