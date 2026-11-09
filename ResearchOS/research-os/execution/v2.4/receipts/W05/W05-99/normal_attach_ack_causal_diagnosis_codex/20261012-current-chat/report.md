# retry06 SESSION_CHANGED 只读诊断

**结论：实际响应链在隔离环境完整复现。根因是 Core 已完成接管却返回 ACK，Main 正确保留 ACK 屏障；仅修改 Desktop 的三个文件来清除屏障不满足既有合同。**

原会话 a09d4435036b2b32a0d7076bfc53fd93，原项目 a7ebcf2a322c6abcf87e043f601ee804。使用已审组合包 Main/IPC、原生 validator 和 Root 保存的真实 result 字节，未访问实际 DB、API、provider 或 Electron。由于未取得 Main 内存 trace，实际 entryBarrier 的判断是由源码、操作次序和离线原字节反例支持的因果推断。

## 证据

- 5 组离线诊断通过；17 个原生 validator 子进程的数值退出码均为 0。原子进程 stdin/stdout/stderr、exit 与每个请求/响应 raw 已封存。
- rev3/epoch2 经真实 validator/reify 两次均为 Number，严格相等；Main generation 不增加。WireNumber 引用不等假设被排除。
- 原 attach ACK → 后续 GET 正常返回 rev3/epoch2 → renderer 可显示当前可写，但 Main 仍保留 rev1/epoch1 和原 command 的 ACK lifetime → AUTHORITY_READ 返回 STALE_RESPONSE、transport 调用 0 → exact Main prepare 抛 SESSION_CHANGED。同 payload 重放仍 ACK；更改 after_sequence 被 COMMAND_PENDING 拒绝。
- 无 pending 的同快照对照可完成 prepare；单独 selection generation 变化也会失败，但不是 ACK 反例的必要条件。
- 当前 schema/validator 已接受 COMPLETED + {snapshot, write_owner_acquired:true}，无需新增公开 schema；这是拟议结果形状验证，不是实际 Core 修复。

完整结果：[results.json](./results.json)、[报告 JSON](./report.json)。所有 response envelope 是按现行合同重建的离线外壳；内含保存的原 result 字节，不能称为原 HTTP 报文。

## 定位与合同

- Core internal/domain/client_protocol.go:1136–1196：同步接管、journal CLIENT_HANDOFF 后 return ack。:731、:748 的历史响应升级分支只针对 session.control；attach 永久重放原 ACK。
- ipc.js:108、195–200、213–218：ACK lifetime 保留并阻止资格 authority read；普通 GET 不清理 ACK，Main 不采用其 CAS tuple。main.js:207–210 将所有 opened 非完成归并为 SESSION_CHANGED。
- React workbench.jsx:404–407、540：直接采用 GET 快照，ACK 后读快照可显示当前可写。
- canonical 22_CLIENT_INTERFACE_DETAILS.md:116 规定 ACK 为持久受理而非完成；:139 要求原子转移之后 CLIENT_HANDOFF **并返回 COMPLETED/AttachResult**，此后才能写。
- CLIENT_HANDOFF 事件确有原 command_id、session、sequence、Core 与 writer 信息，可用于对账，但不能替代合同要求的原命令终态。migration 0002_domain.sql:46 的 idempotency_immutable 明确禁止 UPDATE；SQL23 冻结 command identity。因此本轮不批准 ACK+snapshot 自动解除，也不批准更新原 ACK。

## 建议 sourceForward exact6

沿用既有 c7994ea630534db2b85b1235ce441900 的同步子集设计，并按当前 Main912 文件重绑定。生产范围只有 client_protocol.go 的 attach 授权/同步分支、attach 私有 helper，以及 api/v2.go 的原 scope TTL 默认值；其余四文件为既定原生/HTTP/事务测试。具体路径、旧 SHA、当前 SHA 和边界见 [sourceForward-six-current-binding.json](./sourceForward-six-current-binding.json)。

旧 scope 与当前字节不同的文件：internal/domain/client_protocol.go, internal/api/v2_sessions_test.go。旧行号只能作定位线索；保留当前 session.list、workspace 与 control 测试增量，不能直接套旧文件。

必须保留旧设计的真实行为区分：同 owner 普通续租只改 lease/updated_at，不递增 epoch/revision/watermark；NULL lease 及不同 client 的过期 lease 获取分别核验真实主体、原会话来源、完整历史 Run/Task/effects/permissions/control/queue/fence settlement。不能把现有 return ack 单行替换作为整个 exact6 完成。有效 foreign writer 的异步接管继续明确不支持并保守拒绝。

历史 ACK 永久保留、exact replay 字节不变；无迁移、schema、SDK 或异步终态持久化扩展。Root 可在独立构建审查后通过正常 Desktop 关闭/打开与原会话显式新接管产生新 command 的合法 COMPLETED；此流程不追认原 ACK 完成，不修改旧会话、owner、context 或历史回执。

必要验证：旧真实 ACK 链保留；新合法同步接管直接返回完整 snapshot+write_owner_acquired；same-command replay 不再次写 lease/epoch/event；同 owner 续租与 foreign/null acquisition 区分；身份、CAS、未来 cursor、未 settled 及 rollback 全量不变量；原生 Windows 与 HTTP 路径；旧 ACK/identity 字节、全部历史失败保持。若测试条件需要追加写入路径或改变生产 helper，先回 Root 调整范围。

## 历史与边界

既有 V1 REQUEST_CHANGES、V2 CONDITIONAL_APPROVE_SOURCE_WIP、组合包 APPROVE_PACKAGE_FOR_ROOT_CONTROLLED_ACTIVATION 的原文件哈希均保留在 contract-and-history-refs.json。后两项是原限定范围通过，不追溯擦除，不扩大成实际运行资格。当前发现补充了此前 fixture 未覆盖的真实 Core ACK 成功路径。

Source/Canon/真实 DB 写入、真实 API/provider/model 调用、产品启动、正式验收增量均为 0。本报告不是修复独审。
