# B1 RPC rev3 独立安全审查

**BLOCKED**。本次只读冻结的 8 个源码文件，没有修改源码或执行测试/Native/模型。生产 nil qualifier 仍挡住 prompt；下面问题必须在新冻结版本修复，不能以 test02 通过替代源码结论。

审查冻结：product-v1-native-rpc-runtime-author-20261105/rev3-test02-ready。
lease SHA：0226a367b8d0eec25a04c0f22e8f2eba6db9efdd4849ad51c5a98b74d387f2be。
合同 SHA：03de6480cef5c81504addf6366d03652bff3c5b311ca713279c96a4372336d62。
完整 source SHA、stable diagnostic origin、反例及修复建议见 REVIEW.json。

## B1-F1 — high

位置：codex_rpc_windows.go:381-429

After the startup loop, reading stops throughout Ensure and BeforeModelTurn. Buffered()==0 checks only prefetched bytes. Delayed diagnostics, duplicate responses, server requests or a partial frame can already be queued before prompt admission without invalidating the run. The cancel/intent check is also followed by unlocked file creation/fsync before the actual write.

反例：Fake child sends valid id2+thread/started, then a delayed warning or server request while BeforeModelTurn is blocked; callback succeeds and turn/start can be written before the next read observes the error. Cancel after line413 during intent IO also has no final admission recheck.

最小修复：Maintain sticky capture/protocol state during callbacks; synchronize actual-pipe pending-byte/read handoff with a final admission check after durable intent. Serialize cancellation/error/one-use write admission, while cancellation can still close stdin/stop Job if a write blocks. Original arg0 warning ordering is strong but does not replace live protocol fencing.

验证：Registered fake OS-child delayed-warning/request/partial-frame and cancel-during-intent cases must prove no prompt bytes; do not infer zero bytes from missing intent file alone.

## B1-F2 — high

位置：codex_rpc_windows.go:235,262-289,307-316

Capture exists only in bytes.Buffer and is returned at defer; no bounded durable partial capture or terminal receipt is written. Hard stop loses diagnostics already read. A ReadSlice that crosses the 8MiB limit is consumed but discarded before raw.Write, losing that observed line; the ceiling is checked after ingestion.

反例：Host stops while a callback waits after Native warning bytes were received, or the next line crosses captureLimit; no durable record of those already-observed bytes is guaranteed.

最小修复：Use the established restricted run directory for bounded incremental raw capture and phase/partial metadata; sync before barrier/callback and preserve a bounded offending prefix on limit. Enforce ingestion budget at the reader boundary, distinguish partial/complete, fail closed on IO errors. Persist terminal receipt before Wait returns.

验证：Pure/fake capture pressure, write/sync failure, frame overflow and externally stopped fake-host evidence retention; no Native invocation.

## B1-F3 — medium

位置：codex_rpc_protocol.go:90-160,177-221; codex_rpc_windows.go:336,354-375,449-479

json.Valid/encoding/json do not require valid UTF-8 in strings; no utf8.Valid check exists. Frames are not classified as mutually exclusive response/request/notification. A nonnumeric id is treated as absent, and mixed method/result/id envelopes can be accepted by a matching branch.

反例：Valid id2 policy response with invalid UTF-8 in ignored metadata passes after replacement; a string-id frame using method thread/started can be treated as a notification, although it is a request envelope.

最小修复：Reject invalid UTF-8 before JSON decoding; strict envelope classifier must distinguish key absence from wrong id type and reject mixed method/result/error forms, malformed errors and unexpected root keys according to pinned schema.

验证：Invalid UTF-8, noninteger/string/null IDs on notifications, mixed request/response and duplicate keys at all levels are zero-turn failures.

## B1-F4 — high

位置：codex_rpc_protocol.go:39-44

thread/start explicitly sends environments:[], selecting an empty list rather than the reviewed normal local FromThread default. Official thread_processor unwrap_or_else and thread_manager Option resolution retain Some(empty); core collects no environment selections.

反例：The fake server ignores environments and returns a successful response, hiding that the actual Native route has no selected local executor. This does not implement the contract's local execution route.

最小修复：Omit environments for the reviewed normal default-local route, or freeze and review an exact single local FromThread schema. Assert the chosen creation schema in tests and update template hash/seal binding; do not add environment overrides to first turn.

验证：Pinned public DTO/source conformance plus fake child assertion must distinguish absent from explicit empty; real Native validation remains separately authorized.

## B1-F5 — high

位置：codex_rpc_windows.go:262-281,509-551

After the first turn/completed, the deferred drain appends bytes without parsing them. A later error, duplicate completion, wrong-thread event or incomplete frame can remain in a COMPLETED result. Item IDs/lifecycle are not tracked: an uncompleted commandExecution start, empty/missing agent text, duplicate item completion or changed item identity need not prevent success.

反例：Valid turn acknowledgement/start/completed followed by a protocol error or partial JSON retains COMPLETED if raw drain fits; commandExecution started without completed plus turn/completed also passes.

最小修复：Keep terminal success provisional until bounded shutdown/drain validation; retain sticky errors and validate allowed terminal frames. Track exact item IDs/type/lifecycle and validate final assistant payload and tool outcomes; do not allow later turn/completed to erase a prior incomplete/failed tool.

验证：Terminal-tail error/truncation/duplicate cases, missing tool completion, duplicate/mismatched item IDs and malformed assistant text must not return successful completion.

## B1-F6 — medium

位置：codex_rpc_windows.go:497-548,528; codex_rpc_protocol_test.go; codex_rpc_windows_test.go

The RPC path emits CodexEvent.Kind ASSISTANT instead of the shared existing ASSISTANT_MESSAGE and omits NativeID/tool lifecycle projection. Its allowlist rejects normal v2 streaming agent/reasoning delta notifications; official bespoke_event_handling forwards those. The fake stream is authored to the implementation and does not cover pinned Native protocol behavior.

反例：A normal Native agent-message delta fails after prompt consumption. An accepted completed agent message is passed to domain under a different event kind, so the existing assistant-message contract is not preserved.

最小修复：Implement the bounded pinned-v2 notification subset needed by one normal readonly turn, with exact thread/turn/item binding; public summaries only and no private reasoning exposure. Map final assistant/tool events to existing CodexEvent contract. Keep unknown/permission requests failclosed.

验证：Source-derived transcript fixtures including normal deltas, supported user/item lifecycle, command completion, existing event kinds/NativeID; tests must assert DTO semantics, not only callback counts.


## 已确认的正确部分

实际同一 OS pipe 接线、crypto nonce、固定请求图、实际响应身份比较、首 turn 无 override、nil qualifier failclosed、已有 suspended Job/BeforeResume 和无自动重发均已在源码确认。codex_driver_windows.go 相对已 hash 匹配 lease 的 Main 基线，逐行差异只有强制 NativeTransport=CodexExecTransport。未见旧 exec 通过改 descriptor 获得生产资格的路径。

F1 可采用作者提出的单 reader + actual-pipe Peek watchdog，但必须 sticky dirty；callback 时不可有隐藏读者；停止并 join watchdog 后，在 durable intent 之后做最后同步 Peek/buffer/error/cancel 检查和一次性写入准入。任何 API 不确定性阻止 prompt。若 writer 持锁可能阻塞，取消必须仍能关闭 stdin/Job。原始 helper warning 有“初始化前已写入”的更强源码顺序；任意未来字节只能触发后续停止，不能承诺追溯为零 prompt。

F4 官方依据：[thread_processor.rs](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/app-server/src/request_processors/thread_processor.rs#L1553)、[thread_manager.rs](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/core/src/thread_manager.rs#L2348)、[session/mod.rs](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/core/src/session/mod.rs#L686)。Some(empty) 没有进入默认环境分支。

F6 官方依据：[bespoke_event_handling.rs](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/app-server/src/bespoke_event_handling.rs#L1002)：v2 发送 agent/plan/reasoning delta notifications。现有共享 adapter 的 codexEvent 在 codex_driver_windows.go:491 使用 ASSISTANT_MESSAGE 及 NativeID；工具事件使用 TOOL_EVENT。

## 测试与证据边界

test01 原失败已保留，RESULT 为 exit1/stop_proved/no input drift。rev3 修正的 id1 < stderr warning < id2 顺序断言与 fake child 写序一致；这是旧已知诊断，不重复计数。test02 由 Root 的原 f13 运行，本报告未自行运行或断言其最终结果。现有 fake 矩阵验证部分 mismatches，但缺上列 delayed capture/cancel、UTF-8/envelope、耐久故障及真实 v2 transcript 反例。

B2 第二授权 fence、B3 producer 另审；其未完成属于 runtime prerequisites，不掩盖或替代本报告 B1 源码缺陷。任何新修改应保留 rev3/test01/test02，再由 Root 登记新测试。所有 formal/product/Native/model 增量为 0，D 写入为 0。

一次 git diff 读取尝试因文件系统 Permission denied 未完成；没有重试或提权。随后对准确 Main 文件直接只读 hash/逐行比较，三个既有基线 SHA 均与 lease 一致，因此不以不可用 git 输出作为证据。

