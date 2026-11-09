# Mu M0 V3 independent review

**REQUEST_CHANGES**. 最终冻结patch `01f3691bc17b846282da82643ba913272eddfd37e937bda65b95e0bffeac1e8c`，base `7ec619a16a932ae02daa7c2e6132d266528a1da8`。

既有32/32、默认Agent40/40、worker2/2、targeted tsgo通过。新增相邻行为共5项：3个产品失败、2项通过，对应2个P1。另有初始freeze漂移和1次独审测试假设错误，原始记录完整保留。

## M0-V3-R1 P1 Pending-finish and after-turn checkpoints lose active model and replacement context

packages/agent/src/agent.ts:423

prepareRequest returns selected-runtime-model plus compacted-context. Both no-pause controls call that model twice with compacted context. JSON pause/restore during response or finish produces second call to constructor model synthetic with original-context instead. Response-pause also passes original-context to the pending finish callback.

A resumed request can use the wrong model and restore context removed or replaced by preparation, despite callback counts being correct. Public PrepareRequest permits replacement runtime context/model; the uninterrupted controls prove its current behavior.

Suggested repair: Persist active model, reasoning, exact runtime context and stable tool binding through every continuation phase, including pendingFinish and afterTurn. Restore the pending callback/next-turn transition from that runtime snapshot while preserving the public transcript separately.

## M0-V3-R2 P1 Resuming a tool batch re-enables a tool excluded from that request

packages/agent/src/agent.ts:469

Initial registry contains allowed and excluded; prepareRequest restricts context.tools to allowed. Original assistant calls allowed then excluded. No-pause control executes only allowed and produces isError=true for excluded. Pausing after allowed, serializing to JSON and restoring executes excluded too, giving effects=[allowed,excluded] and isError=false.

Pause/restore broadens the executable tool set for a previously issued batch and can run an effect that the original request would reject.

Suggested repair: Bind each pending tool batch to its original effective tool declarations and resolvable implementations, restore only that set, and fail closed if the exact binding is unavailable. Do not substitute the full current Agent registry.

9文件与全部2127个独立编译输入无漂移；V2冻结字节保留。WIP未提交、未安装。真实模型/工具/网络调用0，D写入0，正式验收0增量。
