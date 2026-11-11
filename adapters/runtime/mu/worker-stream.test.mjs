import test from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { pathToFileURL } from "node:url";
import { join } from "node:path";
import { spawn } from "node:child_process";
import { createInterface } from "node:readline";
import { mkdtemp, mkdir, writeFile, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";

const bundle = process.env.RESEARCHOS_QUEUE_WORKER_BUNDLE;
const sdkRoot = process.env.RESEARCHOS_STREAM_SDK_ROOT;
assert.ok(bundle && sdkRoot, "actual freshly rebuilt worker and pinned SDK paths required");
const { boundedSDKStream, createModelStreamTransport, canonicalJSON, parseWireJSON, createWireInput, STREAM_LIMITS } = await import(pathToFileURL(bundle));
const { Agent } = await import(pathToFileURL(join(sdkRoot, "packages/agent/dist/index.js")));
const { streamSimple } = await import(pathToFileURL(join(sdkRoot, "packages/ai/dist/api/openai-completions.js")));
const hash = raw => `sha256:${createHash("sha256").update(raw).digest("hex")}`;
const EMPTY = hash("");
const pending = () => { let resolve, reject; const promise = new Promise((yes, no) => { resolve = yes; reject = no; }); promise.catch(() => {}); return { promise, resolve, reject }; };
const tick = () => new Promise(resolve => setImmediate(resolve));
const model = { id: "fixture", name: "fixture", provider: "openai", api: "openai-completions", baseUrl: "https://fixture.invalid", reasoning: false, input: ["text"], cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 }, contextWindow: 10000, maxTokens: 128, compat: { supportsStore: false } };
const chunk = (delta, finish_reason = null) => ({ id: "fixture", object: "chat.completion.chunk", choices: [{ index: 0, delta, finish_reason }] });
const sse = value => `data: ${JSON.stringify(value)}\n\n`;
const finish = sse(chunk({}, "stop")) + "data: [DONE]\n\n";
const usage = { id: "fixture", object: "chat.completion.chunk", choices: [], usage: { prompt_tokens: 1, completion_tokens: 1, total_tokens: 2 } };
const base = { project_id: "project", session_id: "session", task_id: "task", run_id: "run", runtime_epoch: 1, queue_generation: "generation", dispatch_key: "dispatch", manifest_hash: hash("manifest"), process_identity: { pid: 12, process_created_ns: "1", job: "job", appcontainer_sid: "sid", profile: "profile", staging_directory: "stage" } };
function fixture(initialized = true) {
  const sent = [], ack = pending();
  const transport = createModelStreamTransport(async frame => { sent.push(frame); }, () => initialized ? base : null);
  const state = transport.begin(3, "task:run:1:model:1", 1);
  const response = transport.response(state, ack.promise);
  const b = { ...base, effect_sequence: 3, effect_key: state.key, request_hash: hash("request") };
  const binding = { ...b, stream_id: hash(canonicalJSON(b)) };
  let raw = Buffer.alloc(0), sequence = 0;
  const frame = (type, seq, offset, digest, payload) => ({ version: "MODEL_SSE_V1", type, binding, sequence: seq, offset, digest, payload });
  const open = () => transport.receive(frame("stream.open", 0, 0, EMPTY, { status: 200, content_type: "text/event-stream" }));
  const data = (text, terminal = false) => {
    const bytes = Buffer.from(text); raw = Buffer.concat([raw, bytes]);
    const record = frame("stream.data", ++sequence, raw.length, hash(raw), { data_base64: bytes.toString("base64"), terminal });
    transport.receive(record); return record;
  };
  const end = (overrides = {}) => {
    const watermark = state.observeSequence;
    transport.receive(frame("stream.terminal", sequence, raw.length, hash(raw), { receipt_id: hash(raw), observation_sequence: watermark }));
    ack.resolve({ status: 200, content_type: "text/event-stream", body_encoding: "MODEL_SSE_V1", stream_id: binding.stream_id, body_sha256: hash(raw), receipt_id: hash(raw), raw_bytes: raw.length, data_sequence: sequence, observation_sequence: watermark, ...overrides });
  };
  const credit = record => transport.receive(frame("stream.observation_credit", record.sequence, record.offset, record.digest, { journal_event_ids: ["fixture-outbox-" + record.sequence], session_watermark: record.sequence }));
  return { transport, state, sent, response, binding, frame, open, data, end, credit, ack };
}

test("canonical wire preserves UTF-8, HTML characters and UTF-16 key ordering", () => {
  assert.equal(canonicalJSON({ z: "<>&中文\u2028\u2029", a: 1 }), '{"a":1,"z":"<>&中文\u2028\u2029"}');
  assert.equal(canonicalJSON({ "\ue000": 1, "😀": 2 }), '{"😀":2,"":1}');
});

test("wire rejects duplicate keys, lone surrogates, nonfinite numbers and deep ambiguity", () => {
  for (const raw of ['{"a":1,"a":2}', '{"a":1,"\\u0061":2}', '{"a":"\\ud800"}', '{"a":1e400}', '{"a":0}false', '['.repeat(66)+'0'+']'.repeat(66)]) assert.throws(() => parseWireJSON(raw));
  assert.deepEqual(parseWireJSON('{"nested":[{"a":"😀中文<>&"}],"zero":0}'), { nested: [{ a: "😀中文<>&" }], zero: 0 });
});

test("actual stdin transform rejects malformed UTF-8 and oversized unterminated lines", async () => {
  for (const bytes of [Buffer.from([0xc0,0x80]), Buffer.alloc(65537, 32), Buffer.from([0xe4,0xb8])]) {
    const input = createWireInput(), failed = pending(); input.on("error", failed.resolve); input.resume(); input.end(bytes);
    assert.ok(await failed.promise instanceof Error);
  }
  const input = createWireInput(); let result = ""; input.on("data", bytes => { result += bytes.toString("hex"); });
  const ended = pending(); input.on("end", ended.resolve); const bytes = Buffer.from('"中文"\n');
  for (const byte of bytes) input.write(Buffer.from([byte])); input.end(); await ended.promise; assert.equal(result, bytes.toString("hex"));
});

test("actual SDK huge mixed provider batch exhausts finite queue visibly without retry", { timeout: 5000 }, async () => {
  const tools = Array.from({ length: 2050 }, (_, i) => ({ index: i, id: `tool-${i}`, type: "function", function: { name: "fixture", arguments: "{}" } }));
  let calls = 0, wrapped;
  const agent = new Agent({ initialState: { model }, streamFn: (m, c, o) => {
    wrapped = boundedSDKStream(options => streamSimple(m, c, options), { ...o, apiKey: "fixture", fetch: async () => {
      calls++; return new Response(sse(chunk({ tool_calls: tools })) + finish, { headers: { "content-type": "text/event-stream" } });
    } }); return wrapped;
  } });
  // The real agent converts its producer error into a failed assistant turn.
  await agent.prompt("FIXTURE bounded decoded batch");
  assert.equal(calls, 1); assert.ok(wrapped.streamMetrics().failed); assert.ok(wrapped.streamMetrics().peak <= STREAM_LIMITS.sdkEvents);
  assert.match(agent.state.errorMessage ?? agent.state.messages.at(-1)?.errorMessage ?? "", /bound exceeded|abort/i);
});

test("actual SDK accepts one event larger than wire frames and drains genuine delta in bounded public fragments", { timeout: 10000 }, async () => {
  const f = fixture(); f.open();
  const text = "中文😀<>&".repeat(25000), input = Buffer.from(sse(chunk({ content: text })) + finish);
  assert.ok(input.length > 65536 && input.length < STREAM_LIMITS.raw);
  const observed = []; let wrapped;
  const agent = new Agent({ initialState: { model }, streamFn: (m, c, o) => {
    wrapped = boundedSDKStream(options => streamSimple(m, c, options), { ...o, apiKey: "fixture", fetch: async () => (await f.response).response }); return wrapped;
  } });
  agent.subscribe(async (event, signal) => {
    const promise = f.transport.observe(event, signal);
    while (f.state.observations.size) {
      const record = f.sent.at(-1); assert.equal(record.type, "stream.observe");
      if (record.payload.event === "text_delta") { assert.ok(Buffer.byteLength(record.payload.text) <= 8192); observed.push(record.payload.text); }
      f.credit(record); await tick();
    }
    await promise;
  });
  const done = agent.prompt("FIXTURE huge bounded SSE event");
  // Last terminal bytes remain quarantined until original ACK. The enormous
  // earlier real delta is not split into synthetic provider events.
  const terminalBytes = Buffer.byteLength(finish), visibleEnd = input.length - terminalBytes;
  for (let offset = 0; offset < visibleEnd; offset += 8192) {
    while (f.state.data.length >= 4) await tick();
    f.data(input.subarray(offset, Math.min(visibleEnd, offset + 8192)));
  }
  while (observed.join("") !== text) await tick();
  f.data(finish, true); f.end(); await done;
  assert.equal(observed.join(""), text); assert.ok(observed.length > 32); assert.ok(wrapped.streamMetrics().peak <= 3); assert.equal(f.transport.closed(), true);
});

test("actual SDK producer waits for every prior mixed batch event after awaited Agent listener", { timeout: 10000 }, async () => {
  const release = pending(), entered = pending();
  const hooks = [], observed = []; let wrapper, calls = 0;
  const content = sse(chunk({ role: "assistant" })) + sse(usage) + sse(chunk({ reasoning_content: "private thinking" })) +
    sse(chunk({ content: "A", reasoning_content: "more private", tool_calls: [{ index: 0, id: "tool", type: "function", function: { name: "fixture_tool", arguments: "{}" } }] })) +
    sse(chunk({ content: "B" })) + finish;
  const agent = new Agent({ initialState: { model }, streamFn: (m, c, o) => {
    const actual = boundedSDKStream(options => streamSimple(m, c, options), { ...o, apiKey: "fixture", maxRetries: 0, onProviderStreamEvent: chunk => { hooks.push(chunk); }, fetch: async () => new Response(++calls === 1 ? content : finish, { headers: { "content-type": "text/event-stream" } }) });
    wrapper ??= actual;
    return actual;
  } });
  agent.subscribe(async event => {
    if (event.type !== "message_update") return;
    const update = event.assistantMessageEvent; observed.push(update.type);
    if (update.type === "text_delta" && update.delta === "A") { entered.resolve(); await release.promise; }
  });
  const done = agent.prompt("FIXTURE producer causal boundary");
  await entered.promise; await tick();
  assert.equal(hooks.length, 4, "next provider hook cannot pass the uncredited prior text event");
  assert.ok(wrapper.streamMetrics().pushed > wrapper.streamMetrics().consumed);
  release.resolve(); await done;
  assert.equal(hooks.length, 7, "tool result is followed by one bounded final MODEL");
  assert.equal(calls, 2);
  assert.ok(observed.includes("thinking_delta") && observed.includes("toolcall_delta"));
  assert.ok(wrapper.streamMetrics().peak <= 7, "mixed batch counts every actual push without unbounded queue");
});

for (const [label, body] of [
  ["zero-output", sse(chunk({ role: "assistant" })) + finish],
  ["usage-only", sse(usage) + finish],
  ["thinking-only", sse(chunk({ reasoning_content: "private" })) + finish],
  ["tool-only", sse(chunk({ tool_calls: [{ index: 0, id: "t", type: "function", function: { name: "fixture", arguments: "{}" } }] })) + finish],
]) test(`actual SDK ${label} has no future-event credit wait`, { timeout: 5000 }, async () => {
  let wrapped, calls = 0;
  const agent = new Agent({ initialState: { model }, streamFn: (m, c, o) => {
    wrapped = boundedSDKStream(options => streamSimple(m, c, options), { ...o, apiKey: "fixture", fetch: async () => new Response(++calls === 1 ? body : finish, { headers: { "content-type": "text/event-stream" } }) }); return wrapped;
  } });
  await agent.prompt("FIXTURE zero visible text");
  assert.equal(agent.state.messages.at(-1).stopReason, "stop");
  assert.ok(wrapped.streamMetrics().peak <= 5);
});

test("stream open requires delivered initialization and exact full binding", async () => {
  const no = fixture(false); assert.throws(no.open, /initialization/); no.transport.abort(); await assert.rejects(no.response);
  const f = fixture(); const wrong = f.frame("stream.open", 0, 0, EMPTY, { status: 200, content_type: "text/event-stream" });
  wrong.binding = { ...wrong.binding, runtime_epoch: 2 }; assert.throws(() => f.transport.receive(wrong), /binding/);
  f.transport.abort(); await assert.rejects(f.response);
});

test("terminal bytes and EOF wait for exact original ACK; credits do not prove closure", { timeout: 5000 }, async () => {
  const f = fixture(); f.open(); const { response } = await f.response; const reader = response.body.getReader();
  const record = f.data("data: [DONE]\n\n", true); await tick();
  assert.equal(f.sent[0].type, "stream.transport_credit"); assert.equal(f.transport.closed(), false);
  let delivered = false; const read = reader.read().then(value => { delivered = true; return value; }); await tick(); assert.equal(delivered, false);
  f.transport.receive(f.frame("stream.terminal", record.sequence, record.offset, record.digest, { receipt_id: record.digest, observation_sequence: 0 }));
  await tick(); assert.equal(delivered, false, "terminal marker alone is not original effect confirmation");
  f.end(); assert.equal(Buffer.from((await read).value).toString(), "data: [DONE]\n\n"); assert.equal((await reader.read()).done, true);
  assert.equal(f.transport.closed(), false, "SDK message_end still requires its observation credit");
  const end = f.transport.observe({ type: "message_end", message: { role: "assistant", stopReason: "stop" } }); await tick();
  f.credit(f.sent.at(-1)); await end; assert.equal(f.transport.closed(), true);
});

test("changed terminal ACK fails the actual pending body read", { timeout: 5000 }, async () => {
  const f = fixture(); f.open(); const { response } = await f.response; f.data("data: [DONE]\n\n", true);
  const reading = response.text(); f.end({ body_sha256: hash("changed") }); await assert.rejects(reading, /ACK mismatch/);
});

test("exact data duplicates idempotent; changed duplicates/gaps/wrong directions rejected", async () => {
  const f = fixture(); f.open(); const { response } = await f.response; const reader = response.body.getReader();
  const first = f.data("hello"); assert.equal(Buffer.from((await reader.read()).value).toString(), "hello"); await tick();
  f.transport.receive(first); assert.equal(f.state.sequence, 1);
  assert.throws(() => f.transport.receive({ ...first, payload: { ...first.payload, data_base64: Buffer.from("other").toString("base64") } }), /duplicate/);
  assert.throws(() => f.transport.receive({ ...first, sequence: 3 }), /sequence/);
  assert.throws(() => f.transport.receive({ ...first, type: "stream.transport_credit", payload: {} }), /direction/);
  f.transport.abort(); await assert.rejects(reader.read());
});

test("four data window enforced without holding cancellation behind credit", async () => {
  const f = fixture(); f.open(); const { response } = await f.response;
  for (let i = 0; i < 4; i++) f.data("x");
  assert.equal(f.transport.metrics().queued_data, 4); assert.throws(() => f.data("x"), /window/);
  f.transport.abort(); await assert.rejects(response.text()); assert.equal(f.transport.closed(), true);
});

test("durable observation exact credit, UTF-8 fragments, dense text index and cancellation", { timeout: 5000 }, async () => {
  const f = fixture(); f.open(); await f.response;
  const start = f.transport.observe({ type: "message_update", assistantMessageEvent: { type: "text_start", contentIndex: 2 } }); await tick();
  const first = f.sent.at(-1); assert.equal(first.payload.text_part, 0); assert.equal(first.payload.sdk_content_index, 2);
  f.credit(first); await start; f.credit(first);
  assert.throws(() => f.transport.receive(f.frame("stream.observation_credit", first.sequence, 1, first.digest, { journal_event_ids: ["changed"], session_watermark: 1 })), /stale|changed/);
  const text = "中文😀".repeat(3000), delta = f.transport.observe({ type: "message_update", assistantMessageEvent: { type: "text_delta", contentIndex: 2, delta: text } });
  let result = "";
  while (result.length < text.length) { await tick(); const item = f.sent.at(-1); assert.equal(item.type, "stream.observe"); assert.ok(Buffer.byteLength(item.payload.text) <= 8192); result += item.payload.text; f.credit(item); }
  await delta; assert.equal(result, text);
  const blocked = f.transport.observe({ type: "message_update", assistantMessageEvent: { type: "text_end", contentIndex: 2 } }); await tick();
  f.transport.abort(); await assert.rejects(blocked); assert.equal(f.transport.metrics().observations, 0);
});

async function childFixture(t, cancel) {
  const root = await mkdtemp(join(tmpdir(), "researchos-stream-sdk-"));
  await mkdir(join(root, "input")); await mkdir(join(root, "output"));
  const binding = { ...base }; delete binding.process_identity;
  await writeFile(join(root, "input/request.json"), JSON.stringify({ task_id: "task", run_id: "run", epoch: 1, input_refs: [], context: {}, task_title: "FIXTURE real SDK stream", task_description: "causal observations", queue_control: true, queue_binding: binding }));
  await writeFile(join(root, "input/worker.json"), JSON.stringify({ ref: "FIXTURE", api: "openai-completions", provider: "openai", model: "fixture", endpoint: "https://fixture.invalid", route: "fixture", max_output_tokens: 128, max_calls: 1, tools: [] }));
  const child = spawn(process.execPath, [bundle, join(root, "input/request.json")], { cwd: root, stdio: ["pipe", "pipe", "pipe"] });
  const exited = pending(); child.once("exit", code => exited.resolve(code));
  t.after(async () => { child.kill(); await exited.promise; await rm(root, { recursive: true, force: true, maxRetries: 5, retryDelay: 50 }); });
  binding.process_identity = { ...base.process_identity, pid: child.pid, staging_directory: root };
  let stderr = ""; child.stderr.on("data", bytes => { stderr += bytes; });
  const done = pending(), credits = new Map(), observations = [], ordinary = [];
  const send = value => child.stdin.write(JSON.stringify(value) + "\n");
  const causalRaw = [];
  const record = (event, details = {}) => causalRaw.push({ event, monotonic_ns: process.hrtime.bigint().toString(), ...details });
  let streamBinding, raw = Buffer.alloc(0), dataSequence = 0, heldEffect, terminalSent = false, finalAckSent = false, abortObserved = false, cancelAt;
  const aux = (type, sequence, offset, digest, payload) => ({ version: "MODEL_SSE_V1", type, binding: streamBinding, sequence, offset, digest, payload });
  async function sendData(bytes, terminal = false) {
    raw = Buffer.concat([raw, Buffer.from(bytes)]); const sequence = ++dataSequence; const wait = pending(); credits.set(sequence, wait);
    record("broker_data_send", { sequence, terminal });
    send(aux("stream.data", sequence, raw.length, hash(raw), { data_base64: Buffer.from(bytes).toString("base64"), terminal }));
    await wait.promise;
  }
  const causal = new Map();
  async function produce(effect) {
    const b = { ...binding, effect_sequence: effect.sequence, effect_key: effect.key, request_hash: hash("FIXTURE prepared request") }; streamBinding = { ...b, stream_id: hash(canonicalJSON(b)) };
    send(aux("stream.open", 0, 0, EMPTY, { status: 200, content_type: "text/event-stream" }));
    for (let i = 0; i < (cancel ? 1 : 40); i++) {
      const wait = pending(); causal.set(String(i), wait);
      await sendData(sse(chunk({ content: String(i) }))); await wait.promise;
    }
    if (cancel) return;
    await sendData(finish, true); terminalSent = true;
    const watermark = observations.at(-1)?.sequence ?? 0;
    send(aux("stream.terminal", dataSequence, raw.length, hash(raw), { receipt_id: hash(raw), observation_sequence: watermark }));
    finalAckSent = true; record("original_MODEL_ACK_send");
    send({ sequence: effect.sequence, key: effect.key, state: "CONFIRMED", payload: { status: 200, content_type: "text/event-stream", body_encoding: "MODEL_SSE_V1", stream_id: streamBinding.stream_id, body_sha256: hash(raw), receipt_id: hash(raw), raw_bytes: raw.length, data_sequence: dataSequence, observation_sequence: watermark } });
  }
  const reader = createInterface({ input: child.stdout });
  reader.on("line", line => { try {
    const frame = JSON.parse(line);
    if (frame.version === "MODEL_SSE_V1") {
      if (frame.type === "stream.transport_credit") { const wait = credits.get(frame.sequence); assert.ok(wait); credits.delete(frame.sequence); wait.resolve(); }
      else if (frame.type === "stream.observe") {
        assert.equal(frame.sequence, observations.length + 1); observations.push(frame);
        if (frame.payload.event === "text_delta") {
          assert.equal(terminalSent, false, "each actual SDK visible delta precedes provider terminal");
          assert.equal(finalAckSent, false, "original MODEL still unacknowledged during 40 real deltas");
          record("actual_SDK_text_delta_received", { observation_sequence: frame.sequence, text: frame.payload.text });
          if (cancel) {
            cancelAt = process.hrtime.bigint(); record("cancel_send_credit_withheld");
            send({ type: "command.clear_abort", binding });
            // Preserve exact ordinary pending identity after abort; the real
            // worker must consume this late UNKNOWN without a second MODEL.
            send({ sequence: heldEffect.sequence, key: heldEffect.key, state: "UNKNOWN", payload: { code: "FIXTURE_CANCELLED" } });
            causal.get(frame.payload.text)?.resolve(); return;
          }
        }
        send(aux("stream.observation_credit", frame.sequence, frame.offset, frame.digest, { journal_event_ids: frame.payload.event === "text_end" || frame.payload.event === "message_end" ? [] : ["FIXTURE-outbox-" + frame.sequence], session_watermark: frame.sequence }));
        record("FIXTURE_observation_credit_send", { sequence: frame.sequence });
        if (frame.payload.event === "text_delta") causal.get(frame.payload.text)?.resolve();
      } else assert.fail("unexpected auxiliary record");
      return;
    }
    ordinary.push(frame); assert.equal(frame.sequence, ordinary.length, "auxiliary traffic never consumes ordinary sequence");
    if (frame.type === "context.ready") send({ type: "command.deliver", binding, initialize: true, command: null });
    if (frame.type === "command.accepted" && frame.payload.initialized) send({ sequence: frame.sequence, key: "command.initialize", state: "CONFIRMED", payload: {} });
    if (frame.type === "effect.request") { assert.equal(heldEffect, undefined, "no retry/new MODEL budget"); heldEffect = frame; produce(frame).catch(done.reject); }
    if (frame.type === "command.abort_observed") { abortObserved = true; record("actual_SDK_abort_observed"); assert.equal(frame.payload.sdk_idle, true); assert.equal(frame.payload.sdk_queue_empty, true); assert.ok(process.hrtime.bigint() - cancelAt < 2_000_000_000n, "actual cancel completes inside original 2s escalation"); }
    if (frame.type === "command.idle") {
      if (cancel) { assert.ok(abortObserved); done.resolve(); return; }
      if (frame.payload.through === 0 && !ordinary.some(item => item.type === "command.sealed")) {
        if (!ordinary.filter(item => item.type === "command.idle").slice(0, -1).length) send({ type: "command.prepare_seal", binding, through: 0 });
        else send({ type: "command.commit_seal", binding, through: 0 });
      }
    }
  } catch (error) { done.reject(error); child.kill(); } });
  child.on("error", done.reject);
  child.on("exit", code => { if (!cancel && code === 0) done.resolve(); else if (!abortObserved) done.reject(new Error(`worker exit ${code}: ${stderr}`)); });
  await done.promise;
  t.diagnostic(JSON.stringify({ measurement_mode: "FIXTURE_TRANSPORT_ONLY_NOT_SQLITE_OR_LIVE", causal_events: causalRaw }));
  if (cancel) { assert.ok(abortObserved); assert.equal(observations.filter(item => item.payload.event === "message_end").length, 0); }
  else {
    assert.equal(await exited.promise, 0); assert.equal(ordinary.at(-1).type, "turn.completed");
    assert.equal(observations.filter(item => item.payload.event === "text_delta").length, 40);
    const result = JSON.parse(await readFile(join(root, "output/result.json"), "utf8"));
    assert.equal(result.messages.at(-1).content.filter(part => part.type === "text").map(part => part.text).join(""), Array.from({ length: 40 }, (_, i) => String(i)).join(""));
    assert.equal(result.model_calls, 1);
  }
}

test("rebuilt actual AgentSession streams 40 causal deltas while original MODEL ACK remains pending", { timeout: 20000 }, t => childFixture(t, false));
test("rebuilt actual AgentSession cancel bypasses withheld observation credit and accepts late exact ACK", { timeout: 10000 }, t => childFixture(t, true));
