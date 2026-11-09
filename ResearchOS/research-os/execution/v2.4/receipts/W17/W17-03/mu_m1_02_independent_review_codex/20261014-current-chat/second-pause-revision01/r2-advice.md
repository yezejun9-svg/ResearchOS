# M1-02-R2 最小修复建议

独立审查结论保持 **NEEDS_CHANGES**。源码候选 `36b2634bfebe6201a14b7661f2dce32b7f1a5098` 的普通两轮暂停恢复通过，不能覆盖跨周期心跳的原生失败。本文件仅提供原作者下一轮修订建议，不修改源码、不签发接受；正式验收增量 0。

依据是同目录冻结 `report.md`（SHA-256 `71399c37bf175148c1ba8dc16cf83b8f41ffdae46e14781aa97cfce0b5e64713`）及 `evidence-manifest.json`（SHA-256 `91b8abb4112916426c0aefe095815c29bcaa35a1f63f44c09278c8f75b1f23a6`），本次读取已复核两项哈希。R2 实测在第二轮 PAUSE 返回 200 后将 epoch2 模型响应保持在途 17 秒，周期 heartbeat 因空 purpose 走通用门禁，随后 Bridge 被取消、dispatch UNKNOWN、pause intent RECONCILING。完整 successor 事务回滚的独立原生故障注入已经通过，不能把该通过与 R2 失败相互抵消。

## 最小源码范围

预期只修改既有 exact9 内两项文件：

- `internal/domain/runtime_coordinator_windows.go`：周期 heartbeat 调用显式传入现有暂停维护 purpose，并在每次调用时复核精确当前暂停身份与阶段。复用已有专用门禁及身份绑定，不复制另一套授权规则。无当前匹配暂停时保持原有普通运行语义；不以 Task BLOCKED 本身、内存旧标记或历史 activation 作为授予暂停维护权限的依据。
- `internal/host/runtime_pause_windows_test.go`：补齐下述原生验证。若实现发现必须修改其他文件，先记录具体缺口，由 Root 明确调整修订范围；本建议不扩大 exact9。

周期 heartbeat、同步 pauseCheckpoint heartbeat 应采用一致的当前暂停维护授权。必须保留 Owner、Goal、lease、manifest、session、queue、Run/attempt/epoch、activation 和暂停 intent 阶段的现有校验。检查需反映每次心跳时的当前权威状态，不能在进入循环时缓存一次授权并永久沿用。

通用 dispatch gate 对任意 BLOCKED 仍须严格拒绝；普通执行、启动、新 effect、新 key、历史 epoch/activation 不获得暂停维护例外。维护 purpose 只允许已有协议所定义的收尾与检查点进度，不得使暂停后的新工作获得执行权限。取消或撤销后的门禁失败仍触发终止；不得吞掉失败、无条件重试或自动恢复运行。

## 必须补齐的原生验证

1. **第二轮 model-in-flight 跨心跳**：同一 Run 完成第一轮 PAUSE/RESUME，epoch2 模型响应在途时通过普通 HTTP 请求第二次 PAUSE。保持在途超过未改动的 15 秒周期，记录实际等待与心跳进度，释放响应后必须得到合法 sealed/confirmed checkpoint，再恢复至 epoch3。不得仅以 HTTP 200 或 Task BLOCKED 判通过；确认 Bridge 没有因维护心跳被取消，队列各一次消费，最终结算和各 epoch 的预算 RESERVE/RELEASE 绑定保持正确。
2. **第二轮 tool-in-flight 跨心跳**：独立定位到 epoch2 的真实 Host 工具在途阶段，再发第二次 PAUSE，并保持工具在途跨过同一真实心跳周期。必须记录 epoch、请求与工具事件，防止把第一轮工具用例当第二轮证据。合法在途工具完成及实际发布仍受现有 effect/authority 校验，随后 checkpoint 确认、恢复与最终消费/预算验证通过；不得伪造工具成功或改短心跳间隔。
3. **取消负例**：在第二轮暂停等待跨心跳的同一原生流程中，通过正常取消入口撤销继续执行条件，证明维护 purpose 不阻止取消传播，Bridge/运行按协议终止，没有合法继任 activation、自动恢复、排队命令重放或取消后新工具发布。保存规范 DB 与 Bridge 状态，不能只断言客户端超时。
4. **撤销负例**：在第二轮等待中撤销当前 Owner 权限，且保留其余绑定，以隔离授权原因；下一次维护检查应拒绝继续。另覆盖 Goal 不再允许继续或 lease 已失效的当前状态，证明 purpose 不绕过原有门禁。原生注入或 fixture 应明确标记，fixture 不冒充原生证据；负例均需断言无继任启动、无自动恢复和无越权副作用。

复跑已通过的普通暂停/恢复/取消、prepared-lease recovery、第二轮正常路径及必要的通用 BLOCKED/历史 activation 拒绝回归；不调整正式阈值。作者须冻结新 commit/tree、精确 diff、完整命令/环境/数字 exit、canonical DB/Bridge 输出及哈希，交给另一身份独立复核。只有新候选的新鲜验证才能关闭 R2。

## 失败历史

本轮独立审查维持 5 次命令 / 2 次非零：03 是 R2 原生失败（同命令内完整 successor rollback 通过）；04 是审查夹具缺必填字段，被存储 CHECK 正确拒绝，修正后05通过。作者 23 次为 11 PASS / 11 FAIL / 1 SKIP；CP483 原生失败下限3已映射作者02–04，不重复累加。早期作者18/7与独立5/2保持原值。追加修订与验证记录，不改写现有报告、manifest、失败或计数。
