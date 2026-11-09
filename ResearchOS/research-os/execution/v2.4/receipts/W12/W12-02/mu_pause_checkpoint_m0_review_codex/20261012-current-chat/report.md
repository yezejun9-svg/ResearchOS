# Mu M0 independent review

Verdict: **REQUEST_CHANGES**. Candidate `7ec619a16a932ae02daa7c2e6132d266528a1da8`; base `8dfebe36508ac0c2508735bb866756dab9283e74`. Source-bound synthetic evidence only.

## M0-R1 P1 Pause during async context preparation still dispatches a new provider request

`packages/agent/src/agent-loop.ts:323`. Provider calls 1 after pause request arrived inside transformContext; expected 0.

Impact: A new provider request may begin after pause even though no in-flight model stream needed settling.

Required change: Fence at the actual streamFunction dispatch after awaited transform, conversion and API-key preparation, while preserving the stopped request context.

## M0-R2 P1 Deferred CustomMessage is flushed into an unfinished tool batch and makes resume fail

`packages/coding-agent/src/core/agent-session.ts:1534`. Public sendCustomMessage(triggerTurn:false) while tool one runs; pause checkpoint pendingCustom=0 with assistant/toolResult/custom; resume sets error Resumable tool batch has unexpected trailing message, effects remain [one]. Unpaused control executes [one,two].

Impact: An ordinary deferred context message prevents the remaining tool from ever running.

Required change: Keep pending custom and bash messages deferred until the whole assistant tool batch has settled; snapshot their full pending state and restore it passively.

## M0-R3 P1 Checkpoint loses whole-batch termination and next-action state

`packages/agent/src/agent-loop.ts:218`. Completed false + remaining true: calls=1 instead of 2. Fully terminated paused batch: calls=2 instead of 1. Both unpaused controls pass.

Impact: Resume either omits required continuation or starts unwanted model work; transcript result IDs alone are insufficient scheduling state.

Required change: Checkpoint full batch aggregate and pending continuation/finish decision. Resume must evaluate original whole batch and respect already-completed terminal decisions, without rerunning completed effects.

## M0-R4 P1 Resumed tool batch skips prepareNextTurn before its next model request

`packages/agent/src/agent-loop.ts:211`. After resumed remaining tool: model calls=2 but prepareNextTurn=0 rather than 1; unpaused control invokes preparation once.

Impact: Required context/model/tool refresh is skipped; AgentSession uses this hook for compaction and prompt/tool-loadout preparation.

Required change: Carry completedTurn into the next runLoop transition so preparation occurs exactly once before the next request, including after restore.

## M0-R5 P2 Restore accepts a consumed watermark beyond the next sequence

`packages/agent/src/agent.ts:519`. lastConsumedSequence=99, nextSequence=1, empty pending queue is accepted.

Impact: Later enqueue/drain can reuse lower sequence numbers and move the consumed watermark backwards, breaking the checkpoint consumption invariant.

Required change: Validate both consumed watermarks are strictly below nextSequence even when pending is empty; retain cross-queue pending uniqueness checks.

## Verification

Original candidate tests 12/12 and worker protocol tests 2/2 independently passed. Additional independent tests: 3 passed, 6 failed across 5 findings; unpaused controls passed. Both raw runs are retained. Source manifests (24 records) matched before/after execution; candidate worktree remains clean. Esbuild input metadata confirms candidate agent/coding-agent source, with existing pi-ai qualification dist. 2123 compiled inputs are hash-bound.

No actual provider/model, production tool, GUI or phone call occurred. No Source, installed SDK, canon or runtime data changed. Formal increment 0; parent acceptance false. Author 40-test regression, types and lint results were inspected as author evidence, not claimed as independent reruns. Initial review UTF-8 decoding failure was corrected with python -X utf8 before execution; failures remain documented.

Reproduce from this directory with `python -X utf8 prepare.py`, pinned Node `compile.mjs`, then pinned Node `--test --test-reporter=tap author-agent.mjs author-session.mjs independent-agent.mjs independent-session.mjs` plus the candidate worker test path. Current failures are expected until candidate source is repaired.
