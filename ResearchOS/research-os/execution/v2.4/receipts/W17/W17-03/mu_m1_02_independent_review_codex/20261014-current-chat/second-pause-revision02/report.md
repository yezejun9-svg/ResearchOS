# CoreR2 exact2 独立审查

结论：**LIMITED_SOURCE_ACCEPTANCE**。冻结候选内的 M1-02-R2 已解决，本轮未发现需阻止此范围源码接受的问题。接受仅覆盖 exact9 基础上的 exact2 心跳修订；没有合入 Main，没有批准发布或产品正式验收。正式仍为 **0/42，22 个父任务全部 open**。

`internal/domain/runtime_coordinator_windows.go:535` 在已有 dispatchGate 事务内读取当前 run/epoch 的 pause intent，再交给原 pause purpose 门禁。`RunAdmitted:695` 的周期心跳传入 heartbeat-current，15 秒周期未变。当前暂停仍需匹配 task/run/runtime/epoch/dispatch/manifest/process、状态见证、有效 Owner、Goal、session/queue/control，并经过原 lease 与 admission 校验。普通调用没有 purpose，BLOCKED 的严格拒绝仍保留；没有借历史 activation 放宽执行或启动。

## 独立验证

本审查恢复时，前位独立 reviewer 的 01 与 02 均已完成，未发现遗留 go/host/domain 测试进程。已核对原命令、日志哈希及前后 source guards，复用其独立结果；它们不是作者测试。新增 03 与 04 使用独立编号及 attempt-ledger-resume.json，原 attempt-ledger.json 未改写。

- 01：13 个原 domain 顶层用例 PASS，覆盖预算接管、终态释放、四 epoch、重放及既有暂停门禁。
- 02：8 个 Host 原生顶层用例 PASS，含四个撤销子例。第二轮模型与工具分别在途等待 17000ms，heartbeat_at 实际推进；同 Run/attempt 恢复至 epoch3，两个 activation、四条命令及四条消费回执各一次。模型路径实际 Host 工具 1 次；工具路径 2 次，并断言文件确已写入第二轮内容。
- 03：上一轮失败的 17 秒 overlay 逐字节未变，SHA-256 `f2dc0aa0a0b72a1aaac2371a225107656f66bfca7a0afd557f6b0f24dc19a800`。本次实际执行 PASS，PAUSED_CONFIRMED 后恢复到 epoch3。相同命令内的完整 successor rollback 用例亦 PASS：真实首次暂停后，仅向隔离 DB 注入 receipt 有效而 reservation_id 错误的 RELEASE，Scan 明确拒绝，Run/Task/账本、pause intents/receipts、carry、activation、dispatch 前后完全一致。
- 04：16 个独立 purpose 子例和 14 个错误历史 hold 子例全部 PASS。复用上一轮修正后的独立夹具字节，未改候选源码。

四条原生两轮轨迹的最终预算账本另经独立 Python 解码：每轨迹六行，每 epoch 一条 RESERVE 与一条 RELEASE，reservation_id、project/run/request/event/policy、零金额币种和 receipt hash 均精确匹配，时间可解析。原生恢复的四条命令与四条消费回执也再次核对。见 resume-verification.json，包含 89 个输入引用的实际哈希复核。

四类撤销均先跨过第二次暂停的心跳，再撤销当前权限，Bridge 被取消，epoch3 activation 为 0，已消费队列保持 2，Host 工具调用保持 1。CANCEL 是真实 HTTP；Owner 调用真实 Service.RevokePrincipal；Goal 与 lease 使用隔离 canonical DB 合成故障。后两类不能称作完整用户撤销路径。

## 历史与边界

本 revision02 独立测试共 4 次命令、25 个顶层 PASS、0 个非零退出、0 skip。作者 revision02 的 7 次尝试保持 6 PASS/1 编译失败；旧作者 23 次 11 PASS/11 FAIL/1 SKIP、旧 reviewer 5 次/2 FAIL，以及更早作者 18/7、reviewer 5/2 均未改写，不能重置或重复累加。只读诊断中的路径错误单独记录，不混作产品失败。

这里运行了真实 Windows Host、canonical DB、AppContainer、broker 和 verifier，模型为本机 synthetic 回应。未调用外部模型，未操作实际 Desktop、产品数据或私钥，未修改 Main/共享状态。purpose/历史 hold 为 domain fixture；预算及 Goal/lease 为原生前置流程加隔离 DB 故障注入。宽泛 Bridge 兼容、真实模型和正式用例仍需各自证据。本结论不扩大为全部 runtime 或产品通过。

候选 HEAD `8f50cb57ff821554aef17e9a9bd5208935489d50`，tree `361ead86ee812d5e040fe1d2cde2a92297eb639f`，base `36b2634bfebe6201a14b7661f2dce32b7f1a5098`。exact2 为 coordinator 与 Host test。scope SHA-256 `b070cfa31d8336ef9c029d4cb410b214ccf0f30750b1dcbdbbce6a8d6d8c7d64`。最终 guard clean；runtime 资产及 overlay 哈希与冻结输入一致。
