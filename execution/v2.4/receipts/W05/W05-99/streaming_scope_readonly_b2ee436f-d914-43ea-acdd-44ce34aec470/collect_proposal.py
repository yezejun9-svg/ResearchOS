"""Read repository source only; emit a proposal, never run product or provider code."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).resolve().parent
SPEC = '.local/worktrees/v24-continuation/spec/v2.4/'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def save(name, value):
    with (OUT / name).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

RANGES = {
 'internal/domain/runtime_model_windows.go': [(47, 140)],
 'internal/domain/runtime_model.go': [(1, 240)],
 'internal/domain/runtime_broker_windows.go': [(150, 245)],
 'internal/domain/runtime_effect_wire_windows.go': [(1, 100)],
 'internal/domain/runtime_model_verification.go': [(525, 595)],
 'internal/domain/runtime_coordinator_windows.go': [(550, 655)],
 'internal/domain/runtime_command_queue_windows.go': [(200, 235), (417, 530)],
 'adapters/runtime/bridge_windows.go': [(20, 65), (330, 445), (540, 655)],
 'adapters/runtime/mu/worker.mjs': [(77, 178), (185, 288), (313, 450)],
 'adapters/runtime/mu/build.mjs': [(1, 96)],
 'internal/domain/runtime_sessions_windows.go': [(157, 305)],
 'internal/domain/client_protocol_journal.go': [(43, 146)],
 'internal/domain/v24_sessions.go': [(113, 146)],
 'internal/domain/client_transcript.go': [(1, 115), (127, 270)],
 'internal/domain/client_protocol_history.go': [(169, 275)],
 'internal/domain/client_command_queue.go': [(75, 135)],
 'apps/cli/cli_stream.go': [(15, 39), (226, 320)],
 'apps/cli/cli_queue_integration_windows_test.go': [(1, 100), (365, 460)],
 'third_party/mu/packages/coding-agent/src/core/agent-session.ts': [(210, 216), (833, 842), (925, 939), (1170, 1183)],
 'third_party/mu/packages/agent/src/agent.ts': [(260, 275), (555, 615)],
 'third_party/mu/packages/agent/src/agent-loop.ts': [(416, 469)],
 'third_party/mu/packages/ai/src/api/openai-completions.ts': [(545, 623)],
 SPEC+'14_CLI_DESKTOP_PRODUCT.md': [(59, 94)],
 SPEC+'17_USER_JOURNEYS_AND_VALUE.md': [(28, 34)],
 SPEC+'22_CLIENT_INTERFACE_DETAILS.md': [(98, 115), (124, 165)],
 SPEC+'contracts/client.protocol.schema.json': [(660, 730), (2777, 2885)],
}
ADDITIONAL = [
 'AGENTS.md', 'execution/project_identity.json', 'execution/toolchains/locked.json',
 'execution/v2.4/component_lock.json', 'third_party/mu.MANIFEST.json', 'third_party/VENDORED_FROM.md',
 'third_party/mu/package-lock.json', 'third_party/mu/packages/coding-agent/package.json',
 'third_party/mu/packages/ai/package.json', 'third_party/mu/packages/agent/package.json',
 'third_party/mu/packages/coding-agent/dist/core/agent-session.js',
 'third_party/mu/packages/agent/dist/agent.js', 'third_party/mu/packages/agent/dist/agent-loop.js',
 'third_party/mu/packages/ai/dist/api/openai-completions.js',
 'apps/cli/cli_stream_test.go', 'adapters/runtime/mu/worker-control.test.mjs',
 'adapters/runtime/bridge_control_windows_test.go',
 'internal/domain/runtime_model_windows_test.go', 'internal/domain/runtime_model_verification_test.go',
 'internal/domain/runtime_command_queue_windows_test.go', 'internal/domain/client_transcript_test.go',
 'internal/domain/client_protocol_history_test.go',
]
paths = list(dict.fromkeys([*RANGES, *ADDITIONAL]))
before = {}
excerpts = []
for rel in paths:
    raw = (ROOT / rel).read_bytes()
    before[rel] = {'sha256': sha(raw), 'bytes': len(raw)}
    if rel in RANGES:
        lines = raw.decode('utf-8-sig').splitlines()
        for start, end in RANGES[rel]:
            excerpts.append({'path': rel, 'source_sha256': sha(raw), 'first_line': start,
                             'last_line': min(end, len(lines)),
                             'lines': [f'{i}: {lines[i-1]}' for i in range(start, min(end, len(lines))+1)]})
identity = json.loads((ROOT / 'execution/project_identity.json').read_bytes())
if identity['project_id'] != 'aede0678-7308-43dc-b9f2-cfe3d90cfdfb':
    raise RuntimeError('wrong project identity')
head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
scope = [
 ('adapters/runtime/mu/worker.mjs', 'Modify', 'MODEL streaming fetch ReadableStream; awaited real agent text events; typed bounded stream messages; abort all stream waiters; retain actual AgentSession/custom-message control.'),
 ('adapters/runtime/bridge_windows.go', 'Modify', 'Strictly discriminate new internal stream envelopes before legacy frame dispatch; initialize/identity gate and single writeMu writer; final settlement additionally requires all stream observations reconciled.'),
 ('adapters/runtime/bridge_stream_windows.go', 'New', 'Internal MODEL_SSE_V1 auxiliary transport and observation-credit state machine; bounded windows, stream binding and cancellation. No effect ACK or queue SEAL authority.'),
 ('internal/domain/runtime_model_windows.go', 'Modify', 'Read live provider SSE incrementally under existing context/header/bounds/credential controls; retain exact complete raw fact and original terminal UNKNOWN rules.'),
 ('internal/domain/runtime_effect_wire_windows.go', 'Modify', 'Streaming final acknowledgement references the exact reconciled full-body receipt and stream digest; legacy gzip full-body path retained. No duplicated 2 MiB body in a 64 KiB frame.'),
 ('internal/domain/runtime_command_queue_windows.go', 'Modify', 'Pump typed stream observations independently from ordered MODEL completion ACK; persist before credit; keep original command receipt and ordered ACK progression.'),
 ('internal/domain/runtime_model_stream.go', 'New', 'Bounded incremental SSE validation, UTF-8 boundary and split-secret quarantine helpers; terminal validation equivalent to completeRuntimeModelSSE.'),
 ('internal/domain/runtime_model_stream_windows.go', 'New', 'Recheck original Run/Task/session/epoch/dispatch/model/manifest/process binding before committing deterministic MESSAGE observations; reconcile final SDK text with original full fact/artifact.'),
 ('internal/domain/runtime_sessions_windows.go', 'Modify', 'Recognize and finalize genuine streamed messages without emitting the entire assistant text again; preserve historical non-streamed artifact projection.'),
 ('internal/domain/client_protocol_journal.go', 'Modify', 'Private runtime MESSAGE append entry point shares schema checks, project/session guards, savepoint and outbox sequencing while retaining session control revision.'),
 ('internal/domain/v24_sessions.go', 'Modify', 'Narrow watermark-only internal advance with writer epoch/current control revision/watermark CAS; existing control-changing AdvanceWatermark semantics remain.'),
 ('internal/domain/client_transcript.go', 'Modify', 'Immutable partial OBSERVED transcript snapshots and current watermark; incomplete/aborted messages preserved; final LIVE provenance requires settled original Run and verified stream reconciliation, not SETTLED-before-START.'),
 ('internal/domain/client_protocol_history.go', 'Modify', 'Explicit streaming interleave validation by message/part ownership; preserve complete executable-history gate and original 32 KiB bound; define interrupted partial history as visible, not replay-authorized.'),
 ('internal/domain/runtime_model_stream_test.go', 'New', 'Pure SSE/UTF-8/secret/EOF/error limits and no prefix leakage tests.'),
 ('internal/domain/runtime_model_stream_windows_test.go', 'New', 'Real Go broker plus rebuilt pinned Mu SDK and local SSE; durable events, effects, queue and cancellation invariants.'),
 ('internal/domain/client_stream_transcript_test.go', 'New', 'Partial snapshot, >200 messages, STEER interleave, revision CAS, final provenance and interrupted history controls.'),
 ('adapters/runtime/bridge_stream_windows_test.go', 'New', 'Transport sequence, identity, credit window, single writer, cancellation priority, queue/SEAL negative controls.'),
 ('adapters/runtime/mu/worker-stream.test.mjs', 'New', 'Actual pinned SDK event/ReadableStream checks and adversarial transport; a fake worker may test framing only, never SDK consumption.'),
 ('apps/cli/cli_model_stream_integration_windows_test.go', 'New', 'Compiled current CLI + real private host/API/named pipe + rebuilt Mu SDK + httptest SSE causal barriers. Do not alter protected S5 cli_stream_test.go.'),
]
proposal = {
 'schema': 'researchos.w05.streaming-source-scope-proposal.v1',
 'status': 'PROPOSED_PENDING_INDEPENDENT_SCOPE_REVIEW',
 'created_at': dt.datetime.now(dt.timezone.utc).isoformat(),
 'author': 'codex:/root/command_queue_impl', 'repo': str(ROOT), 'observed_main_head': head,
 'project_id': identity['project_id'],
 'execution_claim': 'READ_ONLY_SOURCE_INVESTIGATION. No product modification, build, provider request, actual streaming test or acceptance occurred.',
 'scope_count': len(scope),
 'conclusion_zh': '真实流式输出缺少 Go 增量转发、SDK delta 到持久事件的投影；CLI 的现有轮询可承载。仅修改 worker 或把最终完整文本切片不足。需要同步解决顺序 ACK 死锁、token 引起控制 revision 冲突及部分 transcript 与 STEER 的冲突。',
 'source_findings': [
  {'id':'F01','locations':['internal/domain/runtime_model_windows.go:93','adapters/runtime/mu/worker.mjs:372','internal/domain/runtime_sessions_windows.go:235'], 'fact':'Go ReadAll waits EOF, worker awaits final effect before Response(full SSE), host emits assistant text only after SETTLED; current 16,384-character post-completion chunks are not live streaming.'},
  {'id':'F02','locations':['apps/cli/cli_stream.go:25','apps/cli/cli_stream.go:226','apps/cli/cli_stream.go:297'], 'fact':'CLI already polls durable session events and emits fresh JSONL after page validation; default 200 ms poll is a delivery latency floor, not the full-response buffering source.'},
  {'id':'F03','locations':['third_party/mu/packages/ai/src/api/openai-completions.ts:553','third_party/mu/packages/ai/src/api/openai-completions.ts:595','third_party/mu/packages/agent/src/agent-loop.ts:443','third_party/mu/packages/agent/src/agent.ts:266','third_party/mu/packages/agent/src/agent.ts:610','third_party/mu/packages/coding-agent/src/core/agent-session.ts:837'], 'fact':'Pinned SDK parses real provider delta.content into text_delta and awaited agent message_update. AgentSession.subscribe listener is void and _emit does not await it; backpressure must use the existing awaited agent.subscribe hook, with its AbortSignal, without changing the fork.'},
  {'id':'F04','locations':['internal/domain/runtime_command_queue_windows.go:426','internal/domain/runtime_command_queue_windows.go:492','adapters/runtime/bridge_windows.go:550'], 'fact':'Legacy ACKs advance only in contiguous global order. Waiting for ordinary delta-frame ACK behind its still-running MODEL parent would deadlock streaming. Existing late effect ACK identities survive abort and must remain valid.'},
  {'id':'F05','locations':['internal/domain/client_protocol_journal.go:43','internal/domain/v24_sessions.go:140',SPEC+'22_CLIENT_INTERFACE_DETAILS.md:109'], 'fact':'Existing event append advances control revision; applying it unchanged to each token conflicts with frozen revision semantics and inflight STEER expected_revision.'},
  {'id':'F06','locations':['internal/domain/client_transcript.go:136','internal/domain/client_transcript.go:164','internal/domain/client_transcript.go:246','internal/domain/client_protocol_history.go:175','internal/domain/client_command_queue.go:115'], 'fact':'Transcript provenance rejects incomplete messages and requires SETTLED projection before assistant START; old snapshot artifact must match current transcript exactly; executable history rejects overlapping message lifetimes; STEER seals transcript immediately. Early deltas would break these paths unless adapted together.'},
 ],
 'proposed_architecture': {
  'authority':'Original coordinator remains sole executor and GoSQLite outbox remains business event authority. Credentials/network/budget reservation remain in Go. No second writer, worker or scheduling path.',
  'provider_reader':'Validate response status/content-type before forwarding. Incrementally parse actual arriving SSE event bytes; retain the exact bounded full raw response for existing verification/fact digest. Preserve 2 MiB total and 64 KiB envelope bounds, strict UTF-8, completeRuntimeModelSSE final semantics, original HTTP timeout/context and zero retries.',
  'secret_guard':'Never release a credential prefix that could later complete across wire chunks or decoded content deltas. Hold unresolved prefix suffixes and unfinished SSE events; inspect raw and decoded stream strings under bounded state. Exact credentials never cross to worker/public events/logs. Preserve original full-body secret check; byte-tail-only matching is insufficient across JSON events. A blocked stream remains UNKNOWN after dispatch, not a successful redacted answer.',
  'wire':'Negotiate a single fixed internal MODEL_SSE_V1 capability on a source/bundle-bound initialized worker. Strict auxiliary envelope union on existing stdin/stdout; original BridgeFrame sequence and ordered ACK rules remain intact. Per-effect auxiliary stream sequence/offset/hash and bounded credit window are separate from business frames, not extra ready-map entries waiting behind MODEL. Every envelope binds original effect key/request hash/Task/Run/session/runtime epoch/dispatch manifest/process generation. Pre-init, changed duplicate, gap, cross-run and old generation reject.',
  'backpressure':'One existing host stdin writeMu and worker stdout write chain; no locks held while waiting for credits. Auxiliary stream data/observation processing must be cancellable, bounded, and control-prioritized. Go durable MESSAGE commit precedes observation credit. Transport delivery/credit never advances original Acknowledged, confirms an effect, consumes a queued custom message or proves SEAL.',
  'sdk':'Worker constructs Response(ReadableStream) from validated actual incoming chunks and calls the pinned SDK unchanged. Subscribe via awaited session.agent.subscribe for message_update/assistantMessageEvent text_start/text_delta/text_end; capture assistant visible text only, no reasoning or tool-argument leakage. Splitting one genuine delta solely for public field/UTF-8/frame limits is allowed; splitting a completed response to simulate streaming is forbidden.',
  'terminal':'Withhold terminal [DONE]/ReadableStream close until the entire provider response passes the original terminal checks and its CONFIRMED fact is durably ingested. Final effect ACK carries matching final receipt/hash/stream watermark, not duplicate full response. SDK tool decisions cannot run from an unconfirmed terminal response. Intermediate public deltas are observations, not effect settlement.',
  'durability':'Deterministic observation/message IDs bind original effect and SDK content index, with per-part UTF-8 offsets. Persist schema-valid MESSAGE START/DELTA and watermark in one transaction after original binding/current authority recheck. Exact retry is idempotent; altered duplicate/gap fails. Token events do not change control revision; command/control writers still enforce expected_revision and writer_epoch. No mutation of old canonical events.',
  'transcript':'Expose incomplete assistant messages with existing complete=false and immutable OBSERVED transcript at the same watermark. Keep concurrent USER STEER messages with their actual sequence and stable message ownership; do not re-order or silently drop them. For successful completion reconcile SDK text against original Go response/full sealed worker artifact before END/final provenance; final projection must not duplicate streamed text. Preserve legacy completed projection. Interrupted text stays visible/incomplete and cannot be silently promoted to executable trusted context.',
  'cancel_and_unknown':'Canonical Goal/Run cancellation still fences original request, cancels Go HTTP context, clears real SDK queues and obtains clear/abort-observed/idle/process/effect proofs. Reject all stream waiters without discarding late exact final effect ACK identity. Any failure after request dispatch uses original UNKNOWN/budget rules; no automatic replay/new worker/budget reset. Late chunks may support effect reconciliation but may not append new authorized deltas after fence or restore.',
  'seal':'Existing initialize ACK, actual customMessage consumption, hasQueuedMessages and prepare/commit SEAL checks remain. Streaming adds a closure condition: all streams closed or fenced and all durable observations reconciled before final business completion. Original queue_empty must not become frame-only or transport-credit-only.',
 },
 'exact_proposed_source_scope':[{'path':p,'operation':op,'narrow_purpose':purpose} for p,op,purpose in scope],
 'explicit_readonly_boundaries':['All third_party/mu and pinned fork/dependency locks','adapters/runtime/mu/build.mjs (execute current builder only after authorization)','Frozen client.protocol.schema.json and specs','apps/cli/cli_stream_test.go and S5 suffix','Existing canonical receipts/checkpoints/ownership/formal registry','Stable user DB, DPAPI, credentials, private holdout','No new migration or opaque store authority in this proposed scope'],
 'required_architecture_decisions_before_implementation':[
  {'id':'D01','decision':'Approve exact auxiliary envelope schema and fixed finite per-stream/per-run windows, frame/message caps and cancellation timeout; separate durable observation credit from original ordered ACK. Include no-deadlock proof/test with parent MODEL outstanding, simultaneous queue receipt and cancel.', 'reason':'The naive existing frame/ACK path cannot carry awaited delta observations safely.'},
  {'id':'D02','decision':'Approve partial transcript artifact policy, snapshot pointer update cadence/size bound and treatment of interrupted partial history on a later explicit NORMAL request. Proposed fail-closed executable context until explicit context rebuild, while read-only history/snapshot and original cancel remain available.', 'reason':'Frozen public schema already has complete=false; there is no ABORT phase. Must not invent END, hide partial history, or unexpectedly make STEER unreadable.'},
  {'id':'D03','decision':'Approve replacement provenance predicate only for stream-bound records: original run/effect identity + exact reconciled final bytes + runtime measurement mode + settled state, retaining legacy predicates for legacy messages. Decide storage representation using existing outbox/facts and deterministic IDs; if these cannot supply durable binding, request a separate numbered migration scope before writing it.', 'reason':'Removing SETTLED-before-START without equivalent positive evidence would weaken history provenance.'},
  {'id':'D04','decision':'Approve token-only watermark CAS helper and strict credentials-before-forward quarantine behavior, including bounded memory and partial prefix handling.', 'reason':'No blanket writer/revision bypass and no leak-then-redact streaming.'},
 ],
 'actual_future_test_plan':[
  {'id':'T01','lane':'PURE_LOCAL', 'assertions':'Incremental SSE with CRLF, multibyte Chinese split across byte reads, multiline data, comments, multiple choices, zero-text/tool-only events, [DONE] terminal handling. Compare accepted full streams to original completeRuntimeModelSSE; EOF missing DONE, invalid UTF-8/JSON, extra data after DONE, wrong status/type, >2 MiB and read errors reject.'},
  {'id':'T02','lane':'REAL_PINNED_SDK_LOCAL_SSE_FIXTURE', 'assertions':'httptest handler flushes delta A then waits for harness observation of the actual durable public delta; flush B then waits again before [DONE]/EOF. Actual SDK text_delta and SQLite/CLI event precede each release. Record causal sequence and monotonic timestamps. No sleep-based guess and no complete-response rechunking.'},
  {'id':'T03','lane':'REAL_COMPILED_CLI_PRIVATE_HOST_FIXTURE', 'assertions':'Build current CLI/control and worker; real first-use API/named pipe and loopback qualification; JSONL every line valid. First and second DELTA visible before provider completion; final assistant text exact once, no doubled chunks, correct UTF-8 offsets; stderr diagnostics separate. Reconnect from watermark replays once with no second MODEL/TOOL.'},
  {'id':'T04','lane':'DURABLE_TRANSCRIPT_FIXTURE', 'assertions':'While stream blocked between A/B, session.get succeeds with complete=false and exact through-watermark transcript; >200-message snapshot has full immutable artifact. STEER/FOLLOW_UP admission/CAS/real customMessage consumption work without token-induced revision conflict; interleaving preserves all message IDs/bytes. Final history validates original Run/effect; FIXTURE never becomes LIVE.'},
  {'id':'T05','lane':'BRIDGE_ADVERSARIAL', 'assertions':'Before initialize ACK, wrong request hash/run/epoch/manifest/generation, sub-sequence gap, changed duplicate, stale credit and oversized/malformed frame reject. Exact duplicate does not add another event. Parent MODEL remains unresolved while auxiliary observation is durably credited; more deltas than old frame queue capacity do not grow unbounded ready/pending state. No credits may imply queue_empty/SEAL.'},
  {'id':'T06','lane':'REAL_CANCEL_FIXTURE', 'assertions':'Cancel at headers/first delta/credit wait/after DONE-before-final-ACK; canonical Task/Goal original request finalization remains monotonic. No later visible delta after cancel fence; HTTP abort, real SDK queue clear/idle, process terminal and effects reconcile. Late exact ACK accepted for reconciliation; different late ACK or old worker fails. Already received partial text remains incomplete and visible; no forged END.'},
  {'id':'T07','lane':'FAILURE_AND_RECOVERY_FIXTURE', 'assertions':'Connection reset, reader error, invalid final SSE after early valid deltas, host commit failure, worker exit and host restart leave original UNKNOWN where dispatched. Reservation not reset; no automatic retry/second worker. Restore old stream epoch rejects new data while preserving exact prior observations. No tools may execute on unconfirmed EOF.'},
  {'id':'T08','lane':'SECRET_AND_CONTENT_BOUNDARY_FIXTURE', 'assertions':'Synthetic credentials split at every wire offset and across decoded delta events never reach worker/public stdout/raw receipt. Tool argument/thinking deltas are not public assistant text. Secret-prefix buffering finite and cancellation frees it. All credentials used here are labelled synthetic.'},
  {'id':'T09','lane':'EXISTING_CURRENT_REGRESSION', 'assertions':'Run complete current CLI vector including S5 and S6; current queue/bridge/control Node tests; model verification/effect wire/session/transcript/history; fixed 21→22 upgrade and ordinary backup/restore regressions when stream persistence shape changes. Preserve original four historical Q10 failure records and attribution; do not reclassify them or claim parent/LIVE acceptance.'},
 ],
 'freeze_and_evidence_requirements':[
  'Before/after complete Go compile input vector, embed assets, migration SQL, public schema, lock files and all relevant tests/helpers; exact current main commit and dirty source hashes, not HEAD alone.',
  'Use locked Go/Node and current actual build.mjs; record argv/cwd/environment/exit/stdout/stderr and source/build/bundle hashes. Freeze actual SDK dist inputs used by esbuild as well as vendor manifest/source and package locks. Do not label old bundle as new source.',
  'Use a new isolated root for every actual DB/host/loopback fixture. Never point to user DB or private credentials. Source paths outside approved scope remain byte-identical.',
  'Record causal SSE writes, SDK events, durable commit sequences and CLI arrival; exact pass/fail/skip counts and original errors. All loopback outputs measurement_mode FIXTURE; none establishes LIVE_MODEL or current formal parent acceptance.',
  'Independent scope approval precedes source implementation; independent source review and real current integration precede any Root acceptance. Current W04/W07 applicability vectors may become stale from approved source changes and require explicit subsequent recapture; this proposal changes no vector.',
 ],
 'limitations':['Static source establishes buffering mechanisms but this investigation did not execute a timing reproduction.', 'Proposed 19-path scope is a reviewable envelope, not authorization or implemented result.', 'D01–D04 remain explicit independent architecture gates; storage/protocol expansion beyond these exact paths needs amended scope.'],
}
save('input_manifest_before.json', before)
save('source_excerpts.json', excerpts)
save('proposal.json', proposal)
after = {rel: {'sha256':sha((ROOT/rel).read_bytes()),'bytes':(ROOT/rel).stat().st_size} for rel in paths}
save('input_manifest_after.json', after)
if before != after:
    save('input_drift.json', {'changed':[p for p in paths if before[p] != after[p]]})
    raise RuntimeError('source changed during readonly proposal capture')
save('capture_result.json', {'status':'READONLY_PROPOSAL_CAPTURED','input_count':len(paths),'input_drift':[],
     'product_tests_executed':0,'product_sources_written':0,'main_metadata_written':0,'network_requests':0,
     'proposal_sha256':sha((OUT/'proposal.json').read_bytes()),'scope_paths':len(scope),
     'finished_at':dt.datetime.now(dt.timezone.utc).isoformat()})
print(json.dumps({'status':'READONLY_PROPOSAL_CAPTURED','proposal_sha256':sha((OUT/'proposal.json').read_bytes()),'inputs':len(paths),'scope_paths':len(scope)}))
