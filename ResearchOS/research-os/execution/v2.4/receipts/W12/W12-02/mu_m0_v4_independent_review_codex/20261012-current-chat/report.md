# Mu M0 V4 independent review

结论：REQUEST_CHANGES，2 个 P1、1 个 P2。V3 原反例已关闭；新增边界反例仍需修复。

- **M0-V4-R1 P1** — Checkpoint messages and queue payloads lack the promised typed allowlist。位置 packages/agent/src/agent.ts:237。An undeclared extensionState object containing a synthetic refresh token survives export verbatim. restore accepts an invalid thinkingLevel, user content=42, undeclared role and queued message role=42/content=null. No real credential was used.
  建议：Implement one versioned, recursively typed checkpoint DTO with explicit extension data registration; validate all transcript/runtime/prepared/pending/queue locations plus enums before export/restore. Preserve valid SDK custom messages using trusted schemas, and reject undeclared necessary data rather than silently stripping it.

- **M0-V4-R2 P1** — Model identity is not revalidated between restore and actual resume dispatch。位置 packages/agent/src/agent.ts:1138。Changing the registered selected model baseUrl before restore is rejected, but making the identical change after successful restore permits a mock provider dispatch with the changed URL. restore itself has zero dispatches.
  建议：Retain the immutable selected model binding; resolve/verify it at resume and immediately before each restored-flow provider dispatch, including after preparation hooks. Freeze or copy trusted descriptors as appropriate; never reconstruct secrets/headers from checkpoint data.

- **M0-V4-R3 P2** — Prepared request rejects a legitimate tool selected from pauseToolRegistry。位置 packages/agent/src/agent.ts:823。A tool registered only in pauseToolRegistry is selected by prepareRequest. The prepared-request checkpoint exports successfully with root toolNames=[] and runtime toolNames=[registered_only], but restore throws Agent pause request continuation is invalid. The corrected no-pause control executes that tool exactly once.
  建议：Validate continuation against the original effective runtime subset and trusted full registry rather than against only public state.tools. Keep exact signature/version verification and duplicate/unknown rejection.

冻结 9 个源码文件、9 个作者 bundle 和 2128 个作者输入匹配；独立编译 2130 个输入。候选 41/41、原 agent 40/40、worker 2/2、定向类型检查通过。新增 5 项边界测试 1 PASS / 4 FAIL；通过项含 17 种拒绝校验。最小对照中一次错误的 harness 假设已单独纠正，失败原件保留，不计入 Source finding。

全部工作在 C 独审目录，D 仅只读依赖与 scope。Source/Root/Canon/installed SDK 未修改。真实模型、外部工具、网络、SQLite、真实凭据均为 0；正式验收增量 0，父任务不接受。

下一次修复请遵循 state-contract-v4-addendum.md；不能继续靠字段 denylist 或单例布尔分支补洞。
