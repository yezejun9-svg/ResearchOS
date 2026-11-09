# Mu M0 V2 independent review

Verdict: **REQUEST_CHANGES**. Frozen uncommitted WIP patch `71cfeda5c1e6c9f5217e32cf2d7cc1f25bcce9a8d2a6d7b6a75e1dda77883347` on `7ec619a16a932ae02daa7c2e6132d266528a1da8`.

原21例、默认Agent40例、worker2例通过；新增5例为2通过、3失败。targeted tsgo exit0。输入与候选9文件前后哈希一致。

## M0-V2-R1 P1 Already-paused custom message corrupts unfinished tool batch

packages/coding-agent/src/core/agent-session.ts:2043

After pause: pendingCustom=0; transcript system/custom/assistant/toolResult/custom. Resume: Resumable tool batch has unexpected trailing message; effects=[one], provider fixture calls=1.

Why: isStreaming is false after cooperative pause, so triggerTurn:false falls through to _appendCustomMessage even though the assistant tool batch is incomplete.

Suggested repair: Treat paused unfinished turns as deferred message ingestion boundaries. Snapshot raw new messages and flush only after full batch settlement. Add both same-instance and checkpoint-restored arrival coverage.

## M0-V2-R2 P1 Pause during prepareNextTurn repeats preparation on restore

packages/agent/src/agent-loop.ts:313

Pause requested while awaited prepareNextTurn is gated. It finishes once; next steering poll throws pause. Snapshot retains afterTurn. Restore/resume invokes preparation again: prepares=2, model fixture calls=2.

Why: Continuation only distinguishes tools and afterTurn. The returned preparation state is local and no prepared-next-request phase is committed before the later pause fence.

Suggested repair: Persist a completed preparation phase and its context/model/thinking/message outputs, with queue consumption position. Resume it without reexecuting compaction or extension preparation.

## M0-V2-R3 P1 Pause during ordinary assistant response loses finishTurn and continuation decision

packages/agent/src/agent-loop.ts:415

Pause while first fixture response is in flight, then settle ordinary assistant with no tools. Resume finishes immediately: finishTurn=0, model fixture calls=1. Default control requires finishTurn=2 and calls=2.

Why: The new pre-finish fence interrupts after message_end; a non-tool assistant clears continuation, and resumePaused returns for trailing assistant without queued messages.

Suggested repair: Record a pending-finish phase for every assistant response, including no-tool responses, before honoring pause. Persist and resume its finish decision exactly once.

仅Source/fixture独审；V2未提交、未安装，不产生任何产品/CLI/WindowsDesktop/phone正式验收。所有22当前义务仍OPEN，formal保持0/42。
